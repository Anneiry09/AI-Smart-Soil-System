from fastapi import APIRouter

router = APIRouter(prefix="/recommendations", tags=["Recommendations"])

@router.get("/{device_id}")
def get_recommendations(device_id: str):
    # Sẽ hoàn thiện ở Milestone 4.2
    return {"device_id": device_id, "recommendations": []}
