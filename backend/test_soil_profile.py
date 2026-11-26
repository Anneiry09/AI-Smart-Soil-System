"""
Kiểm thử nhanh tính năng Phân loại nhóm đặc tính đất (soil_profile)
và quy đổi đơn vị đầu vào cho Model A / Isolation Forest.

Cách chạy:
    python test_soil_profile.py
"""

import os
import sys
import warnings

warnings.filterwarnings("ignore")

BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

import numpy as np

from app.modules.soil_ai.evaluator import SoilAIEvaluator

PROFILE_KEYS = {"profile_code", "profile_name", "common_match", "tags", "measurement_warnings"}
GOOD_PROFILES = {"DAT_TRUNG_TINH_TOT", "DAT_TRUNG_TINH_ON_DINH"}

CASES = [
    {
        "name": "Đất mặn nặng",
        "input": dict(ec=2400.0, ph=6.5, moisture=50.0, n=60.0, p=20.0, k=80.0),
        "expect": {"DAT_NHIEM_MAN"},
        "expect_warning": False,
    },
    {
        "name": "Đất chua nghi phèn",
        "input": dict(ec=1200.0, ph=4.7, moisture=55.0, n=45.0, p=12.0, k=55.0),
        "expect": {"DAT_NGHI_PHEN"},
        "expect_warning": False,
    },
    {
        "name": "Đất khô dưới 15%",
        "input": dict(ec=180.0, ph=5.6, moisture=12.0, n=30.0, p=8.0, k=40.0),
        "expect": {"DAT_BAC_MAU_CHUA"},
        "expect_warning": True,
    },
    {
        "name": "Đất kiềm cao",
        "input": dict(ec=700.0, ph=8.1, moisture=45.0, n=70.0, p=22.0, k=90.0),
        "expect": {"DAT_KIEM_CAO"},
        "expect_warning": False,
    },
    {
        "name": "Đất trung tính tốt",
        "input": dict(ec=650.0, ph=6.6, moisture=55.0, n=120.0, p=35.0, k=160.0),
        # TOT -> DAT_TRUNG_TINH_TOT; nếu Model A chấm TRUNG_BINH thì là DAT_TRUNG_TINH_ON_DINH
        "expect": GOOD_PROFILES,
        "expect_warning": False,
    },
]


def check_unit_conversion(evaluator: SoilAIEvaluator) -> None:
    n_a, p_a, k_a, ec_a = evaluator._convert_units_for_model_a(n=100.0, p=20.0, k=50.0, ec=650.0)
    assert abs(n_a - 224.0) < 1e-6 and abs(p_a - 44.8) < 1e-6 and abs(k_a - 112.0) < 1e-6, "Sai hệ số NPK -> kg/ha"
    assert abs(ec_a - 650.0) < 1e-6, "EC phải giữ nguyên µS/cm (Model A v1.0 train theo µS/cm)"
    print("[OK] Quy đổi đơn vị Model A: N/P/K x2.24 (kg/ha), EC giữ nguyên µS/cm")


def run() -> None:
    evaluator = SoilAIEvaluator.get_instance()
    print(f"Model A: {'đã nạp' if evaluator.model_a is not None else 'chưa nạp (dùng luật dự phòng)'} | "
          f"Isolation Forest: {'đã nạp' if evaluator.iforest is not None else 'chưa nạp'}")
    check_unit_conversion(evaluator)
    print("-" * 78)

    failures = []
    for i, case in enumerate(CASES, 1):
        inp = case["input"]
        res = evaluator.evaluate(temperature=28.0, **inp)
        profile = res.get("soil_profile")
        health = res.get("soil_health", {})
        anomaly = res.get("anomaly_detection", {})

        print(f"[{i}] {case['name']}  (EC={inp['ec']:.0f}, pH={inp['ph']}, Ẩm={inp['moisture']}%, "
              f"NPK={inp['n']:.0f}-{inp['p']:.0f}-{inp['k']:.0f})")
        print(f"    soil_profile : {profile.get('profile_code') if profile else None} – "
              f"{profile.get('profile_name') if profile else None}")
        if profile:
            print(f"    tags         : {profile['tags']}")
            print(f"    warnings     : {profile['measurement_warnings']}")
        print(f"    soil_health  : {health.get('code')} | score={health.get('health_score')}")
        print(f"    anomaly      : is_anomaly={anomaly.get('is_anomaly')} | score={anomaly.get('anomaly_score')}")

        if not profile or set(profile.keys()) != PROFILE_KEYS:
            failures.append(f"Ca {i}: soil_profile thiếu hoặc sai khóa")
            continue
        if profile["profile_code"] not in case["expect"]:
            failures.append(f"Ca {i}: profile_code={profile['profile_code']} không thuộc {case['expect']}")
        if case["expect_warning"] != bool(profile["measurement_warnings"]):
            failures.append(f"Ca {i}: measurement_warnings không đúng kỳ vọng")
        if "anomaly_detection" not in res or "soil_health" not in res:
            failures.append(f"Ca {i}: thiếu anomaly_detection hoặc soil_health")

    # So sánh nhanh: EC đúng thang µS/cm vs. EC bị chia 1000 (lỗi cũ) với Isolation Forest
    if evaluator.iforest is not None:
        good = CASES[4]["input"]
        base = [good["n"] * 2.24, good["p"] * 2.24, good["k"] * 2.24, good["ph"]]
        s_new = float(evaluator.iforest.score_samples(np.array([base + [good["ec"]]], dtype=np.float32))[0])
        s_old = float(evaluator.iforest.score_samples(np.array([base + [good["ec"] / 1000.0]], dtype=np.float32))[0])
        print("-" * 78)
        print(f"Isolation Forest (đất trung tính tốt): EC µS/cm -> score {s_new:.4f} | "
              f"EC chia 1000 (lỗi cũ) -> score {s_old:.4f}  (càng thấp càng bất thường)")

    print("-" * 78)
    if failures:
        for f in failures:
            print("[FAIL]", f)
        raise SystemExit(1)
    print("TẤT CẢ 5 CA KIỂM THỬ SOIL PROFILE ĐỀU ĐẠT (PASS)")


if __name__ == "__main__":
    run()
