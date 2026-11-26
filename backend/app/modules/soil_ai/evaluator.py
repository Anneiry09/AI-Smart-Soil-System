"""
Module Đánh giá Sức khỏe Thổ nhưỡng và Khuyến nghị Cây trồng (Soil AI Evaluator).
Tích hợp:
- Lớp 0: Lọc lỗi phần cứng cảm biến RS485
- Quy đổi đơn vị cảm biến (mg/kg, µS/cm) sang chuẩn Model A (kg/ha, dS/m)
- Phát hiện dị thường đất (Isolation Forest)
- Model A (XGBoost): Đánh giá phân loại sức khỏe đất (0-100) & giải thích TreeSHAP
- Model B (Random Forest): Gợi ý Top 3 cây trồng phù hợp (Việt hóa) kèm điều kiện tiên quyết
- Đánh giá 4 Trụ cột Thổ nhưỡng (Lý tính, Hóa tính, Độ mặn, Dinh dưỡng)
- Phân loại nhóm đặc tính đất (Soil Profile) trực tiếp từ cảm biến 7-in-1
- Tầng chẩn đoán tổng hợp & khử mâu thuẫn giữa các chỉ số rời rạc
- Phác đồ hành động theo thứ tự ưu tiên (Action Plan)
"""

from __future__ import annotations
import os
import json
import logging
import warnings
import importlib
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import joblib

# Suppress sklearn version mismatch warnings for pickled models
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", message=".*InconsistentVersionWarning.*")

logger = logging.getLogger("soil_ai.evaluator")

# Feature human-readable Vietnamese names
FEATURE_NAMES_VI: Dict[str, str] = {
    "n": "Hàm lượng Đạm (N)",
    "p": "Hàm lượng Lân (P)",
    "k": "Hàm lượng Kali (K)",
    "ph": "Độ chua pH",
    "ec": "Độ dẫn điện EC (độ mặn)",
    "moisture": "Độ ẩm đất",
    "temperature": "Nhiệt độ đất",
    "humidity": "Độ ẩm không khí",
    "rainfall": "Lượng mưa",
    "npk_total": "Tổng dinh dưỡng NPK",
    "n_p_ratio": "Tỉ lệ Đạm / Lân (N/P)",
    "n_k_ratio": "Tỉ lệ Đạm / Kali (N/K)",
    "p_k_ratio": "Tỉ lệ Lân / Kali (P/K)",
    "ph_dev_optimal": "Độ lệch pH so với chuẩn 6.5",
    "is_acidic_flag": "Chỉ dấu đất chua (pH < 6.0)",
    "ec_npk_ratio": "Tỉ lệ độ mặn EC / NPK",
}


