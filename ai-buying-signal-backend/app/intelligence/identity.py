import json
import logging
from typing import Optional
from pydantic import BaseModel
from app.agents.intelligence import call_llm_with_fallback

logger = logging.getLogger(__name__)

class IdentityResult(BaseModel):
    person_name: Optional[str]
    job_title: Optional[str]
    company_name: Optional[str]
    email: Optional[str]
    linkedin_url: Optional[str]
    confidence_score: int

class IdentityResolutionEngine:
    async def resolve_identity(self, text_content: str, author_username: str) -> IdentityResult:
        """
        Step 1: Use LLM to extract structured identity data from the raw signal context.
        """
        prompt = f"""
        Extract the identity of the person posting this message, or the company they represent.
        
        Author Username: {author_username}
        Text: {text_content[:1000]}
        
        Return ONLY valid JSON matching this schema:
        {{
            "person_name": "Full name if present, else null",
            "job_title": "Title if mentioned (e.g. 'Founder', 'CTO'), else null",
            "company_name": "Company name if mentioned, else null",
            "email": "Email address if provided, else null",
            "linkedin_url": "LinkedIn URL if provided, else null",
            "confidence_score": integer 0-100 (100 if email/linkedin explicitly found)
        }}
        """
        
        messages = [{"role": "user", "content": prompt}]
        
        try:
            result_text = await call_llm_with_fallback(messages, temperature=0.0, expect_json=True)
            data = json.loads(result_text)
            
            # Step 2: Fallback enrichment via API (Apollo/Clearbit stub)
            enriched_data = await self._enrich_via_api(
                person_name=data.get("person_name"),
                company_name=data.get("company_name"),
                email=data.get("email")
            )
            
            return IdentityResult(
                person_name=enriched_data.get("person_name") or data.get("person_name"),
                job_title=enriched_data.get("job_title") or data.get("job_title"),
                company_name=enriched_data.get("company_name") or data.get("company_name"),
                email=enriched_data.get("email") or data.get("email"),
                linkedin_url=enriched_data.get("linkedin_url") or data.get("linkedin_url"),
                confidence_score=data.get("confidence_score", 0)
            )
        except Exception as e:
            logger.error(f"Identity resolution failed: {e}")
            return IdentityResult(
                person_name=None, job_title=None, company_name=None,
                email=None, linkedin_url=None, confidence_score=0
            )

    async def _enrich_via_api(self, person_name: str = None, company_name: str = None, email: str = None) -> dict:
        """
        Stub for Apollo/Clearbit enrichment API.
        If the LLM extracted a company but no email, we would call an external API to find the domain and email format.
        """
        if company_name and not email:
            # Simulate a successful API enrichment hit
            if "startup" in company_name.lower():
                return {
                    "email": f"founder@{company_name.lower().replace(' ', '')}.com",
                    "job_title": "Founder / CEO"
                }
        return {}
