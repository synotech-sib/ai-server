# modules/reporter.py 부분 수정 (generate_expert_report 함수 내)
# ... 중략 ...
    # Section I. Executive Summary 수정
    pdf.multi_cell(0, 7, txt=(
        f"The proposed design yields an areal capacity of {res['areal_capacity']} mAh/cm2. "
        f"The calculated material-level specific energy is {res['specific_energy']} Wh/kg "
        f"(based on {3.2}V nominal voltage). This design is optimized for high-power SIB applications."
    ))
# ... 후략 ...