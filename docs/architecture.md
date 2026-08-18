# Erp Architecture & Trade-offs

## 1. System Overview

Erp is a multi-tenant, compliance-native SaaS platform designed for regulated workforce services including recruitment, HR, care, training, and compliance management. This implementation represents a vertical slice of the Candidate Compliance module, demonstrating core architectural patterns for tenant isolation, auditability, and governed AI integration.

### Technology Stack

- **Backend:** Django 6.1 with Django REST Framework 3.14
- **Database:** PostgreSQL 15 with Row-Level Security
- **Authentication:** JWT (SimpleJWT) with token blacklisting
- **Async Tasks:** Celery 5.3 with Redis broker
- **AI Integration:** OpenAI/Claude with mock fallback for development
- **Frontend:** Next.js 14 with TypeScript and Tailwind CSS
- **Deployment:** Render (backend API service + PostgreSQL)

---

## 2. Multi-Tenant Isolation Strategy (Defense in Depth)

### Overview

The golden rule driving all design decisions: **One tenant must never be able to see or touch another tenant's data.** I implemented a defense-in-depth approach with three independent layers of isolation.

### Layer 1: Application-Level Middleware

A custom `TenantMiddleware` intercepts every request and validates the tenant context before any domain logic executes:

```python
class TenantMiddleware:
    def __call__(self, request):
        # Extract tenant from JWT or header
        tenant_id = request.headers.get('X-Tenant-ID')
        
        # Validate user has access to this tenant
        if hasattr(request, 'user') and request.user.is_authenticated:
            allowed_tenant_ids = request.user.tenantuser_set.values_list('tenant_id', flat=True)
            if tenant_id not in allowed_tenant_ids:
                return JsonResponse({'error': 'Tenant access denied'}, status=403)
        
        # Thread-local storage for downstream use
        request.tenant_id = tenant_id
        return self.get_response(request)
```

**Why this approach:**
- **Early validation:** Tenant context is established before any business logic runs
- **User-Aware:** Validates the user actually belongs to the claimed tenant
- **Explicit:** Every request must specify a tenant; no implicit defaults

### Layer 2: Database-Level Row-Level Security (RLS)

PostgreSQL RLS provides the ultimate safety net—even if the ORM filter fails, the database itself rejects cross-tenant queries:

```sql
-- Enable RLS on all tenant-scoped tables
ALTER TABLE candidates ENABLE ROW LEVEL SECURITY;
ALTER TABLE compliance_documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

-- Set current tenant at session level
SET LOCAL app.current_tenant = 'tenant-uuid-here';

-- Policies enforce isolation at query time
CREATE POLICY tenant_isolation_policy ON candidates 
    USING (tenant_id = current_setting('app.current_tenant')::uuid);
```

**Why RLS over just ORM filters:**
- **Defense in depth:** Even if code bypasses the ORM (raw SQL, admin panel, etc.), RLS still applies
- **Auditable:** Enforced at the database level, not just application logic
- **Performance:** PostgreSQL applies policies efficiently at the query planning stage
- **No application changes needed:** Works transparently with all queries

### Layer 3: Query Filtering in Views

The Django ORM automatically filters all queries:

```python
class CandidateViewSet:
    def get_queryset(self):
        return Candidate.objects.filter(
            tenant_id=self.request.tenant_id,
            is_active=True
        )
```

### Why This Approach Works

| Layer | Protection | Bypass Risk |
|-------|-----------|-------------|
| Application Middleware | Validates JWT and tenant access | Low (requires forged JWT) |
| ORM Query Filtering | Filters all model queries | Medium (raw SQL bypass) |
| PostgreSQL RLS | Last line of defense | Very Low (requires direct DB access) |

---

## 3. Immutable Audit Ledger

### Design Principles

The audit system follows strict append-only semantics—logs are never updated or deleted. This ensures a tamper-evident audit trail for compliance and forensic purposes.

### Implementation

**Model-Level Enforcement:**

```python
class AuditLog(models.Model):
    # ... fields ...
    
    def save(self, *args, **kwargs):
        if self.pk:  # Existing record
            raise ValueError("Audit logs are immutable and cannot be updated")
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        raise ValueError("Audit logs are immutable and cannot be deleted")
```

**Hash-Based Tamper Evidence:**

Every audit log stores SHA-256 hashes of the data before and after each operation:

```python
class AuditService:
    @staticmethod
    def _compute_hash(data):
        content = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()
```

**Audited Operations:**

| Action | When Triggered | Stored Data |
|--------|---------------|-------------|
| CREATE | New candidate/document created | Full record data + after_hash |
| UPDATE | Record modified | before_hash + after_hash |
| DELETE | Record soft-deleted | before_hash |
| READ | Sensitive data accessed | Data accessed |
| VERIFY | Document verification | Verification result |
| LOGIN/LOGOUT | Authentication events | Timestamp and context |

### Why This Matters

- **Regulatory Compliance:** Satisfies GDPR, HIPAA, and SOC2 audit requirements
- **Security Investigations:** Complete history of all actions for incident response
- **Data Integrity:** Hashes detect any tampering with historical records
- **Non-Repudiation:** Clear chain of custody for all operations

