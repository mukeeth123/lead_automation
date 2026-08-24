from fastapi import APIRouter

router = APIRouter()

@router.get("/overview")
async def get_overview():
    return {"status": "mock data not implemented yet"}