class SoilAIEvaluator:
    _instance: Optional[SoilAIEvaluator] = None

    def __init__(self, artifacts_dir: Optional[str] = None):
        """Khởi tạo và nạp các model, metadata từ thư mục artifacts."""
        if artifacts_dir is None:
            artifacts_dir = os.path.join(os.path.dirname(__file__), "artifacts")
        self.artifacts_dir: str = artifacts_dir

        self.model_a: Any = None
        self.le_a: Any = None
        self.iforest: Any = None
        self.meta_a: Dict[str, Any] = {}

        self.model_b: Any = None
        self.le_b: Any = None
        self.meta_b: Dict[str, Any] = {}

        self.tree_explainer: Any = None
        self._load_artifacts()

    @classmethod
    def get_instance(cls, artifacts_dir: Optional[str] = None) -> SoilAIEvaluator:
        """Singleton instance getter."""
        if cls._instance is None:
            cls._instance = SoilAIEvaluator(artifacts_dir)
        return cls._instance

    def _load_artifacts(self) -> None:
        """Tải mô hình và metadata an toàn."""
        # 1. Model A Metadata
        meta_a_path = os.path.join(self.artifacts_dir, "soil_health_metadata.json")
        if os.path.exists(meta_a_path):
            with open(meta_a_path, "r", encoding="utf-8") as f:
                self.meta_a = json.load(f)

        # 2. Model B Metadata
        meta_b_path = os.path.join(self.artifacts_dir, "crop_metadata.json")
        if os.path.exists(meta_b_path):
            with open(meta_b_path, "r", encoding="utf-8") as f:
                self.meta_b = json.load(f)

        # 3. Label Encoders
        le_a_path = os.path.join(self.artifacts_dir, "soil_health_label_encoder.joblib")
        if os.path.exists(le_a_path):
            try:
                self.le_a = joblib.load(le_a_path)
            except Exception as e:
                logger.warning("Không thể nạp soil_health_label_encoder: %s", e)

        le_b_path = os.path.join(self.artifacts_dir, "crop_label_encoder.joblib")
        if os.path.exists(le_b_path):
            try:
                self.le_b = joblib.load(le_b_path)
            except Exception as e:
                logger.warning("Không thể nạp crop_label_encoder: %s", e)

        # 4. Anomaly Isolation Forest
        iforest_path = os.path.join(self.artifacts_dir, "anomaly_iforest.joblib")
        if os.path.exists(iforest_path):
            try:
                self.iforest = joblib.load(iforest_path)
            except Exception as e:
                logger.warning("Không thể nạp anomaly_iforest: %s", e)

        # 5. Model A: XGBoost Soil Health
        model_a_path = os.path.join(self.artifacts_dir, "soil_health_xgb.joblib")
        if os.path.exists(model_a_path):
            try:
                self.model_a = joblib.load(model_a_path)
                try:
                    shap = importlib.import_module("shap")
                    self.tree_explainer = shap.TreeExplainer(self.model_a)
                except Exception as ex_shap:
                    logger.info("TreeSHAP chưa sẵn sàng (%s), sẽ dùng phương thức giải thích thay thế.", ex_shap)
            except Exception as e:
                logger.warning("Không thể nạp Model A (soil_health_xgb): %s", e)

        # 6. Model B: Random Forest (hoặc XGBoost) Crop Recommendation
        model_b_path = os.path.join(self.artifacts_dir, "crop_rec_rf.joblib")
        if not os.path.exists(model_b_path):
            model_b_path = os.path.join(self.artifacts_dir, "crop_rec_xgb.joblib")
        if os.path.exists(model_b_path):
            try:
                self.model_b = joblib.load(model_b_path)
            except Exception as e:
                logger.warning("Không thể nạp Model B (crop_rec): %s", e)

    @staticmethod
    def check_hardware_error(
        moisture: float,
        temperature: float,
        ec: float,
        ph: float,
        n: float,
        p: float,
        k: float
    ) -> Optional[Dict[str, Any]]:
        """
        Lớp 0: Lọc lỗi phần cứng RS485 và cảm biến vật lý.
        Quy tắc:
        - temperature <= -30
        - ec >= 19000
        - ph >= 13.5
        - moisture < 5
        - ec == 0 and n == 0 and p == 0 and k == 0 (mất nguồn / đứt dây RS485)
        """
        faults: List[str] = []
        if temperature <= -30:
            faults.append(f"Nhiệt độ đo được bất thường ({temperature}°C <= -30°C)")
        if ec >= 19000:
            faults.append(f"Độ dẫn điện EC vượt ngưỡng cảm biến ({ec} >= 19000 µS/cm)")
        if ph >= 13.5:
            faults.append(f"Độ pH vượt ngưỡng vật lý ({ph} >= 13.5)")
        if moisture < 5.0:
            faults.append(f"Độ ẩm đất thấp bất thường hoặc chưa cắm que ({moisture}% < 5%)")
        if ec == 0 and n == 0 and p == 0 and k == 0:
            faults.append("Tất cả chỉ số EC và N-P-K đều bằng 0 (nghi ngờ đứt cáp RS485 hoặc mất nguồn)")

        if faults:
            return {
                "is_hardware_error": True,
                "status": "HARDWARE_ERROR",
                "fault_reasons": faults,
                "message": "Phát hiện lỗi phần cứng / cảm biến RS485. Dữ liệu không đủ điều kiện phân tích AI."
            }
        return None

    def _convert_units_for_model_a(
        self,
        n: float,
        p: float,
        k: float,
        ec: float
    ) -> Tuple[float, float, float, float]:
        """
        Quy đổi đơn vị cảm biến RS485 7-in-1 sang thang đo mà Model A / Isolation Forest
        đã được huấn luyện.

        Đã kiểm chứng trực tiếp trên ngưỡng tách (split thresholds) của soil_health_xgb.joblib
        và anomaly_iforest.joblib (bản v1.0):
          - N, P, K: thang kg/ha (ngưỡng N ~144–364, K ~359–704)  -> nhân ppm_to_kg_ha_factor (2.24)
          - EC: thang µS/cm (ngưỡng EC ~370–710 = 0.37–0.71 dS/m × 1000) -> chia ec_us_to_ds_divisor (1.0)

        Các hệ số đọc từ soil_health_metadata.json để có thể hiệu chuẩn lại mà không cần sửa code.
        Nếu metadata thiếu ec_us_to_ds_divisor thì suy ra từ ec_unit (uS/cm -> 1.0, dS/m -> 1000.0).
        """
        ppm_to_kg_ha = float(self.meta_a.get("ppm_to_kg_ha_factor", 2.24))

        if "ec_us_to_ds_divisor" in self.meta_a:
            ec_divisor = float(self.meta_a["ec_us_to_ds_divisor"])
        else:
            ec_unit = str(self.meta_a.get("ec_unit", "uS/cm")).strip().lower()
            ec_divisor = 1000.0 if ec_unit in ("ds/m", "ms/cm") else 1.0

        n_model_a = float(n) * ppm_to_kg_ha
        p_model_a = float(p) * ppm_to_kg_ha
        k_model_a = float(k) * ppm_to_kg_ha
        ec_model_a = float(ec) / ec_divisor if ec_divisor != 0 else float(ec)
        return n_model_a, p_model_a, k_model_a, ec_model_a

    def _engineer_features_model_a(self, n: float, p: float, k: float, ph: float, ec: float) -> np.ndarray:
        """Feature Engineering khớp chính xác với engineered_features của Model A."""
        npk_total = float(n + p + k)
        n_p_ratio = float(n / (p + 1e-5))
        n_k_ratio = float(n / (k + 1e-5))
        p_k_ratio = float(p / (k + 1e-5))
        ph_dev_optimal = float(abs(ph - 6.5))
        is_acidic_flag = 1.0 if ph < 6.0 else 0.0
        ec_npk_ratio = float(ec / (npk_total + 1e-5))

        feature_dict: Dict[str, float] = {
            "n": float(n),
            "p": float(p),
            "k": float(k),
            "ph": float(ph),
            "ec": float(ec),
            "npk_total": npk_total,
            "n_p_ratio": n_p_ratio,
            "n_k_ratio": n_k_ratio,
            "p_k_ratio": p_k_ratio,
            "ph_dev_optimal": ph_dev_optimal,
            "is_acidic_flag": is_acidic_flag,
            "ec_npk_ratio": ec_npk_ratio,
        }

        feature_order: List[str] = self.meta_a.get("engineered_features", [
            "n", "p", "k", "ph", "ec", "npk_total",
            "n_p_ratio", "n_k_ratio", "p_k_ratio",
            "ph_dev_optimal", "is_acidic_flag", "ec_npk_ratio"
        ])
        return np.array([[feature_dict[feat] for feat in feature_order]], dtype=np.float32)

    def _engineer_features_model_b(
        self,
        n: float,
        p: float,
        k: float,
        temperature: float,
        humidity: float,
        ph: float,
        rainfall: float
    ) -> np.ndarray:
        """Feature Engineering khớp chính xác với engineered_features của Model B."""
        npk_total = float(n + p + k)
        n_p_ratio = float(n / (p + 1e-5))
        n_k_ratio = float(n / (k + 1e-5))
        p_k_ratio = float(p / (k + 1e-5))
        ph_dev_optimal = float(abs(ph - 6.5))
        is_acidic_flag = 1.0 if ph < 6.0 else 0.0

        feature_dict: Dict[str, float] = {
            "n": float(n),
            "p": float(p),
            "k": float(k),
            "temperature": float(temperature),
            "humidity": float(humidity),
            "ph": float(ph),
            "rainfall": float(rainfall),
            "npk_total": npk_total,
            "n_p_ratio": n_p_ratio,
            "n_k_ratio": n_k_ratio,
            "p_k_ratio": p_k_ratio,
            "ph_dev_optimal": ph_dev_optimal,
            "is_acidic_flag": is_acidic_flag,
        }

        feature_order: List[str] = self.meta_b.get("engineered_features", [
            "n", "p", "k", "temperature", "humidity", "ph", "rainfall",
            "npk_total", "n_p_ratio", "n_k_ratio", "p_k_ratio",
            "ph_dev_optimal", "is_acidic_flag"
        ])
        return np.array([[feature_dict[feat] for feat in feature_order]], dtype=np.float32)

    def _explain_with_shap(self, X_arr: np.ndarray, pred_class_idx: int) -> List[Dict[str, Any]]:
        """Tính TreeSHAP hoặc ước tính đóng góp để trích xuất Top 3 yếu tố quan trọng nhất."""
        feature_order: List[str] = self.meta_a.get("engineered_features", [
            "n", "p", "k", "ph", "ec", "npk_total",
            "n_p_ratio", "n_k_ratio", "p_k_ratio",
            "ph_dev_optimal", "is_acidic_flag", "ec_npk_ratio"
        ])

        top_factors: List[Dict[str, Any]] = []
        if self.tree_explainer is not None:
            try:
                shap_vals = self.tree_explainer.shap_values(X_arr)
                if isinstance(shap_vals, list):
                    vals = shap_vals[pred_class_idx][0]
                elif getattr(shap_vals, "ndim", 0) == 3:
                    vals = shap_vals[0, :, pred_class_idx]
                else:
                    vals = shap_vals[0]

                indices = np.argsort(np.abs(vals))[::-1][:3]
                for idx in indices:
                    feat = feature_order[idx]
                    impact = float(vals[idx])
                    top_factors.append({
                        "feature": feat,
                        "name_vi": FEATURE_NAMES_VI.get(feat, feat),
                        "shap_value": round(impact, 4),
                        "direction": "Tích cực (nâng điểm)" if impact > 0 else "Tiêu cực (kéo giảm điểm)",
                        "impact_weight": round(abs(impact), 4)
                    })
                return top_factors
            except Exception as e:
                logger.debug("TreeSHAP calculation failed, fallback to importance: %s", e)

        # Fallback nếu shap chưa cài hoặc có lỗi tương thích
        if self.model_a is not None and hasattr(self.model_a, "feature_importances_"):
            importances = self.model_a.feature_importances_
            indices = np.argsort(importances)[::-1][:3]
            for idx in indices:
                feat = feature_order[idx]
                top_factors.append({
                    "feature": feat,
                    "name_vi": FEATURE_NAMES_VI.get(feat, feat),
                    "shap_value": round(float(importances[idx]), 4),
                    "direction": "Yếu tố quyết định phân loại",
                    "impact_weight": round(float(importances[idx]), 4)
                })
        return top_factors

    def _compute_influencing_factors(
        self,
        n: float,
        p: float,
        k: float,
        ph: float,
        ec: float,
        moisture: float,
        temperature: float
    ) -> List[Dict[str, Any]]:
        """
        Tính toán đóng góp nông học của các yếu tố (SHAP-equivalent agronomic impact)
        đảm bảo luôn minh bạch hóa lý do chấm điểm của AI trong mọi trường hợp.
        """
        candidates: List[Tuple[str, float, str]] = []

        # 1. EC (Độ mặn)
        if ec >= 2000.0:
            dev = -round((ec - 1000.0) / 800.0, 2)
            candidates.append(("ec", dev, "Tiêu cực (Độ mặn rất cao, kéo giảm điểm)"))
        elif ec >= 1500.0:
            dev = -round((ec - 1000.0) / 1000.0, 2)
            candidates.append(("ec", dev, "Tiêu cực (Độ mặn tăng cao)"))
        elif ec < 300.0 and ec > 0:
            dev = -round((300.0 - ec) / 300.0, 2)
            candidates.append(("ec", dev, "Tiêu cực (Đất nghèo ion khoáng)"))
        else:
            candidates.append(("ec", +0.72, "Tích cực (Độ dẫn điện an toàn)"))

        # 2. pH (Độ chua)
        dev_ph = ph - 6.5
        if ph < 5.2:
            candidates.append(("ph", -round(abs(dev_ph) * 1.1, 2), "Tiêu cực (Đất chua phèn nặng, khóa rễ)"))
        elif ph < 6.0:
            candidates.append(("ph", -round(abs(dev_ph) * 0.8, 2), "Tiêu cực (Đất hơi chua)"))
        elif ph > 7.8:
            candidates.append(("ph", -round(abs(dev_ph) * 1.1, 2), "Tiêu cực (Đất kiềm hóa cao, kết tủa khoáng)"))
        elif ph > 7.5:
            candidates.append(("ph", -round(abs(dev_ph) * 0.8, 2), "Tiêu cực (Đất hơi kiềm)"))
        else:
            candidates.append(("ph", +0.85, "Tích cực (pH lý tưởng cho hấp thu khoáng)"))

        # 3. Moisture (Độ ẩm đất)
        if moisture < 25.0:
            dev_m = -round((35.0 - moisture) / 20.0, 2)
            candidates.append(("moisture", dev_m, "Tiêu cực (Đất khô hạn nghiêm trọng)"))
        elif moisture < 35.0:
            dev_m = -round((35.0 - moisture) / 25.0, 2)
            candidates.append(("moisture", dev_m, "Tiêu cực (Độ ẩm đất thấp)"))
        elif moisture > 85.0:
            dev_m = -round((moisture - 75.0) / 20.0, 2)
            candidates.append(("moisture", dev_m, "Tiêu cực (Ngập úng bão hòa nước)"))
        elif moisture > 75.0:
            dev_m = -round((moisture - 75.0) / 25.0, 2)
            candidates.append(("moisture", dev_m, "Tiêu cực (Độ ẩm đất hơi cao)"))
        else:
            candidates.append(("moisture", +0.78, "Tích cực (Độ ẩm đất tối ưu)"))

        # 4. NPK Total (Tổng dinh dưỡng)
        npk_total = n + p + k
        if npk_total < 120.0:
            dev_npk = -round((150.0 - npk_total) / 100.0, 2)
            candidates.append(("npk_total", dev_npk, "Tiêu cực (Tổng dinh dưỡng NPK thiếu hụt)"))
        elif npk_total > 500.0:
            dev_npk = -round((npk_total - 400.0) / 200.0, 2)
            candidates.append(("npk_total", dev_npk, "Tiêu cực (Dư thừa khoáng NPK)"))
        else:
            candidates.append(("npk_total", +0.65, "Tích cực (Dinh dưỡng NPK cân đối dồi dào)"))

        # 5. Nitrogen
        if n < 40.0:
            candidates.append(("n", -round((50.0 - n) / 40.0, 2), "Tiêu cực (Hàm lượng Đạm thấp)"))
        elif n >= 65.0:
            candidates.append(("n", +0.58, "Tích cực (Đạm tốt cho sinh khối lá)"))

        # 6. Phosphorus
        if p < 15.0:
            candidates.append(("p", -round((20.0 - p) / 15.0, 2), "Tiêu cực (Hàm lượng Lân nghèo)"))
        elif p >= 30.0:
            candidates.append(("p", +0.52, "Tích cực (Lân tốt cho phát triển rễ)"))

        # 7. Potassium
        if k < 60.0:
            candidates.append(("k", -round((70.0 - k) / 50.0, 2), "Tiêu cực (Hàm lượng Kali thấp)"))
        elif k >= 100.0:
            candidates.append(("k", +0.55, "Tích cực (Kali tốt cho đề kháng cây)"))

        # Sắp xếp theo trị tuyệt đối độ tác động giảm dần
        candidates.sort(key=lambda item: abs(item[1]), reverse=True)

        top_factors: List[Dict[str, Any]] = []
        for feat, val, direction in candidates[:3]:
            top_factors.append({
                "feature": feat,
                "name_vi": FEATURE_NAMES_VI.get(feat, feat),
                "shap_value": round(val, 2),
                "impact_weight": round(abs(val), 2),
                "direction": direction
            })
        return top_factors

    def evaluate_pillars(
        self,
        moisture: float,
        temperature: float,
        ec: float,
        ph: float,
        n: float,
        p: float,
        k: float,
        soil_health_code: str
    ) -> List[Dict[str, Any]]:
        """
        Đánh giá đầy đủ 4 trụ cột thổ nhưỡng bao quát 7 chỉ số cảm biến:
        1. Lý tính (Ẩm & Nhiệt)
        2. Hóa tính (pH)
        3. Độ mặn (EC)
        4. Dinh dưỡng (NPK)
        """
        pillars = []

        # 1. Trụ cột Lý tính (Ẩm & Nhiệt)
        if moisture < 25.0 or moisture > 85.0 or temperature > 38.0 or temperature < 15.0:
            phys_status = "NGUY_HIEM"
            phys_status_vi = "Nguy hiểm"
            phys_note = "Độ ẩm/nhiệt độ nằm ngoài ngưỡng an toàn cho bộ rễ"
        elif moisture < 35.0 or moisture > 75.0 or temperature > 33.0 or temperature < 18.0:
            phys_status = "CANH_BAO"
            phys_status_vi = "Cảnh báo"
            phys_note = "Đất thiếu nước hoặc nhiệt độ khá cao"
        else:
            phys_status = "TOT"
            phys_status_vi = "Ổn định"
            phys_note = "Ẩm độ và nhiệt độ tối ưu cho hệ vi sinh và hô hấp rễ"

        pillars.append({
            "key": "physical",
            "title": "Lý tính (Ẩm & Nhiệt)",
            "status": phys_status,
            "status_vi": phys_status_vi,
            "value_text": f"{moisture:.1f}% • {temperature:.1f}°C",
            "short_note": phys_note
        })

        # 2. Trụ cột Hóa tính (pH)
        if ph < 5.0 or ph > 8.0:
            chem_status = "NGUY_HIEM"
            chem_status_vi = "Nguy hiểm"
            chem_note = "pH lệch nghiêm trọng, khóa các dưỡng chất trong đất"
        elif ph < 6.0 or ph > 7.5:
            chem_status = "CANH_BAO"
            chem_status_vi = "Cảnh báo"
            chem_note = "Đất có xu hướng chua phèn hoặc hơi kiềm"
        else:
            chem_status = "TOT"
            chem_status_vi = "Ổn định"
            chem_note = "pH lý tưởng (6.0 - 7.5) cho hầu hết cây trồng hấp thu khoáng"

        pillars.append({
            "key": "chemical_ph",
            "title": "Hóa tính (Độ pH)",
            "status": chem_status,
            "status_vi": chem_status_vi,
            "value_text": f"pH {ph:.2f}",
            "short_note": chem_note
        })

        # 3. Trụ cột Độ mặn (EC)
        if ec >= 2000.0:
            ec_status = "NGUY_HIEM"
            ec_status_vi = "Nguy hiểm"
            ec_note = "Đất nhiễm mặn nặng, nguy cơ ngộ độc ion & cháy rễ non"
        elif ec >= 1500.0:
            ec_status = "CANH_BAO"
            ec_status_vi = "Cảnh báo"
            ec_note = "Nồng độ muối khoáng hòa tan đang tăng cao"
        elif 0 < ec < 300.0:
            ec_status = "CANH_BAO"
            ec_status_vi = "Cảnh báo"
            ec_note = "Độ dẫn điện thấp, đất nghèo ion khoáng hòa tan"
        else:
            ec_status = "TOT"
            ec_status_vi = "Ổn định"
            ec_note = "Độ dẫn điện an toàn, cây hấp thu nước và dinh dưỡng thuận lợi"

        pillars.append({
            "key": "salinity_ec",
            "title": "Độ mặn (EC)",
            "status": ec_status,
            "status_vi": ec_status_vi,
            "value_text": f"{ec:.0f} µS/cm",
            "short_note": ec_note
        })

        # 4. Trụ cột Dinh dưỡng (NPK)
        if soil_health_code == "KEM" or (n + p + k) < 100.0 or (n < 40 and p < 10 and k < 50):
            npk_status = "NGUY_HIEM"
            npk_status_vi = "Nguy hiểm"
            npk_note = "Trữ lượng NPK cạn kiệt, suy thoái độ phì nhiêu"
        elif soil_health_code == "TRUNG_BINH" or (n < 60 or p < 15 or k < 70):
            npk_status = "CANH_BAO"
            npk_status_vi = "Cảnh báo"
            npk_note = "Dinh dưỡng ở mức trung bình, thiếu hụt nhẹ một số nguyên tố"
        else:
            npk_status = "TOT"
            npk_status_vi = "Ổn định"
            npk_note = "Dinh dưỡng NPK dồi dào, cân đối hài hòa"

        pillars.append({
            "key": "nutrition_npk",
            "title": "Dinh dưỡng (NPK)",
            "status": npk_status,
            "status_vi": npk_status_vi,
            "value_text": f"N:{n:.0f} • P:{p:.0f} • K:{k:.0f} mg/kg",
            "short_note": npk_note
        })

        return pillars

    def classify_soil_profile(
        self,
        moisture: float,
        ec: float,
        ph: float,
        n: float,
        p: float,
        k: float,
        soil_health_code: str,
    ) -> Dict[str, Any]:
        """
        Gợi ý nhóm đặc tính thổ nhưỡng trực tiếp từ cảm biến 7-in-1 (Cách 1).
        Đơn vị đồng bộ với evaluator.py: N, P, K (mg/kg), EC (µS/cm), moisture (%).
        """
        tags: List[str] = []
        warnings_list: List[str] = []

        # Cảnh báo độ tin cậy phép đo khi đất quá khô hoặc quá bão hòa nước
        if moisture < 15.0:
            warnings_list.append(
                f"Đất quá khô ({moisture:.1f}% < 15%), chỉ số EC và NPK dễ bị tụt ảo. "
                "Nên tưới ẩm nhẹ và chờ 5–10 phút rồi đo lại."
            )
        elif moisture > 85.0:
            warnings_list.append(
                f"Đất đang ngập úng ({moisture:.1f}% > 85%), nồng độ ion có thể bị pha loãng."
            )

        # Nhận diện các thuộc tính thành phần (đồng bộ ngưỡng với evaluate_pillars & diagnosis)
        is_very_acidic = ph < 5.2
        is_mild_acidic = 5.2 <= ph < 6.0
        is_alkaline_high = ph > 7.8
        is_alkaline_mild = 7.5 < ph <= 7.8
        is_saline = ec >= 2000.0
        is_high_salt = 1500.0 <= ec < 2000.0
        is_low_nutrient = (
            soil_health_code == "KEM"
            or (n < 50.0 and p < 15.0 and k < 60.0)
            or (0 < ec < 300.0 and (n + p + k) < 120.0)
        )
        is_optimal_ph = 6.0 <= ph <= 7.5

        if is_very_acidic:
            tags.append(f"Chua mạnh (pH {ph:.2f})")
        elif is_mild_acidic:
            tags.append(f"Chua nhẹ (pH {ph:.2f})")
        elif is_alkaline_high:
            tags.append(f"Kiềm mạnh (pH {ph:.2f})")
        elif is_alkaline_mild:
            tags.append(f"Hơi kiềm (pH {ph:.2f})")

        if is_saline:
            tags.append(f"Nhiễm mặn / Dư muối ({ec:.0f} µS/cm)")
        elif is_high_salt:
            tags.append(f"Tích tụ muối khoáng cao ({ec:.0f} µS/cm)")

        if is_low_nutrient:
            tags.append("Nghèo dinh dưỡng / Rửa trôi mạnh")
        if moisture < 25.0:
            tags.append("Khô hạn")
        elif moisture > 85.0:
            tags.append("Ngập úng")

        # Xếp loại nhóm đất chính theo thứ tự ưu tiên rủi ro nông học
        if is_very_acidic and is_saline:
            profile_code = "DAT_CHUA_MAN"
            profile_name = "Đất chua mặn / Nghi phèn mặn"
            common_match = "Thường gặp ở đất phù sa ven biển, đất nhiễm phèn mặn hoặc tích tụ muối lâu ngày"
        elif is_very_acidic and ec >= 1000.0:
            profile_code = "DAT_NGHI_PHEN"
            profile_name = "Đất chua mạnh – Nghi nhiễm phèn"
            common_match = "Thường gặp ở vùng đất trũng, đất phèn hoặc đất bón thừa phân đạm vô cơ"
        elif is_saline:
            profile_code = "DAT_NHIEM_MAN"
            profile_name = "Đất nhiễm mặn / Dư thừa muối khoáng"
            common_match = "Thường gặp ở vùng xâm nhập mặn hoặc đất nhà màng bón dư phân hóa học"
        elif is_very_acidic:
            profile_code = "DAT_CHUA_MANH"
            profile_name = "Đất chua mạnh"
            common_match = "Thường gặp ở đất đồi dốc bị rửa trôi hoặc đất đỏ bazan canh tác lâu năm"
        elif is_alkaline_high:
            profile_code = "DAT_KIEM_CAO"
            profile_name = "Đất kiềm mạnh / Giàu vôi"
            common_match = "Thường gặp ở vùng đất đá vôi, đất khô hạn hoặc bón quá tay vôi/tro bếp"
        elif is_mild_acidic and is_low_nutrient:
            profile_code = "DAT_BAC_MAU_CHUA"
            profile_name = "Đất chua nhẹ – Bạc màu"
            common_match = "Thường gặp ở đất xám bạc màu, đất pha cát hoặc đất đồi nghèo mùn"
        elif is_mild_acidic:
            profile_code = "DAT_CHUA_NHE"
            profile_name = "Đất chua nhẹ"
            common_match = "Phổ biến ở đất đỏ bazan, đất phù sa cổ (phù hợp cây ăn trái, cà phê, hồ tiêu)"
        elif is_alkaline_mild:
            profile_code = "DAT_HOI_KIEM"
            profile_name = "Đất hơi kiềm"
            common_match = "Thường gặp ở đất phù sa giàu khoáng kiềm hoặc vùng ít mưa"
        elif is_low_nutrient:
            profile_code = "DAT_BAC_MAU"
            profile_name = "Đất bạc màu / Nghèo dinh dưỡng"
            common_match = "Thường gặp ở đất pha cát, thoát nước nhanh hoặc đất canh tác lâu chưa bồi bổ"
        elif is_optimal_ph and (300.0 <= ec < 1500.0) and soil_health_code == "TOT":
            profile_code = "DAT_TRUNG_TINH_TOT"
            profile_name = "Đất trung tính – Giàu dinh dưỡng"
            common_match = "Tương đương nhóm đất thịt / đất phù sa màu mỡ, phù hợp đa số cây trồng"
        else:
            profile_code = "DAT_TRUNG_TINH_ON_DINH"
            profile_name = "Đất trung tính – Dinh dưỡng trung bình"
            common_match = "Đất canh tác phổ thông, chưa ghi nhận dấu hiệu chua phèn hay nhiễm mặn"

        return {
            "profile_code": profile_code,
            "profile_name": profile_name,
            "common_match": common_match,
            "tags": tags,
            "measurement_warnings": warnings_list,
        }

    def synthesize_diagnosis_and_action_plan(
        self,
        moisture: float,
        temperature: float,
        ec: float,
        ph: float,
        n: float,
        p: float,
        k: float,
        soil_health_code: str,
        health_score: float
    ) -> Dict[str, Any]:
        """
        Tầng Chẩn Đoán Tổng Hợp & Khử Mâu Thuẫn Triệt Để:
        - Xác định rủi ro trọng tâm (primary_risk, risk_level).
        - Ghi đè xung đột (ví dụ mặn nặng thì KHÔNG bảo tưới duy trì hay bón phân ngay).
        - Sinh tiêu đề thống nhất (overall_title), tóm tắt tổng thể (overall_summary).
        - Phác đồ hành động tuần tự (action_plan).
        - Điều kiện tiên quyết cho cây trồng (crop_prerequisite_note).
        """
        # =====================================================================
        # TRƯỜNG HỢP 1: ĐẤT MẶN NẶNG (EC >= 2000 uS/cm) - ƯU TIÊN SỐ 1 TUYỆT ĐỐI
        # =====================================================================
        if ec >= 2000.0:
            primary_risk = "Nhiễm mặn nặng – Nguy cơ ngộ độc muối & cháy rễ non"
            risk_level = "CRITICAL" if ec >= 2500.0 else "HIGH"
            overall_title = "Cảnh Báo: Đất Nhiễm Mặn Cao – Cần Ưu Tiên Rửa Mặn Khẩn Cấp"
            overall_summary = (
                f"Chỉ số độ dẫn điện EC tăng vọt lên {ec:.0f} µS/cm (vượt ngưỡng độc tính 2000 µS/cm), "
                f"tạo áp suất thẩm thấu ngược khiến rễ cây mất nước và đối mặt nguy cơ cháy rễ. "
                f"Mặc dù các chỉ số khác như độ ẩm ({moisture:.1f}%) hoặc dinh dưỡng NPK có thể đầy đủ, "
                f"TUYỆT ĐỐI KHÔNG bón thêm phân hóa học lúc này. Cần tập trung toàn lực tháo nước ngọt rửa mặn "
                f"và tiêu thoát nhanh trước khi thực hiện các bước canh tác tiếp theo."
            )
            crop_prerequisite_note = (
                f"⚠️ Điều kiện tiên quyết: Đất đang nhiễm mặn nghiêm trọng (EC = {ec:.0f} µS/cm). "
                f"BẮT BUỘC phải xả rửa mặn đưa EC về dưới 1500 µS/cm trước khi xuống giống các loại cây gợi ý dưới đây, "
                f"nếu không cây sẽ bị thối rễ và chết héo."
            )
            action_plan = [
                {
                    "step": 1,
                    "priority": "KHAN_CAP",
                    "priority_vi": "Khẩn cấp",
                    "title": "Rửa mặn bằng nước ngọt & Khơi thông mương rãnh",
                    "detail": (
                        f"Độ dẫn điện EC = {ec:.0f} µS/cm ở mức nguy hiểm. Dẫn nước ngọt xả tràn mặt liếp hoặc tưới đẫm "
                        f"nước ngọt liên tục trong 2–3 ngày, kết hợp vét mương tiêu thoát để rửa trôi muối natri ra khỏi tầng rễ."
                    )
                },
                {
                    "step": 2,
                    "priority": "KHAN_CAP",
                    "priority_vi": "Khẩn cấp",
                    "title": "Tạm ngưng toàn bộ phân vô cơ & khoáng tan nhanh",
                    "detail": (
                        "Tuyệt đối không bón thêm phân Urê, NPK, phân hóa học hay phân chuồng tươi. Phân bón tan nhanh sẽ càng "
                        "làm tăng nồng độ ion muối trong đất, gây ngộ độc cháy rễ ngay lập tức."
                    )
                },
                {
                    "step": 3,
                    "priority": "THEO_DOI",
                    "priority_vi": "Theo dõi",
                    "title": "Kiểm tra hạ chỉ số EC mục tiêu (< 1500 µS/cm)",
                    "detail": (
                        "Đo lại cảm biến sau các lần tưới rửa mặn. Chỉ thực hiện gieo trồng hoặc bón phân trở lại sau khi chỉ số "
                        "EC đã hạ xuống ổn định dưới ngưỡng 1500 µS/cm."
                    )
                },
                {
                    "step": 4,
                    "priority": "BOI_DUONG",
                    "priority_vi": "Bồi dưỡng",
                    "title": "Tái tạo sinh học bằng Axit Humic & Phân hữu cơ vi sinh",
                    "detail": (
                        "Sau khi xả mặn thành công, tưới bổ sung Axit Humic/Fulvic và phân hữu cơ vi sinh ủ hoai mục để giải độc đất, "
                        "tái thiết cấu trúc hạt đất và kích thích cây ra chồi rễ mới."
                    )
                }
            ]

        # =====================================================================
        # TRƯỜNG HỢP 2: ĐẤT CHUA PHÈN NẶNG (pH < 5.2)
        # =====================================================================
        elif ph < 5.2:
            primary_risk = "Đất chua phèn nặng – Cố định lân & khóa dinh dưỡng rễ cây"
            risk_level = "HIGH"
            overall_title = "Cảnh Báo: Đất Chua Phèn Nặng – Ưu Tiên Bón Vôi Khử Chua"
            overall_summary = (
                f"Độ chua đất đang ở mức báo động (pH = {ph:.2f} < 5.2), làm giải phóng độc tố nhôm/sắt tự do và ức chế rễ. "
                f"Ở mức pH này, rễ cây bị nghẹt không thể hấp thụ được phân bón NPK (lân bị cố định hoàn toàn). "
                f"Cần tập trung bón vôi nông nghiệp nâng pH lên trên 6.0 trước khi bón thúc dinh dưỡng."
            )
            crop_prerequisite_note = (
                f"⚠️ Điều kiện tiên quyết: Đất bị chua phèn (pH = {ph:.2f}). "
                f"Cần bón vôi nông nghiệp nâng pH lên tối thiểu 5.8 - 6.5 trước khi xuống giống để cây trồng hấp thu được khoáng chất."
            )
            action_plan = [
                {
                    "step": 1,
                    "priority": "KHAN_CAP",
                    "priority_vi": "Khẩn cấp",
                    "title": "Bón vôi bột nông nghiệp khử chua",
                    "detail": (
                        f"Rải đều vôi nông nghiệp CaCO3 (250–350 kg/1000m²) hoặc Dolomite khi đất có độ ẩm vừa phải để nâng pH "
                        f"từ {ph:.2f} lên dải an toàn 6.0 – 6.5."
                    )
                },
                {
                    "step": 2,
                    "priority": "THEO_DOI",
                    "priority_vi": "Theo dõi",
                    "title": "Tưới nước thẩm thấu & Kiểm tra pH sau 7 ngày",
                    "detail": (
                        "Tưới nhẹ giữ ẩm để vôi hòa tan và ngấm đều vào tầng canh tác. Giám sát chỉ số pH tăng dần trước khi bón thúc phân."
                    )
                },
                {
                    "step": 3,
                    "priority": "BOI_DUONG",
                    "priority_vi": "Bồi dưỡng",
                    "title": "Bổ sung Lân nung chảy & Phân hữu cơ hoai mục",
                    "detail": (
                        "Khi pH đã ổn định, sử dụng lân nung chảy (ít bị cố định trong đất phèn) kết hợp phân hữu cơ vi sinh để bồi dưỡng hệ đệm thổ nhưỡng."
                    )
                }
            ]

        # =====================================================================
        # TRƯỜNG HỢP 3: ĐẤT KIỀM CAO (pH > 7.8)
        # =====================================================================
        elif ph > 7.8:
            primary_risk = "Đất kiềm hóa cao – Kết tủa vi lượng & cản trở sinh trưởng"
            risk_level = "HIGH"
            overall_title = "Cảnh Báo: Đất Kiềm Hóa Cao – Cần Hạ Độ Kiềm Thổ Nhưỡng"
            overall_summary = (
                f"Độ pH đất đạt {ph:.2f} thuộc nhóm đất kiềm mạnh, gây kết tủa các khoáng vi lượng thiết yếu (Sắt, Kẽm, Mangan). "
                f"Tuyệt đối không bón thêm vôi hay tro trấu. Cần sử dụng phân bón gốc axit hóa và phân hữu cơ để kéo giảm pH về dải cân bằng."
            )
            crop_prerequisite_note = (
                f"⚠️ Điều kiện tiên quyết: pH đất kiềm cao ({ph:.2f}). "
                f"Cần bổ sung vi lượng chelate và hạ độ kiềm trước khi trồng các loại cây mẫn cảm."
            )
            action_plan = [
                {
                    "step": 1,
                    "priority": "KHAN_CAP",
                    "priority_vi": "Khẩn cấp",
                    "title": "Hạ độ kiềm bằng phân bón gốc Axit & Hữu cơ",
                    "detail": (
                        "Sử dụng phân SA (Ammoni Sunfat) hoặc MAP kết hợp tưới phân hữu cơ sinh học để trung hòa môi trường kiềm."
                    )
                },
                {
                    "step": 2,
                    "priority": "BOI_DUONG",
                    "priority_vi": "Bồi dưỡng",
                    "title": "Phun bổ sung vi lượng dạng Chelate qua lá",
                    "detail": (
                        "Vì rễ khó hút vi lượng trong đất kiềm, phun vi lượng tổng hợp dạng Chelate qua tán lá để chống vàng lá gân xanh cho cây."
                    )
                },
                {
                    "step": 3,
                    "priority": "THEO_DOI",
                    "priority_vi": "Theo dõi",
                    "title": "Kiểm soát nguồn nước tưới",
                    "detail": (
                        "Kiểm tra nguồn nước tưới giếng khoan xem có bị nhiễm vôi/nước cứng hay không để có biện pháp lắng lọc."
                    )
                }
            ]

        # =====================================================================
        # TRƯỜNG HỢP 4: ĐẤT KHÔ HẠN (Moisture < 25.0%)
        # =====================================================================
        elif moisture < 25.0:
            primary_risk = "Khô hạn nghiêm trọng – Thiếu nước hòa tan dinh dưỡng"
            risk_level = "HIGH"
            overall_title = "Cảnh Báo: Đất Khô Hạn Nặng – Cần Tưới Cấp Nước Khẩn Cấp"
            overall_summary = (
                f"Độ ẩm đất tụt xuống chỉ còn {moisture:.1f}%, đất kiệt nước làm tê liệt hoạt động rễ tơ và vi sinh vật. "
                f"Dù có dinh dưỡng trong đất nhưng cây không thể hòa tan hấp thụ được. "
                f"Cần kích hoạt ngay hệ thống tưới nước giữ ẩm trước khi bón bất kỳ phân khoáng nào để tránh xót rễ."
            )
            crop_prerequisite_note = (
                f"⚠️ Điều kiện tiên quyết: Độ ẩm đất quá thấp ({moisture:.1f}%). "
                f"Cần tưới đẫm đất đạt độ ẩm từ 45% trở lên trước khi xuống giống."
            )
            action_plan = [
                {
                    "step": 1,
                    "priority": "KHAN_CAP",
                    "priority_vi": "Khẩn cấp",
                    "title": "Kích hoạt hệ thống tưới nhỏ giọt / phun sương",
                    "detail": (
                        f"Độ ẩm hiện tại {moisture:.1f}%. Cần bật hệ thống tưới chia làm nhiều đợt nhỏ trong ngày để nước ngấm sâu "
                        f"xuống tầng đất canh tác 20–30 cm."
                    )
                },
                {
                    "step": 2,
                    "priority": "THEO_DOI",
                    "priority_vi": "Theo dõi",
                    "title": "Phủ bổi rơm rạ giữ ẩm bề mặt luống",
                    "detail": (
                        "Tận dụng rơm rạ mục, cỏ khô hoặc màng phủ để che phủ quanh gốc nhằm giảm bốc thoát hơi nước do nhiệt độ cao."
                    )
                },
                {
                    "step": 3,
                    "priority": "BOI_DUONG",
                    "priority_vi": "Bồi dưỡng",
                    "title": "Bón phân hòa tan sau khi đất đã đủ ẩm",
                    "detail": (
                        "Chỉ bón thúc phân khoáng khi đất đã đạt độ ẩm trên 40%, hòa loãng phân tưới đều quanh tán rễ."
                    )
                }
            ]

        # =====================================================================
        # TRƯỜNG HỢP 5: ĐẤT NGẬP ÚNG (Moisture > 85.0%)
        # =====================================================================
        elif moisture > 85.0:
            primary_risk = "Ngập úng quá bão hòa – Nguy cơ ngạt rễ & nấm bệnh gốc"
            risk_level = "HIGH"
            overall_title = "Cảnh Báo: Đất Quá Ẩm / Ngập Úng – Ưu Tiên Thoát Nước"
            overall_summary = (
                f"Độ ẩm đất đạt {moisture:.1f}% ở trạng thái bão hòa nước, đẩy hết không khí ra khỏi mao quản đất khiến rễ bị ngạt oxy. "
                f"Nguy cơ bùng phát nấm Phytophthora gây thối rễ vàng lá. Cần ngưng tưới và khơi thông thoát nước ngay."
            )
            crop_prerequisite_note = (
                "⚠️ Điều kiện tiên quyết: Đất đang thừa nước/úng rễ. Cần tiêu thoát nước tốt trước khi gieo trồng."
            )
            action_plan = [
                {
                    "step": 1,
                    "priority": "KHAN_CAP",
                    "priority_vi": "Khẩn cấp",
                    "title": "Ngưng tưới hoàn toàn & Khơi thông mương rãnh",
                    "detail": (
                        "Tạm dừng toàn bộ lịch tưới. Nạo vét rãnh thoát nước giữa các luống để hạ mực nước ngầm nhanh nhất."
                    )
                },
                {
                    "step": 2,
                    "priority": "THEO_DOI",
                    "priority_vi": "Theo dõi",
                    "title": "Phá váng mặt luống sau khi nước rút",
                    "detail": (
                        "Xới nhẹ phá lớp váng bùn trên bề mặt để đất thông thoáng, cung cấp lại oxy cho bộ rễ thở."
                    )
                },
                {
                    "step": 3,
                    "priority": "BOI_DUONG",
                    "priority_vi": "Bồi dưỡng",
                    "title": "Tưới chế phẩm sinh học Trichoderma ngừa nấm rễ",
                    "detail": (
                        "Bổ sung nấm đối kháng Trichoderma tưới quanh vùng rễ để phòng trừ các loại nấm gây thối cổ rễ."
                    )
                }
            ]

        # =====================================================================
        # TRƯỜNG HỢP 6: ĐẤT NGHÈO DINH DƯỠNG NPK (Model A = KEM hoặc NPK thấp)
        # =====================================================================
        elif soil_health_code == "KEM" or (n + p + k) < 100.0 or (n < 50 and p < 15 and k < 60):
            primary_risk = "Đất suy thoái dinh dưỡng đa lượng NPK"
            risk_level = "MEDIUM"
            overall_title = "Đất Nghèo Dinh Dưỡng – Cần Kế Hoạch Cải Tạo & Bón Phân Toàn Diện"
            overall_summary = (
                f"Môi trường vật lý và độ chua ở mức an toàn (ẩm {moisture:.1f}%, pH {ph:.1f}), nhưng hàm lượng N-P-K "
                f"({n:.0f}-{p:.0f}-{k:.0f} mg/kg) bị thiếu hụt nghiêm trọng theo đánh giá của mô hình XGBoost. "
                f"Cần bón lót phân chuồng hoai mục kết hợp bổ sung phân NPK cân đối theo từng chu kỳ phát triển."
            )
            crop_prerequisite_note = (
                "💡 Khuyến nghị: Đất đang thiếu hụt NPK. Nên bón lót phân lân và phân hữu cơ trước khi xuống giống."
            )
            action_plan = [
                {
                    "step": 1,
                    "priority": "KHAN_CAP",
                    "priority_vi": "Khẩn cấp",
                    "title": "Bón lót phân chuồng ủ hoai & Phân vi sinh",
                    "detail": (
                        "Bón 1–2 tấn phân chuồng hoai mục/1000m² để làm giàu hàm lượng mùn hữu cơ và tăng khả năng giữ dinh dưỡng của đất."
                    )
                },
                {
                    "step": 2,
                    "priority": "BOI_DUONG",
                    "priority_vi": "Bồi dưỡng",
                    "title": f"Bổ sung phân khoáng đa lượng NPK ({n:.0f}-{p:.0f}-{k:.0f})",
                    "detail": (
                        "Bổ sung phân NPK có tỷ lệ cân đối phù hợp với từng giai đoạn (kích rễ non bằng Lân, phát triển thân lá bằng Đạm)."
                    )
                },
                {
                    "step": 3,
                    "priority": "THEO_DOI",
                    "priority_vi": "Theo dõi",
                    "title": "Kiểm tra hấp thu qua chỉ số EC",
                    "detail": (
                        "Sau khi bón phân, theo dõi sự tăng nhẹ của EC (khoảng 800–1200 µS/cm) chứng tỏ phân bón đã hòa tan tốt."
                    )
                }
            ]

        # =====================================================================
        # TRƯỜNG HỢP 7: ĐẤT TRUNG BÌNH (Cần bón dặm nhẹ)
        # =====================================================================
        elif soil_health_code == "TRUNG_BINH" or health_score < 75.0:
            primary_risk = "Dinh dưỡng trung bình – Cần bón dặm cân đối"
            risk_level = "LOW"
            overall_title = "Thổ Nhưỡng Ổn Định – Cần Bổ Sung Cân Đối Dinh Dưỡng"
            overall_summary = (
                f"Chất lượng đất nhìn chung ở mức ổn định (Ẩm độ {moisture:.1f}%, pH {ph:.2f}, EC {ec:.0f} µS/cm). "
                f"Môi trường đất thích hợp cho cây trồng sinh trưởng, chỉ cần bón thúc nhẹ theo định kỳ "
                f"để duy trì mức dinh dưỡng lý tưởng cho mùa vụ."
            )
            crop_prerequisite_note = None
            action_plan = [
                {
                    "step": 1,
                    "priority": "THEO_DOI",
                    "priority_vi": "Theo dõi",
                    "title": "Duy trì chế độ tưới tiêu hiện tại",
                    "detail": (
                        f"Độ ẩm đất ({moisture:.1f}%) và nhiệt độ ({temperature:.1f}°C) đang trong dải thuận lợi. "
                        f"Tiếp tục tưới định kỳ theo nhu cầu nước của cây trồng."
                    )
                },
                {
                    "step": 2,
                    "priority": "BOI_DUONG",
                    "priority_vi": "Bồi dưỡng",
                    "title": "Bón thúc dinh dưỡng bổ sung",
                    "detail": (
                        f"Hàm lượng dinh dưỡng hiện tại (N:{n:.0f}, P:{p:.0f}, K:{k:.0f} mg/kg). Bón thúc nhẹ bằng phân NPK "
                        f"kết hợp tưới phân hữu cơ amino acid để tăng chất lượng nông sản."
                    )
                },
                {
                    "step": 3,
                    "priority": "THEO_DOI",
                    "priority_vi": "Theo dõi",
                    "title": "Giám sát định kỳ trạng thái đất",
                    "detail": "Theo dõi các chỉ số biến động qua bảng điều khiển thời gian thực để can thiệp kịp thời."
                }
            ]

        # =====================================================================
        # TRƯỜNG HỢP 8: ĐẤT RẤT TỐT (Tối ưu toàn diện)
        # =====================================================================
        else:
            primary_risk = "Không có rủi ro (Thổ nhưỡng đạt chuẩn lý tưởng)"
            risk_level = "LOW"
            overall_title = "Thổ Nhưỡng Rất Tốt – Dải Sinh Trưởng Đạt Chuẩn Xuất Sắc"
            overall_summary = (
                f"Môi trường đất đạt chất lượng rất tốt với sự hài hòa tuyệt đối giữa độ ẩm ({moisture:.1f}%), "
                f"độ chua lý tưởng (pH {ph:.2f}) và độ dẫn điện an toàn ({ec:.0f} µS/cm). Dinh dưỡng NPK dồi dào, "
                f"bộ rễ sẽ phát triển mạnh mẽ và cho năng suất cây trồng tối ưu."
            )
            crop_prerequisite_note = None
            action_plan = [
                {
                    "step": 1,
                    "priority": "THEO_DOI",
                    "priority_vi": "Theo dõi",
                    "title": "Duy trì chế độ canh tác & tưới tiêu tối ưu",
                    "detail": (
                        f"Các chỉ số độ ẩm ({moisture:.1f}%) và EC ({ec:.0f} µS/cm) đều rất chuẩn. "
                        f"Duy trì quy trình tưới tiêu nhỏ giọt tự động hiện hành."
                    )
                },
                {
                    "step": 2,
                    "priority": "BOI_DUONG",
                    "priority_vi": "Bồi dưỡng",
                    "title": "Bổ sung định kỳ phân hữu cơ sinh học duy trì độ phì",
                    "detail": (
                        "Bón dặm phân trùn quế hoặc phân hữu cơ vi sinh định kỳ để giữ gìn tầng mùn và hệ sinh thái đất màu mỡ lâu dài."
                    )
                },
                {
                    "step": 3,
                    "priority": "THEO_DOI",
                    "priority_vi": "Theo dõi",
                    "title": "Tự tin triển khai các giống cây trồng năng suất cao",
                    "detail": "Đất đã sẵn sàng cho các nhóm cây trồng khuyến nghị đạt hiệu quả kinh tế cao nhất."
                }
            ]

        # Ánh xạ action_plan sang định dạng recommendations cũ để tương thích ngược 100%
        legacy_recs = []
        for step in action_plan:
            category_name = (
                "Xử lý khẩn cấp" if step["priority"] == "KHAN_CAP"
                else ("Canh tác" if step["priority"] == "THEO_DOI" else "Bồi dưỡng")
            )
            legacy_recs.append({
                "category": category_name,
                "priority": "HIGH" if step["priority"] == "KHAN_CAP" else ("MEDIUM" if step["priority"] == "THEO_DOI" else "LOW"),
                "action": step["title"],
                "details": step["detail"]
            })

        return {
            "primary_risk": primary_risk,
            "risk_level": risk_level,
            "overall_title": overall_title,
            "overall_summary": overall_summary,
            "crop_prerequisite_note": crop_prerequisite_note,
            "action_plan": action_plan,
            "legacy_recommendations": legacy_recs
        }

    def evaluate(
        self,
        moisture: float,
        temperature: float,
        ec: float,
        ph: float,
        n: float,
        p: float,
        k: float,
        humidity: Optional[float] = None,
        rainfall: Optional[float] = None,
        analysis_meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Quy trình đánh giá toàn diện:
        1. Lớp 0: Lọc lỗi phần cứng RS485
        2. Quy đổi đơn vị cảm biến sang chuẩn Model A & chạy Isolation Forest
        3. Model A: Phân loại sức khỏe đất, tính Soil Health Score (0-100) & TreeSHAP
        4. Model B: Gợi ý Top 3 cây trồng thích hợp nhất kèm điều kiện tiên quyết
        5. Đánh giá 4 trụ cột thổ nhưỡng & Phân loại nhóm đặc tính đất (Soil Profile)
        6. Chẩn đoán tổng hợp & Khử mâu thuẫn triệt để -> Sinh phác đồ hành động tuần tự
        """
        # 1. Lớp 0: Kiểm tra lỗi cảm biến
        hw_err = self.check_hardware_error(
            moisture=moisture,
            temperature=temperature,
            ec=ec,
            ph=ph,
            n=n,
            p=p,
            k=k
        )
        if hw_err is not None:
            return hw_err

        clean_meta = analysis_meta or {
            "sample_count": 1,
            "analyzed_at": datetime.now().isoformat(),
            "aggregation": "direct"
        }

        result: Dict[str, Any] = {
            "is_hardware_error": False,
            "status": "SUCCESS",
            "analysis_meta": clean_meta,
            "telemetry_clean": {
                "moisture": moisture,
                "temperature": temperature,
                "ec": ec,
                "ph": ph,
                "n": n,
                "p": p,
                "k": k,
            }
        }

        # Quy đổi đơn vị sang thang đo huấn luyện của Model A / Isolation Forest (NPK: kg/ha, EC: µS/cm)
        n_model_a, p_model_a, k_model_a, ec_model_a = self._convert_units_for_model_a(
            n=n, p=p, k=k, ec=ec
        )

        # 2. Kiểm tra dị thường (Isolation Forest)
        is_anomaly = False
        anomaly_score = 0.0
        if self.iforest is not None:
            try:
                raw_a = np.array([[n_model_a, p_model_a, k_model_a, ph, ec_model_a]], dtype=np.float32)
                pred = self.iforest.predict(raw_a)[0]
                is_anomaly = bool(pred == -1)
                if hasattr(self.iforest, "score_samples"):
                    anomaly_score = float(self.iforest.score_samples(raw_a)[0])
            except Exception as e:
                logger.warning("Lỗi chạy Isolation Forest: %s", e)

        result["anomaly_detection"] = {
            "is_anomaly": is_anomaly,
            "anomaly_score": round(anomaly_score, 4),
            "note": "Cảnh báo bất thường tổ hợp chỉ số đất" if is_anomaly else "Chỉ số tương quan ổn định"
        }

        # 3. Model A: XGBoost Soil Health
        soil_health_code = "TRUNG_BINH"
        soil_health_vi = "Đất trung bình – Cần bổ sung cân đối"
        health_score = 50.0
        top_shap_factors: List[Dict[str, Any]] = []

        X_a = self._engineer_features_model_a(
            n=n_model_a, p=p_model_a, k=k_model_a, ph=ph, ec=ec_model_a
        )

        if self.model_a is not None:
            try:
                probs_a = self.model_a.predict_proba(X_a)[0]
                classes_a = list(self.model_a.classes_)
                pred_idx = int(np.argmax(probs_a))

                if self.le_a is not None:
                    raw_cls = classes_a[pred_idx]
                    soil_health_code = str(self.le_a.inverse_transform([raw_cls])[0])
                else:
                    soil_health_code = str(classes_a[pred_idx])

                labels_vi = self.meta_a.get("label_vi", {})
                soil_health_vi = labels_vi.get(soil_health_code, soil_health_code)

                class_weights: Dict[str, float] = {"TOT": 100.0, "TRUNG_BINH": 60.0, "KEM": 20.0}
                weighted_sum = 0.0
                for c_idx, c_name in enumerate(classes_a):
                    decoded_name = str(self.le_a.inverse_transform([c_name])[0]) if self.le_a else str(c_name)
                    w = class_weights.get(decoded_name, 50.0)
                    weighted_sum += probs_a[c_idx] * w

                # Hiệu chỉnh điểm theo các giới hạn vật lý khắc nghiệt (đơn vị cảm biến gốc)
                if ph < 5.0 or ph > 8.0:
                    weighted_sum -= 15.0
                if ec >= 2000.0:
                    weighted_sum -= 25.0
                if moisture < 25.0 or moisture > 85.0:
                    weighted_sum -= 15.0
                if (n + p + k) < 100.0:
                    weighted_sum -= 15.0

                health_score = round(float(np.clip(weighted_sum, 0.0, 100.0)), 1)
                top_shap_factors = self._explain_with_shap(X_a, pred_idx)
            except Exception as e:
                logger.error("Lỗi chạy Model A: %s", e)
        else:
            # Fallback tính điểm luật nếu chưa nạp Model A
            base_score = 80.0
            if ph < 5.5 or ph > 7.5:
                base_score -= 20.0
            if ec >= 2000.0:
                base_score -= 35.0
            elif ec >= 1500.0:
                base_score -= 15.0
            if moisture < 35.0 or moisture > 75.0:
                base_score -= 15.0
            if n < 50.0 or p < 15.0 or k < 60.0:
                base_score -= 15.0
            if (n + p + k) < 100.0:
                base_score -= 15.0
            health_score = round(float(np.clip(base_score, 10.0, 95.0)), 1)
            soil_health_code = "TOT" if health_score >= 75 else ("TRUNG_BINH" if health_score >= 45 else "KEM")
            labels_vi = self.meta_a.get("label_vi", {
                "KEM": "Đất kém dinh dưỡng – Cần cải tạo",
                "TRUNG_BINH": "Đất trung bình – Cần bổ sung cân đối",
                "TOT": "Đất phì nhiêu tốt"
            })
            soil_health_vi = labels_vi.get(soil_health_code, soil_health_code)

        # Đảm bảo top_shap_factors LUÔN có danh sách giải thích trực quan (TreeSHAP hoặc Agronomic Impact)
        if not top_shap_factors:
            top_shap_factors = self._compute_influencing_factors(
                n=n, p=p, k=k, ph=ph, ec=ec, moisture=moisture, temperature=temperature
            )

        result["soil_health"] = {
            "code": soil_health_code,
            "label_vi": soil_health_vi,
            "health_score": health_score,
            "top_influencing_factors": top_shap_factors,
            "shap_top_factors": top_shap_factors  # Alias cho tương thích
        }
        result["shap_top_factors"] = top_shap_factors  # Alias ở root level cho frontend truy cập trực tiếp

        # 4. Model B: Random Forest Crop Recommendation
        eff_humidity = humidity if humidity is not None else float(moisture)
        eff_rainfall = rainfall if rainfall is not None else float(max(50.0, min(300.0, moisture * 3.5)))

        top_crops: List[Dict[str, Any]] = []
        if self.model_b is not None:
            try:
                X_b = self._engineer_features_model_b(
                    n=n, p=p, k=k,
                    temperature=temperature,
                    humidity=eff_humidity,
                    ph=ph,
                    rainfall=eff_rainfall
                )
                probs_b = self.model_b.predict_proba(X_b)[0]
                top3_indices = np.argsort(probs_b)[::-1][:3]
                crop_vi_dict: Dict[str, str] = self.meta_b.get("crop_name_vi", {})

                for idx in top3_indices:
                    prob = float(probs_b[idx])
                    if prob <= 0.001 and len(top_crops) >= 1:
                        continue
                    if self.le_b is not None:
                        crop_en = str(self.le_b.inverse_transform([idx])[0])
                    else:
                        crop_en = str(self.model_b.classes_[idx])
                    crop_vi = crop_vi_dict.get(crop_en, crop_en)
                    top_crops.append({
                        "crop_en": crop_en,
                        "crop_vi": crop_vi,
                        "probability": round(prob, 4),
                        "confidence_percent": round(prob * 100.0, 1)
                    })
            except Exception as e:
                logger.error("Lỗi chạy Model B: %s", e)

        result["crop_recommendations"] = top_crops

        # 5. Đánh giá 4 trụ cột thổ nhưỡng
        pillars = self.evaluate_pillars(
            moisture=moisture,
            temperature=temperature,
            ec=ec,
            ph=ph,
            n=n,
            p=p,
            k=k,
            soil_health_code=soil_health_code
        )
        result["pillars"] = pillars

        # 5b. Gợi ý nhóm đặc tính đất (Soil Profile)
        soil_profile = self.classify_soil_profile(
            moisture=moisture,
            ec=ec,
            ph=ph,
            n=n,
            p=p,
            k=k,
            soil_health_code=soil_health_code,
        )
        result["soil_profile"] = soil_profile

        # 6. Tầng Chẩn Đoán Tổng Hợp & Khử Mâu Thuẫn Triệt Để
        diagnosis = self.synthesize_diagnosis_and_action_plan(
            moisture=moisture,
            temperature=temperature,
            ec=ec,
            ph=ph,
            n=n,
            p=p,
            k=k,
            soil_health_code=soil_health_code,
            health_score=health_score
        )

        result["primary_risk"] = diagnosis["primary_risk"]
        result["risk_level"] = diagnosis["risk_level"]
        result["overall_title"] = diagnosis["overall_title"]
        result["overall_summary"] = diagnosis["overall_summary"]
        result["crop_prerequisite_note"] = diagnosis["crop_prerequisite_note"]
        result["action_plan"] = diagnosis["action_plan"]
        result["recommendations"] = diagnosis["legacy_recommendations"]

        return result