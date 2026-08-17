import json
import os
import openai

class LLMService:
    """Service for LLM integration with clear interface for mocking"""
    
    def __init__(self):
        self.model = os.environ.get('AI_MODEL', 'mock')
        self.api_key = os.environ.get('AI_API_KEY', '')
    
    def extract_cv_data(self, text):
        """Extract structured data from CV text"""
        
        if self.model == 'mock':
            return self._mock_extract(text)
        elif self.model == 'openai':
            return self._openai_extract(text)
        elif self.model == 'claude':
            return self._claude_extract(text)
        else:
            return self._mock_extract(text)
    
    def _mock_extract(self, text):
        """Mock extraction for development"""
        # Simulate extraction - in production, this would use actual LLM
        import re
        
        # Simple regex-based extraction for demo
        name_match = re.search(r'(?:Name|Full Name):?\s*([A-Za-z\s]+)', text, re.IGNORECASE)
        email_match = re.search(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
        experience_match = re.search(r'(\d+)\s*(?:years?|yrs?)(?:\s*experience)?', text, re.IGNORECASE)
        
        return {
            'success': True,
            'model': 'mock',
            'data': {
                'full_name': name_match.group(1).strip() if name_match else 'Not found',
                'email': email_match.group(0) if email_match else 'Not found',
                'skills': ['Python', 'Django', 'React', 'PostgreSQL'],  # Mock skills
                'years_experience': int(experience_match.group(1)) if experience_match else 0,
                'certifications': ['AWS Certified', 'Project Management']
            }
        }
    
    def _openai_extract(self, text):
        """OpenAI integration"""
        try:
            
            openai.api_key = self.api_key
            
            prompt = f"""
            Extract the following fields from this CV text:
            - full_name
            - email
            - skills (list)
            - years_experience (integer)
            - certifications (list)
            
            Return as valid JSON.
            
            CV Text:
            {text[:4000]}
            """
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            result = json.loads(response.choices[0].message.content)
            return {
                'success': True,
                'model': 'openai',
                'data': result
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def _claude_extract(self, text):
        """Claude integration"""
        # Similar to OpenAI integration
        return self._mock_extract(text)