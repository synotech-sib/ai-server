import streamlit as st
import pandas as pd
import numpy as np
import time
import os

# --- [1. 외부 데이터 로드 엔진: XLSX & CSV 모두 지원] ---
def load_external_data():
    # 폴더 내 파일 리스트 확인
    files = os.listdir('.')
    
    # 1.1. 소재 리스트 로드 (material_list)
    mat_df = None
    if 'material_list.xlsx' in files:
        mat_df = pd.read_excel('material_list.xlsx')
    elif 'material_list.csv' in files:
        mat_df = pd.read_csv('material_list.csv')
    else:
        # [cite_start]파일이 없을 경우 기본값 (알트리스 실측 데이터 기준) [cite: 124, 213, 1226]
        mat_df = pd.DataFrame({
            'Category': ['Cathode', 'Cathode', 'Cathode', 'Anode', 'Anode', 'Electrolyte', 'Separator'],
            'Name': ['프러시안 화이트 (PW)', '층상산화물 (LO)', '폴리음이온 (PA)', '쿠라레 A', '애경케미칼 D', 'G Type', 'PE'],
            'Base_Capacity': [162.0, 135.0, 110.0, 340.0, 310.0, 1.0, 1.0]
        })

    # 1.2. 공정 설정 로드 (param_config)
    config_df = None
    if 'param_config.xlsx' in files:
        config_df = pd.read_excel('param_config.xlsx').set_index('Parameter')
    elif 'param_config.csv' in files:
        config_df = pd.read_csv('param_config.csv').set_index('Parameter')
        
    return mat_df, config_df

mat_df, config_df = load_external_data()

# --- [2. 시스템 상태 관리] ---
if 'history' not in st.session_state: st.session_state.history = []
if 'is_pro' not in st.session_state: st.session_state.is_pro = False
IP_MARK = "IP by Synotech"

st.set_page_config(page_title=f"SynoCore | {IP_MARK}", layout="wide")

