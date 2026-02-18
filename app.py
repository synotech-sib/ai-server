import streamlit as st
import pandas as pd
import numpy as np
import time
import os

# --- [1. 외부 데이터 로드 엔진: XLSX & CSV 지원] ---
def load_external_data():
    files = os.listdir('.')
    # 1.1 소재 리스트 로딩
    mat_df = None
    try:
        if 'material_list.xlsx' in files:
            mat_df = pd.read_excel('material_list.xlsx', engine='openpyxl')
        elif 'material_list.csv' in files:
            mat_df = pd.read_csv('material_list.csv')
        else:
            # 파일 부재 시 알트리스 실측 데이터 기본값 적용
            mat_df = pd.DataFrame({
                'Category': ['Cathode', 'Cathode', 'Anode', 'Electrolyte', 'Separator'],
                'Name': ['프러시안 화이트 (PW)', '층상산화물 (LO)', '쿠라레 A', 'G Type (표준)', 'PE'],
                'Base_Capacity': [162.0, 135.0, 340.0, 1.0, 1.0]
            })
    except ImportError:
        st.error("⚠️ 'openpyxl' 라이브러리가 필요합니다. 터미널에서 'pip install openpyxl'을 실행해주세요.")
        # 폴백 데이터
        mat_df = pd.DataFrame({'Category':['Cathode'],'Name':['Default'],'Base_Capacity':[162.0]})

    # 1.2 공정 범위 설정 로딩
    config_df = None
    if 'param_config.xlsx' in files:
        config_df = pd.read_excel('param_config.xlsx', engine='openpyxl').set_index('Parameter')
    elif 'param_config.csv' in files:
        config_df = pd.read_csv('param_config.csv').set_index('Parameter')
        
    return mat_df, config_df

mat_df, config_df = load_external_data()

# --- [2. 시스템 초기화 및 테마 설정] ---
if 'history' not in st.session_state: st.session_state.history = []
if 'is_pro' not in st.session_state: st.session_state.is_pro = False
IP_MARK = "IP by Synotech"

st.set_page_config(page_title=f"SynoCore | {IP_MARK}", layout="wide")

# CSS 스타일 정의
st.markdown(f"""
    <style>
    .stApp {{ background-color: #ffffff; }}
    .report-container {{ border: 2px solid #1A729A; padding: 35px; border-radius: 15px; background-color: #ffffff; margin-top: 20px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
    .report-header {{ border-bottom: 2px solid #1A729A; padding-bottom: 15px; margin-bottom: 25px; text-align: center; }}
    .stat-card {{ background-color: #f1f6f9; border-top: 5px solid #1A729A; padding: 20px; border-radius: 10px; text-align: center; }}
    div[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] + div > div {{ color: #1A729A !important; font-weight: 800; font-size: 1.1rem !important; }}
    </style>
    """, unsafe_allow_html=True)

# --- [3. 사이드바: 이메일 로그인 및 목표 설정] ---
with st.sidebar:
    st.markdown("<h1 style='text-align: center; color: #1A729A; font-weight: 800;'>SynoCore</h1>", unsafe_allow_html=True)
    st.caption(f"Status: {IP_MARK}")
    
    st.divider()
    st.subheader("🎯 목표 에너지 밀도")
    target_whkg = st.number_input("Target (Wh/kg)", value=160.0, step=1.0)
    
    st.divider()
    st.subheader("🔐 Professional Login")
    u_email = st.text_input("ID", placeholder="company email")
    u_pw = st.text_input("Password", type="password")
    
    if st.button("Login"):
        # [해결] wschoi@synotech.co.kr 전용 계정 적용
        if u_email == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
            st.session_state.is_pro = True
            st.success(f"Authorized: {u_email.split('@')[0]}")
        else:
            st.error("Invalid Credentials")
    
    st.divider()
    if st.button("🗑️ History Clear"):
        st.session_state.history = []
        st.rerun()

# --- [4. 메인 UI: 레시피 설계] ---
st.title(f"SIB 레시피 설계 및 성능 예측 플랫폼 ({IP_MARK})")
st.markdown("---")

col_left, col_right = st.columns([3, 1])