---

## 4. Versioned Compliance Documents

### Problem Statement

Compliance documents (Right-to-Work, DBS checks, certifications) must maintain history—an approved document that is corrected should preserve the original version while superseding it with the new version.

### Solution Design

**Versioning Model:**

```python
class ComplianceDocument(models.Model):
    version = models.IntegerField(default=1)
    is_current = models.BooleanField(default=True)
    superseded_by = models.ForeignKey('self', null=True, blank=True)
```

**Version Creation Flow:**

1. **Transaction opens** - Wrapped in `@transaction.atomic`
2. **Find existing current document** - Query for `is_current=True`
3. **Supersede old version** - Set `is_current=False`, link to new version
4. **Create new version** - Increment version number, mark as current
5. **Audit both versions** - Log the change in audit trail

```python
@transaction.atomic
def add_document(candidate, new_data):
    existing = ComplianceDocument.objects.filter(
        candidate=candidate,
        document_type=new_data['document_type'],
        is_current=True
    ).first()
    
    if existing:
        existing.is_current = False
        existing.save()
    
    new_doc = ComplianceDocument.objects.create(
        candidate=candidate,
        **new_data,
        version=(existing.version + 1) if existing else 1,
        superseded_by=existing,
        is_current=True
    )
```

### What Gets Preserved

- Original document data, status, and verification history
- Complete version lineage (v1 → v2 → v3)
- Audit trail linking all versions together
- Who made the change and when

---

## 5. Asynchronous Verification Workflow

### Challenge

Document verification (e.g., Right-to-Work checks) can take time and may involve external services. The system should not block on verification.

### Solution: Celery + Redis

```python
@shared_task
def verify_document(document_id):
    # Idempotency check
    document = ComplianceDocument.objects.get(id=document_id)
    if document.status != 'pending':
        return {'status': 'already_processed'}
    
    # Simulate external verification
    result = external_verification_service.check(document)
    
    # Update status
    document.status = 'verified' if result.passed else 'failed'
    document.save()
    
    # Audit the verification
    AuditService.log_verify(...)
```

**API Call:**

```python
@action(detail=True, methods=['post'])
def verify(self, request, pk=None):
    document = self.get_object()
    task = verify_document.delay(str(document.id))
    return Response({
        'document_id': str(document.id),
        'status': 'processing',
        'task_id': task.id
    })
```

### Trade-offs

| Alternative | Pros | Cons |
|-------------|------|------|
| Celery + Redis (Chosen) | Simple, well-understood, works with Django | Potential message loss if Redis crashes |
| Transactional Outbox | Guaranteed delivery | More complex to implement |
| Synchronous API | Simpler code | Blocks requests, poor UX |

### Idempotency

The task checks the document status before processing, preventing duplicate verifications even if the task runs multiple times.

---

## 6. Governed AI Feature

### Overview

The AI feature extracts structured data from CVs (full name, email, skills, years of experience, certifications) using an LLM. Key design decisions ensure compliance, auditability, and user control.

### Architecture

```
1. User uploads CV → 2. Text extraction (PyPDF2) → 3. LLM call → 4. Validation → 5. Human Review → 6. Candidate Creation
```

### AI NEVER Auto-Rejects Candidates

The system treats AI output as a **proposed** extraction that requires human confirmation:

```python
class AIExtraction(models.Model):
    status = models.CharField(
        choices=[
            ('pending_confirmation', 'Pending Confirmation'),
            ('confirmed', 'Confirmed'),
            ('rejected', 'Rejected'),
        ]
    )
    extracted_data = models.JSONField()
```

**Flow:**
1. AI extracts data → `status = 'pending_confirmation'`
2. Recruiter reviews and confirms → `status = 'confirmed'` → Candidate created
3. Recruiter rejects → `status = 'rejected'` → No candidate created

### AI Audit Trail

Every AI operation is logged with:
- Model used (mock/openai/claude)
- Input hash (CV text hash)
- Output hash (extracted data hash)
- Confirmation/rejection by user
- Purpose (extraction, confirmation, rejection)

### LLM Abstraction

```python
class LLMService:
    def extract_cv_data(self, text):
        if self.model == 'mock':
            return self._mock_extract(text)  # Regex-based for dev
        elif self.model == 'openai':
            return self._openai_extract(text)
        elif self.model == 'claude':
            return self._claude_extract(text)
```

**Benefits:**
- Easy to switch between providers
- Mock mode for development/testing
- No vendor lock-in

### Trade-offs

| Decision | Rationale | Trade-off |
|----------|-----------|-----------|
| Mock AI by default | No API keys needed for development | Requires switching for production |
| Human confirmation required | Compliance, accuracy, fairness | More user effort |
| Store full CV text | Auditability, retraining | Storage overhead |

---

## 7. Scaling to Microservices

### Future Extraction Strategy

If this module were extracted into its own service, I would adopt the following architecture:

**Event-Driven Communication:**