# --- [3. 전문 디자인 및 오류 수정 (f-string CSS)] ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #ffffff; }}
    .report-container {{ border: 2px solid #1A729A; padding: 40px; border-radius: 20px; background-color: #ffffff; margin-top: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
    .report-header {{ border-bottom: 3px double #1A729A; padding-bottom: 15px; margin-bottom: 25px; text-align: center; }}
    .stat-card {{ background-color: #f1f6f9; border-top: 5px solid #1A729A; padding: 20px; border-radius: 10px; text-align: center; }}
    /* 고스트 슬라이더 스타일 */
    div[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] + div > div {{
        color: #1A729A !important; font-weight: 800; font-size: 1.1rem !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- [4. 사이드바: 이메일 로그인 및 다국어] ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #1A729A;'>SynoCore</h1>", unsafe_allow_html=True)
    st.caption(f"Status: {IP_MARK}")
    
    st.divider()
    st.subheader("🔐 Professional Login")
    # [수정] 이메일 형식 및 placeholder 적용
    u_email = st.text_input("ID", placeholder="company email")
    u_pw = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if u_email == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
            st.session_state.is_pro = True
            st.success(f"Authorized: {u_email.split('@')[0]}")
        else:
            st.error("Invalid Credentials")
    
    st.divider()
    if st.button("🗑️ History Clear"):
        st.session_state.history = []
        st.rerun()

# --- [5. 메인 레이아웃: 레시피 설계] ---
st.title(f"SIB 레시피 설계 및 성능 예측 ({IP_MARK})")
st.markdown("---")

col_main, col_target = st.columns([3, 1])

with col_main:
    # 5.1. 소재 리스트 동적 생성
    st.subheader("🧪 소재 레시피 (Recipe Settings)")
    r1, r2, r3 = st.columns(3)
    
    c_list = mat_df[mat_df['Category'] == 'Cathode']['Name'].tolist()
    a_list = mat_df[mat_df['Category'] == 'Anode']['Name'].tolist()
    e_list = mat_df[mat_df['Category'] == 'Electrolyte']['Name'].tolist()
    s_list = mat_df[mat_df['Category'] == 'Separator']['Name'].tolist()

    cathode = r1.selectbox("양극재 (Cathode)", c_list)
    anode = r2.selectbox("음극재 (Anode)", a_list)
    electrolyte = r3.selectbox("전해질 (Electrolyte)", e_list)
    
    r4, r5, r6 = st.columns(3)
    additives = r4.multiselect("첨가제", ["VC", "FEC", "CNT", "Graphene"], default=["VC", "CNT"])
    separator = r5.selectbox("분리막 (Separator)", s_list)
    v_window = r6.selectbox("전압 구간 (V)", ["4.2V-2.0V", "4.0V-2.0V", "3.8V-2.0V"])

    # 5.2. 공정 파라미터 범위 동적 로드
    st.subheader("⚙️ 공정 설계 파라미터")
    p1, p2, p3 = st.columns(3)
    
    def get_cfg(param, key, default):
        try: return float(config_df.loc[param, key])
        except: return default

    c_loading = p1.slider("양극 로딩량 (mg/cm²)", get_cfg('Loading','Min',5.0), get_cfg('Loading','Max',30.0), get_cfg('Loading','Default',13.0))
    ice_val = p2.slider("초기 효율 (ICE %)", get_cfg('ICE','Min',70.0), get_cfg('ICE','Max',98.0), get_cfg('ICE','Default',85.0))
    np_ratio = p3.slider("N/P Ratio", get_cfg('NP_Ratio','Min',1.0), get_cfg('NP_Ratio','Max',1.5), get_cfg('NP_Ratio','Default',1.15))
    
    c_rate = st.slider("방전 속도 (C-rate)", 0.1, 5.0, 0.33)

with col_target:
    st.subheader("🎯 목표 설정")
    target_whkg = st.number_input("Target Energy Density", value=160.0, step=1.0)
    st.divider()
    st.write("**Design Snapshot**")
    st.caption(f"Cathode: {cathode}")
    st.caption(f"Anode: {anode}")

# --- [6. 분석 및 보고서 출력] ---
if st.button("🚀 마스터 분석 실행 및 리포트 생성", use_container_width=True):
    # [cite_start]연산 로직 (알트리스 실측 데이터 기반) [cite: 124, 213, 240]
    c_cap_base = mat_df[mat_df['Name'] == cathode]['Base_Capacity'].values[0]
    v_factor = {"4.2V-2.0V": 1.0, "4.0V-2.0V": 0.88, "3.8V-2.0V": 0.72}.get(v_window, 1.0)
    rate_factor = np.exp(-0.2 * (c_rate - 0.1))
    
    eff_cap = c_cap_base * v_factor * rate_factor * (ice_val/100.0)
    whkg = (eff_cap * 3.1 * 0.38 * (c_loading / (c_loading + 5.0))) * 10
    
    # 로그 보존 (선택한 소재 명칭을 텍스트로 저장)
    st.session_state.history.append({
        "Time": time.strftime("%H:%M"),
        "Recipe": f"{cathode}/{anode}",
        "Wh/kg": round(whkg, 1),
        "Target": target_whkg
    })

    st.markdown('<div class="report-container">', unsafe_allow_html=True)
    st.markdown(f'<div class="report-header"><h2 style="color:#1A729A; margin:0;">SIB DESIGN ANALYSIS REPORT</h2><p style="color:#666; font-size:0.9rem;">{IP_MARK}</p></div>', unsafe_allow_html=True)
    
    k1, k2, k3 = st.columns(3)
    diff = whkg - target_whkg
    color = "#28a745" if diff >= 0 else "#dc3545"
    
    # [수정] image_76578c에서 발생한 포맷팅 오류 교정 (: .1f)
    k1.markdown(f'<div class="stat-card"><div style="font-size:1.8rem; font-weight:bold; color:{color};">{whkg:.1f} Wh/kg</div><div>예상 에너지 밀도</div></div>', unsafe_allow_html=True)
    k2.markdown(f'<div class="stat-card"><div style="font-size:1.8rem; font-weight:bold;">{eff_cap:.1f} mAh/g</div><div>실효 가역 용량</div></div>', unsafe_allow_html=True)
    k3.markdown(f'<div class="stat-card"><div style="font-size:1.8rem; font-weight:bold;">{np_ratio}</div><div>N/P Ratio</div></div>', unsafe_allow_html=True)

    # [cite_start]기술적 제약 사항 코멘트 [cite: 29, 32, 221]
    st.subheader("💡 기술적 한계 및 제언 (Technical Comments)")
    c_left, c_right = st.columns(2)
    with c_left:
        st.markdown(f"**[{cathode} 특성 진단]**")
        if "프러시안" in cathode:
            [cite_start]st.warning("- 수분 민감도 극도로 높음: 공정 전 170°C 이상 진공 건조 필수[cite: 29].")
        [cite_start]st.write(f"- {anode} 매칭 시 Sodium Plating 방지를 위해 N/P Ratio 1.15 권장[cite: 221].")
    with c_right:
        st.markdown("**[목표 달성 전략]**")
        if whkg < target_whkg:
            st.error(f"- 에너지 밀도 부족: 로딩량을 {c_loading * (target_whkg/whkg):.1f}mg 이상으로 상향 필요.")
        else:
            st.success("- 설계 안정권: 현재 레시피로 샘플 제작 및 수명 테스트 권장.")
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- [7. 히스토리 비교] ---
if st.session_state.history:
    st.divider()
    st.subheader("🔄 설계 이력 로그 (History)")
    st.table(pd.DataFrame(st.session_state.history).iloc[::-1])