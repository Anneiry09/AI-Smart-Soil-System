"""
Kiểm thử chuyên sâu Tầng Chẩn Đoán Thổ Nhưỡng Tổng Thể & Khử Mâu Thuẫn:
Xác thực 3 kịch bản trọng tâm:
  1. Kịch bản Đất Mặn Cao (EC = 2880 uS/cm, Moisture = 44%, pH = 6.5, Temp = 29°C)
     -> Kiểm tra: TUYỆT ĐỐI không có lời khuyên mâu thuẫn "tưới duy trì" hoặc "bón phân ngay".
     -> Bắt buộc có crop_prerequisite_note cảnh báo rửa mặn trước khi gieo trồng.
     -> Phác đồ 4 bước chuẩn xác: Rửa mặn -> Ngưng phân vô cơ -> Theo dõi EC < 1500 -> Phân hữu cơ/Humic.
  2. Kịch bản Đất Tốt Phì Nhiêu (Moisture = 55%, pH = 6.6, EC = 750 uS/cm)
     -> Kiểm tra: 4 trụ cột đều ổn định, không có rủi ro, điểm cao, không có cảnh báo tiên quyết.
  3. Kịch bản Lỗi Cảm Biến RS485 (Nhiệt độ âm sâu, mất tín hiệu NPK)
     -> Kiểm tra: Lớp 0 chặn ngay, status HARDWARE_ERROR, không in kết luận sai lệch.
"""

import sys
import os
import json

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.modules.soil_ai.evaluator import SoilAIEvaluator

def test_holistic_scenarios():
    evaluator = SoilAIEvaluator.get_instance()
    print("=" * 75)
    print(" BẮT ĐẦU KIỂM THỬ TẦNG CHẨN ĐOÁN TỔNG HỢP & KHỬ MÂU THUẪN (SOIL AI)")
    print("=" * 75)

    # -------------------------------------------------------------------------
    # KỊCH BẢN 1: ĐẤT MẶN CAO (EC = 2880 uS/cm)
    # -------------------------------------------------------------------------
    print("\n[KỊCH BẢN 1] Kiểm tra Đất Mặn Cao (EC = 2880 µS/cm, Độ ẩm 44%, pH 6.5)...")
    res1 = evaluator.evaluate(
        moisture=44.0,
        temperature=29.0,
        ec=2880.0,
        ph=6.5,
        n=72.0,
        p=36.0,
        k=112.0
    )

    print("  -> Primary Risk:", res1["primary_risk"])
    print("  -> Risk Level:", res1["risk_level"])
    print("  -> Overall Title:", res1["overall_title"])
    print("  -> Prerequisite Note:", res1["crop_prerequisite_note"])
    print("  -> Action Plan:")
    for step in res1["action_plan"]:
        print(f"     Bước {step['step']} [{step['priority_vi']}]: {step['title']}")

    # Kiểm tra tính phi mâu thuẫn (Contradiction-free checks)
    full_text = " ".join([s["title"] + " " + s["detail"] for s in res1["action_plan"]])
    assert "Duy trì chế độ tưới tiêu hiện tại" not in full_text, "LỖI MÂU THUẪN: Đất mặn lại khuyên duy trì tưới tiêu!"
    assert "bón phân cân đối ngay" not in full_text.lower(), "LỖI MÂU THUẪN: Đất mặn lại khuyên bón phân ngay!"
    assert res1["crop_prerequisite_note"] is not None, "LỖI: Thiếu cảnh báo tiên quyết rửa mặn cho cây trồng!"
    assert res1["action_plan"][0]["priority"] == "KHAN_CAP", "LỖI: Bước 1 phải là khẩn cấp rửa mặn!"
    assert res1["risk_level"] in ["HIGH", "CRITICAL"], "LỖI: Mức độ rủi ro mặn phải là HIGH hoặc CRITICAL!"
    print("  ==> KỊCH BẢN 1: ĐẠT CHUẨN KHỬ MÂU THUẪN 100% (PASS)")

    # -------------------------------------------------------------------------
    # KỊCH BẢN 2: ĐẤT TỐT PHÌ NHIÊU (Moisture = 55%, pH = 6.6, EC = 750)
    # -------------------------------------------------------------------------
    print("\n[KỊCH BẢN 2] Kiểm tra Đất Tốt Phì Nhiêu (Ẩm 55%, pH 6.6, EC 750 µS/cm)...")
    res2 = evaluator.evaluate(
        moisture=55.0,
        temperature=27.0,
        ec=750.0,
        ph=6.6,
        n=115.0,
        p=45.0,
        k=160.0
    )

    print("  -> Overall Title:", res2["overall_title"])
    print("  -> Điểm sức khỏe:", res2["soil_health"]["health_score"])
    print("  -> Trụ cột đánh giá:")
    for p in res2["pillars"]:
        print(f"     + {p['title']}: {p['value_text']} -> {p['status_vi']}")

    assert res2["risk_level"] == "LOW", "LỖI: Đất tốt phải có risk_level LOW!"
    assert res2["crop_prerequisite_note"] is None, "LỖI: Đất tốt không được có cờ cảnh báo cản trở gieo trồng!"
    assert all(p["status"] == "TOT" for p in res2["pillars"]), "LỖI: Tất cả 4 trụ cột phải đạt trạng thái TOT!"
    assert res2["soil_health"]["health_score"] >= 75.0, "LỖI: Điểm đất tốt phải >= 75!"
    print("  ==> KỊCH BẢN 2: ĐẠT CHUẨN XUẤT SẮC (PASS)")

    # -------------------------------------------------------------------------
    # KỊCH BẢN 3: LỖI CẢM BIẾN RS485 (LỚP 0)
    # -------------------------------------------------------------------------
    print("\n[KỊCH BẢN 3] Kiểm tra Lỗi Cảm Biến RS485 (Moisture = 3%, Temp = -35°C, EC=N=P=K=0)...")
    res3 = evaluator.evaluate(
        moisture=3.0,
        temperature=-35.0,
        ec=0.0,
        ph=14.0,
        n=0.0,
        p=0.0,
        k=0.0
    )

    print("  -> Hardware Error Detected:", res3.get("is_hardware_error"))
    print("  -> Status:", res3.get("status"))
    print("  -> Fault Reasons:", res3.get("fault_reasons"))

    assert res3.get("is_hardware_error") is True, "LỖI: Không phát hiện lỗi phần cứng Lớp 0!"
    assert res3.get("status") == "HARDWARE_ERROR", "LỖI: Status phải là HARDWARE_ERROR!"
    assert len(res3.get("fault_reasons", [])) >= 3, "LỖI: Phải liệt kê đủ các nguyên nhân vi phạm!"
    print("  ==> KỊCH BẢN 3: ĐẠT CHUẨN BẢO VỆ PHẦN CỨNG (PASS)")

    print("\n" + "=" * 75)
    print(" TẤT CẢ 3 KỊCH BẢN NGHIỆM THU ĐÃ VƯỢT QUA KIỂM THỬ THÀNH CÔNG! ")
    print("=" * 75)

if __name__ == "__main__":
    test_holistic_scenarios()
