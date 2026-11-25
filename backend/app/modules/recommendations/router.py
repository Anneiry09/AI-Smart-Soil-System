from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/approvals", tags=["Human-in-the-Loop AI Agent"])

class ApprovalAction(BaseModel):
    action: str  # approve, reject, modify
    notes: Optional[str] = None

# Bộ nhớ tạm lưu trạng thái các thẻ phê duyệt
APPROVAL_CARDS = [
    {
        "id": "APP-01",
        "type": "WAREHOUSE_COMBO",
        "badge": "Xuất Kho Nông Thịnh",
        "badge_color": "green",
        "title": "Đề xuất Combo Phân bón Phục hồi Thổ nhưỡng",
        "subtitle": "Căn cứ chẩn đoán AI: Vườn sầu riêng đang bị chua phèn (pH 4.8) và thiếu hữu cơ",
        "details": {
            "target_farm": "Nhà vườn Anh Hùng (Huyện Cẩm Mỹ, Đồng Nai)",
            "combo_name": "Bộ Giải Độc Đất & Kích Rễ Chuyên Sâu Nông Thịnh",
            "items": [
                "1 Can 5L Humic Acid Nhập Khẩu Mỹ (Kích thích rễ tơ)",
                "1 Xô 20kg Tinh Vôi Sữa Nano Nông Thịnh (Khử chua tức thời)",
                "2 Chai 500ml Vi Lượng Chelated Tổng Hợp"
            ],
            "total_value": "1.450.000 VNĐ",
            "stock_status": "Sẵn hàng tại Kho Nông Thịnh Đồng Nai"
        },
        "status": "PENDING"
    },
    {
        "id": "APP-02",
        "type": "LOGISTICS_GROUPING",
        "badge": "Gom Đơn Ghép Chuyến",
        "badge_color": "blue",
        "title": "Gợi ý Gom 3 Đơn Hàng Cùng Tuyến Vận Chuyển",
        "subtitle": "Tối ưu hóa logistics giao phân bón khu vực Cẩm Mỹ - Long Khánh",
        "details": {
            "route": "Kho Long Khánh -> Vườn Anh Hùng -> Vườn Chú Ba -> Vườn Tân Phú",
            "total_cargo_weight": "480 kg",
            "cost_saving": "Tiết kiệm 35% chi phí vận chuyển (giảm 240.000đ)",
            "estimated_delivery": "15:30 Chiều nay (23/11/2026)"
        },
        "status": "PENDING"
    },
    {
        "id": "APP-03",
        "type": "SEO_ARTICLE",
        "badge": "Bài Viết Chuẩn SEO",
        "badge_color": "purple",
        "title": "Bản nháp Phân tích Kỹ thuật Nông nghiệp Tự động",
        "subtitle": "AI Agent tự động trích xuất đồ thị phục hồi đất thực tế để soạn bài truyền thông",
        "details": {
            "headline": "Giải pháp cấp cứu rễ sầu riêng đầu mùa khô: Bài học thực nghiệm từ cảm biến 7-in-1",
            "channels": "Fanpage Kỹ Thuật Nông Thịnh & Website nongthinh.vn",
            "attached_evidence": "Biểu đồ phục hồi pH từ 4.8 lên 6.5 và đồ thị vi khí hậu 3 ngày liên tiếp",
            "seo_score": "92/100 (Từ khóa: hạ phèn sầu riêng, kích rễ mùa khô, nongthinh.vn)"
        },
        "status": "PENDING"
    }
]

@router.get("/")
def get_approval_cards():
    """Lấy danh sách các Thẻ Phê Duyệt đang chờ hoặc đã xử lý."""
    return APPROVAL_CARDS

@router.post("/{card_id}/action")
def act_on_approval(card_id: str, payload: ApprovalAction):
    """Thực hiện phê duyệt, chỉnh sửa hoặc từ chối đề xuất của AI Agent."""
    card = next((c for c in APPROVAL_CARDS if c["id"] == card_id), None)
    if not card:
        raise HTTPException(status_code=404, detail="Không tìm thấy thẻ phê duyệt")
        
    action_map = {
        "approve": "APPROVED",
        "reject": "REJECTED",
        "modify": "MODIFIED"
    }
    
    new_status = action_map.get(payload.action.lower(), "PENDING")
    card["status"] = new_status
    if payload.notes:
        card["notes"] = payload.notes
        
    return {
        "status": "success",
        "card_id": card_id,
        "new_status": new_status,
        "message": f"Đã thực hiện thao tác '{payload.action}' thành công!"
    }