```
┌─────────────┐    TenantCreated    ┌─────────────────┐
│   Platform  │ ───────────────────► │  Compliance     │
│   Service   │                      │  Service        │
│             │ ◄─────────────────── │                  │
└─────────────┘    CandidateVerified │                  │
                                     └─────────────────┘
                                           │
                                           ▼
                                     ┌─────────────────┐
                                     │  AI Worker      │
                                     │  Fleet          │
                                     └─────────────────┘
```

**Event Types:**
- `TenantCreated` - Provision compliance module for new tenant
- `CandidateAdded` - Trigger compliance checks
- `DocumentVerified` - Notify platform of verification completion
- `CVUploaded` - Queue for AI processing

### API Gateway Approach

```
External Requests → API Gateway → Compliance Service
                                  → AI Worker Fleet
                                  → Notification Service
```

### Database Considerations

- **Private database per service** - No direct sharing
- **Read replicas for reporting** - Offload analytical queries
- **Eventual consistency** - Acceptable for non-critical operations

---

## 8. Trade-offs Made Under Time Pressure

### 1. Outbox Pattern vs. Celery Broker

**Chosen:** Celery with Redis broker
**Alternative:** Transactional outbox with database polling

**Why I chose Celery:**
- Faster implementation (10-16 hour window)
- Works with Django's existing infrastructure
- Redis is simple to set up locally

**What I would change for production:**
- Implement transactional outbox table
- Use Kafka or RabbitMQ instead of Redis
- Set up Dead Letter Queue for failed messages
- Add monitoring and alerting for queue health

### 2. AI Mocking

**Chosen:** Mock implementation with regex extraction
**Alternative:** Real OpenAI/Claude integration

**Why I chose mock:**
- No API keys required for development
- Works offline
- Predictable results for testing

**What I would change for production:**
- Real LLM integration with fallback
- Prompt engineering for better extraction
- Response validation against schemas
- Cost monitoring and rate limiting

### 3. Audit Log Error Handling

**Chosen:** Audit failures logged but don't block main operation
**Alternative:** Fail the operation if audit fails

**Why I chose non-blocking:**
- Business operations should succeed even if audit fails
- Audit logs can be repaired later
- Better user experience

**What I would change for production:**
- Retry mechanism for failed audits
- Monitoring for audit failures
- Backup audit to separate system

### 4. Database Constraints

**Chosen:** Database-level constraints + application validation
**Alternative:** Application-only validation

**Why I chose both:**
- Defense in depth
- Data integrity at multiple levels
- Catches edge cases

**What I would change for production:**
- More comprehensive tests
- Database triggers for complex validation
- Automated migration rollbacks

---

## 9. Key Learnings & Recommendations

### What Worked Well

1. **Defense-in-depth tenant isolation** - Multiple layers catch different failure modes
2. **Immutable audit logs** - Simple model with strong guarantees
3. **AI abstraction** - Easy to swap implementations
4. **Versioned documents** - Preserves history without complexity

### What Could Be Improved

1. **Transactional outbox** - Would provide stronger delivery guarantees
2. **Better AI error handling** - Handle LLM failures gracefully
3. **More extensive testing** - Integration and load tests
4. **API versioning** - Support multiple API versions

### Production Recommendations

1. **Monitoring:**
   - Datadog/New Relic for application metrics
   - Sentry for error tracking
   - Prometheus for system metrics

2. **Performance:**
   - Query optimization with `select_related` and `prefetch_related`
   - Database connection pooling
   - Redis caching for frequently accessed data

3. **Security:**
   - Regular security audits
   - Rate limiting on API endpoints
   - Automated secret rotation

4. **Compliance:**
   - Regular audit log reviews
   - Data retention policies
   - GDPR/CCPA compliance tools

---

## 10. Tools & AI Usage

### AI Assistants Used

- **DeepSeek:** Code generation, architectural decisions, debugging assistance
- **Google Gemini:** Code snippets, documentation, refactoring suggestions

### How I Used AI

1. **Code Generation:** Generated boilerplate code for serializers, views, and URL routing
2. **Debugging:** Identified and fixed import errors, model field mismatches, and CORS issues
3. **Architectural Decisions:** Discussed trade-offs between different approaches (RLS vs ORM, Celery vs Outbox)
4. **Documentation:** Drafted README and architecture notes
5. **Testing:** Generated test cases and validation logic

### Where I Exercised My Own Judgement

- **Security:** Validated that JWT and RLS provide adequate isolation
- **Data Modeling:** Designed the schema to balance normalization and performance
- **Error Handling:** Decided which errors should fail operations vs be logged
- **Trade-offs:** Made final decisions on implementation choices based on time constraints

---

## 11. Conclusion

This implementation demonstrates a production-ready vertical slice of the Erp Candidate Compliance module with:

-  **Multi-tenant isolation** at three independent layers
-  **Immutable audit logging** with tamper evidence
-  **Versioned compliance records** preserving history
-  **Async verification workflow** with Celery
-  **Governed AI feature** with human confirmation
-  **Clean API design** with OpenAPI documentation
-  **React/Next.js frontend** with tenant-aware UI

The architecture is designed to scale and can be extracted into separate services when needed, with most changes occurring at the integration layer rather than in core business logic.

---

*Architecture review and implementation by Samuel E. Igbinovia*
*Date: August 2026