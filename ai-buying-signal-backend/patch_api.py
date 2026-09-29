import sys

chat_route = """

from app.schemas.company import CompanyChatRequest, CompanyChatResponse
from app.agents.intelligence import groq_client, GROQ_MODEL

@router.post("/{company_id}/chat", response_model=CompanyChatResponse)
async def chat_with_company(company_id: str, request: CompanyChatRequest, db: Session = Depends(get_db)):
    company = db.query(Company).filter(Company.id == company_id).first()
    if not company:
        raise HTTPException(status_code=404, detail="Company not found")
        
    enriched = company.enriched_data or {}
    raw_context = enriched.get("raw_context", "(No raw context available)")
    
    prompt = f"\"\"\"\nYou are a helpful AI Sales Assistant. You are answering a salesperson's questions about the company: {company.name}.\n\nHere is all the raw scraped data we found on them:\n\n{raw_context}\n\nHere is the ICP Summary we generated: {enriched.get('description', '')}\n\nAnswer the user's question directly and concisely based on this information. If the answer is not in the text, say 'I don't have that information in my scraped context.'\n\"\"\""
    
    try:
        response = await groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": request.message}
            ],
            temperature=0.3
        )
        reply = response.choices[0].message.content
        return {"reply": reply}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
"""

with open(r'C:\Users\mukee\social media listening\ai-buying-signal-backend\app\api\v1\companies.py', 'a', encoding='utf8') as f:
    f.write(chat_route)