with col_left:
    st.subheader("🧪 소재 레시피 (Recipe Selection)")
    r1, r2, r3 = st.columns(3)
    c_list = mat_df[mat_df['Category'] == 'Cathode']['Name'].tolist()
    a_list = mat_df[mat_df['Category'] == 'Anode']['Name'].tolist()
    e_list = mat_df[mat_df['Category'] == 'Electrolyte']['Name'].tolist()

    cathode = r1.selectbox("양극재 (Cathode)", c_list)
    anode = r2.selectbox("음극재 (Anode)", a_list)
    electrolyte = r3.selectbox("전해질 (Electrolyte)", e_list)
    
    st.subheader("⚙️ 공정 설계 파라미터")
    p1, p2, p3 = st.columns(3)
    
    def get_cfg(param, key, default):
        if config_df is not None and param in config_df.index:
            try: return float(config_df.loc[param, key])
            except: return default
        return default

    c_loading = p1.slider("양극 로딩량 (mg/cm²)", get_cfg('Loading','Min',5.0), get_cfg('Loading','Max',30.0), get_cfg('Loading', 'Default', 13.0))
    ice_val = p2.slider("초기 효율 (ICE %)", get_cfg('ICE','Min',50.0), get_cfg('ICE','Max',98.0), get_cfg('ICE', 'Default', 85.0))
    np_ratio = p3.slider("N/P Ratio", get_cfg('NP_Ratio','Min',1.0), get_cfg('NP_Ratio','Max',1.5), get_cfg('NP_Ratio', 'Default', 1.15))
    
    v_window = st.selectbox("전압 구간 (V Window)", ["4.2V-2.0V", "4.0V-2.0V", "3.8V-2.0V"])
    c_rate = st.slider("방전 속도 (C-rate)", 0.1, 5.0, 0.33)

with col_right:
    st.subheader("📋 설계 요약")
    st.write(f"**Cathode:** {cathode}")
    st.write(f"**Anode:** {anode}")
    st.write(f"**Target:** {target_whkg} Wh/kg")
    
    # [수정] image_76578c 에러 해결: 포맷팅 교정
    c_cap_base = mat_df[mat_df['Name'] == cathode]['Base_Capacity'].values[0]
    st.info(f"선택 소재 비용량: {c_cap_base:.1f} mAh/g")

# --- [5. 분석 실행 및 보고서 생성] ---
if st.button("🚀 마스터 분석 실행 및 리포트 생성", use_container_width=True):
    # 5.1 계산 로직
    v_factor = {"4.2V-2.0V": 1.0, "4.0V-2.0V": 0.88, "3.8V-2.0V": 0.72}.get(v_window, 1.0)
    rate_factor = np.exp(-0.2 * (c_rate - 0.1))
    
    eff_cap = c_cap_base * v_factor * rate_factor * (ice_val/100.0)
    whkg = (eff_cap * 3.1 * 0.38 * (c_loading / (c_loading + 5.0))) * 10
    
    # 히스토리 저장
    st.session_state.history.append({
        "Date": time.strftime("%Y-%m-%d %H:%M"),
        "Recipe": f"{cathode}/{anode}",
        "Wh/kg": round(whkg, 1),
        "Target": target_whkg
    })

    # 보고서 렌더링
    st.markdown('<div class="report-container">', unsafe_allow_html=True)
    st.markdown(f'<div class="report-header"><h2 style="color:#1A729A; margin:0;">SIB DESIGN REPORT</h2><p style="color:#666;">{IP_MARK}</p></div>', unsafe_allow_html=True)
    
    k1, k2, k3 = st.columns(3)
    diff = whkg - target_whkg
    color_code = "#28a745" if diff >= 0 else "#dc3545"
    
    # [해결] image_77bcfc 중괄호 충돌 방지를 위한 별도 렌더링
    k1.markdown(f'<div class="stat-card"><div style="font-size:1.8rem; font-weight:bold; color:{color_code};">{whkg:.1f} Wh/kg</div><div>예상 에너지 밀도</div></div>', unsafe_allow_html=True)
    k2.markdown(f'<div class="stat-card"><div style="font-size:1.8rem; font-weight:bold;">{eff_cap:.1f} mAh/g</div><div>실효 가역 용량</div></div>', unsafe_allow_html=True)
    k3.markdown(f'<div class="stat-card"><div style="font-size:1.8rem; font-weight:bold;">{np_ratio}</div><div>N/P Ratio</div></div>', unsafe_allow_html=True)

    # 5.2 기술적 제언 (Altris 자료 근거) [cite: 29, 30, 231, 234]
    st.subheader("⚠️ 기술적 한계 및 제언 (Technical Comments)")
    cl, cr = st.columns(2)
    with cl:
        st.markdown(f"**[{cathode} 특성 분석]**")
        if "프러시안" in cathode:
            st.warning("알트리스 가이드(Page 4)에 따라 170°C 이상 진공 건조(12-24h)가 수분 제어의 핵심입니다.")
        st.write(f"- {anode} 음극 매칭 시 Sodium Plating 방지를 위해 N/P Ratio 1.15를 권장합니다.")
    with cr:
        st.markdown("**[설계 최적화 전략]**")
        if whkg < target_whkg:
            st.error(f"목표 미달: 로딩량을 {c_loading * (target_whkg/whkg):.1f}mg 이상으로 상향 검토하십시오.")
        else:
            st.success("설계 안정권: 현재 레시피로 프로토타입 제작을 권장합니다.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- [6. 설계 히스토리 섹션] ---
if st.session_state.history:
    st.divider()
    st.subheader("🔄 설계 이력 로그 (History)")
    st.table(pd.DataFrame(st.session_state.history).iloc[::-1])