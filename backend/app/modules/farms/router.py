from fastapi import APIRouter

router = APIRouter(prefix="/farms", tags=["Farms"])

@router.get("/")
def list_farms():
    # Sẽ hoàn thiện ở Milestone 4.1
    return [{"id": 1, "name": "Vườn Nông Thịnh - Đồng Nai", "location": "Đồng Nai"}]
