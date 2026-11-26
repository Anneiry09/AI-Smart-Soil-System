from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Optional

from app.modules.soil_ai.evaluator import SoilAIEvaluator

router = APIRouter(prefix="/soil-ai", tags=["Soil AI Evaluation"])

class SoilEvaluationRequest(BaseModel):
    moisture: float = Field(..., description="Độ ẩm đất (%)", examples=[45.0])
    temperature: float = Field(..., description="Nhiệt độ đất (°C)", examples=[28.5])
    ec: float = Field(..., description="Độ dẫn điện EC (uS/cm)", examples=[720.0])
    ph: float = Field(..., description="Độ chua pH (0-14)", examples=[6.5])
    nitrogen: float = Field(..., description="Đạm N (ppm)", examples=[60.0])
    phosphorus: float = Field(..., description="Lân P (ppm)", examples=[28.0])
    potassium: float = Field(..., description="Kali K (ppm)", examples=[95.0])
    humidity: Optional[float] = Field(None, description="Độ ẩm không khí (%)", examples=[75.0])
    rainfall: Optional[float] = Field(None, description="Lượng mưa (mm)", examples=[150.0])

@router.post(
    "/evaluate",
    summary="Đánh giá sức khỏe đất và gợi ý cây trồng thời gian thực",
    response_description="Kết quả phân tích AI và khuyến nghị nông học"
)
def evaluate_soil(payload: SoilEvaluationRequest):
    """
    Endpoint tiếp nhận dữ liệu 7 chỉ số đất để:
    1. Lọc lỗi phần cứng RS485 (Lớp 0)
    2. Đánh giá 4 trụ cột thổ nhưỡng (Lý tính, Hóa tính, Độ mặn, Dinh dưỡng)
    3. Chẩn đoán tổng hợp & Khử mâu thuẫn triệt để
    4. Chấm điểm sức khỏe đất (Model A - XGBoost) kèm giải thích TreeSHAP
    5. Gợi ý Top 3 cây trồng phù hợp nhất (Model B - Random Forest) kèm điều kiện tiên quyết
    6. Phác đồ hành động canh tác theo thứ tự ưu tiên (action_plan)
    """
    evaluator = SoilAIEvaluator.get_instance()
    analysis_meta = {
        "sample_count": 1,
        "analyzed_at": datetime.now().isoformat(),
        "aggregation": "direct_input"
    }
    result = evaluator.evaluate(
        moisture=payload.moisture,
        temperature=payload.temperature,
        ec=payload.ec,
        ph=payload.ph,
        n=payload.nitrogen,
        p=payload.phosphorus,
        k=payload.potassium,
        humidity=payload.humidity,
        rainfall=payload.rainfall,
        analysis_meta=analysis_meta
    )
    return result

@router.get(
    "/health",
    summary="Kiểm tra trạng thái nạp các model AI"
)
def get_ai_status():
    evaluator = SoilAIEvaluator.get_instance()
    return {
        "status": "online",
        "model_a_loaded": evaluator.model_a is not None,
        "model_b_loaded": evaluator.model_b is not None,
        "anomaly_iforest_loaded": evaluator.iforest is not None,
        "tree_shap_ready": evaluator.tree_explainer is not None,
        "model_a_classes": evaluator.meta_a.get("classes", []),
        "model_b_supported_crops_count": len(evaluator.meta_b.get("classes", []))
    }
