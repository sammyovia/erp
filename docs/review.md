# Code Review Feedback

**Review of `GET /candidates` endpoint**

This PR requires substantial changes before it can be merged. It currently contains critical security vulnerabilities, violates our multi-tenant isolation guarantees, and lacks basic API maturity.

### 1. Security & Tenant Isolation (Critical)
*   **SQL Injection:** The `search` query parameter is concatenated directly into the SQL string (`'%${search}%'`). This allows arbitrary SQL execution.
    *   *Fix:* Use parameterized queries (e.g., `WHERE name ILIKE ?` or the ORM's equivalent).
*   **Broken Tenant Isolation:** `req.query.tenantId` is completely untrusted user input. A user from Tenant A could pass `?tenantId=TenantB` and view their data. Furthermore, the SQL query doesn't even use the `tenantId` to filter the rows, meaning it returns candidates for *all* tenants.
    *   *Fix:* The `tenantId` must be securely extracted from the authenticated user's context (e.g., JWT token claims), never from a query string. The query must explicitly filter by this authenticated tenant ID.

### 2. Authentication & Authorization (Critical)
*   **Missing Auth Middleware:** There is no authentication check protecting this endpoint. It is exposed to the public internet.
    *   *Fix:* Apply our standard Auth middleware.
*   **Missing Authorization (Permissions):** There is no check to ensure the user actually has the "read:candidates" permission.
    *   *Fix:* Apply RBAC/policy checks before executing business logic.

### 3. API Design & Reliability (Major)
*   **Missing Pagination:** Returning `SELECT *` on a potentially massive table will cause memory bloat and degrade performance.
    *   *Fix:* Implement cursor-based or offset/limit pagination.
*   **Error Handling:** There is no `try/catch` block. If the DB connection fails, the Node process might crash or leak a stack trace to the client.
    *   *Fix:* Wrap in a try/catch and return an RFC 7807 Problem Details JSON error.
*   **Data Leakage:** `SELECT *` returns all columns, which likely includes sensitive PII, internal IDs, or audit hashes that the client shouldn't see.
    *   *Fix:* Explicitly select only the fields required by the UI API contract (or use a Data Transfer Object / Serializer).

### 4. Code Quality (Minor)
*   **Logging PII:** `console.log('Returned candidates', rows)` logs candidate PII to standard out, violating GDPR/compliance policies.
    *   *Fix:* Remove the console log. Use a structured logger (e.g., Pino) to log the *action* and *count*, but never the payload.