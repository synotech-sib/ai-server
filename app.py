import streamlit as st
import pandas as pd
import numpy as np
import time
import os

# --- [1. 외부 데이터 로드 함수] ---
@st.cache_data
def load_external_data():
    # 파일이 없을 경우를 대비한 기본값 설정
    if os.path.exists('material_list.csv'):
        mat_df = pd.read_csv('material_list.csv')
    else:
        mat_df = pd.DataFrame({
            'Category': ['Cathode', 'Anode'], 
            'Name': ['기본 양극재', '기본 음극재'], 
            'Base_Capacity': [160, 300]
        })
        
    if os.path.exists('param_config.csv'):
        config_df = pd.read_csv('param_config.csv').set_index('Parameter')
    else:
        config_df = None # 기본값 로직 사용
    
    return mat_df, config_df

mat_df, config_df = load_external_data()

# --- [2. 시스템 초기화 및 상태 관리] ---
if 'history' not in st.session_state: st.session_state.history = []
if 'is_pro' not in st.session_state: st.session_state.is_pro = False

# [변경] 모델 버전 대신 IP 문구 적용
IP_MARK = "IP by Synotech"

st.set_page_config(page_title=f"SynoCore | {IP_MARK}", layout="wide")

# --- [3. 전문 디자인 테마] ---
st.markdown(f"""
    <style>
    .stApp {{ background-color: #ffffff; }}
    .report-container {{ border: 2px solid #1A729A; padding: 40px; border-radius: 20px; background-color: #ffffff; margin-top: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }}
    .stat-card {{ background-color: #f1f6f9; border-top: 5px solid #1A729A; padding: 20px; border-radius: 10px; text-align: center; }}
    /* 고스트 슬라이더 */
    div[data-testid="stSlider"] [data-baseweb="slider"] div[role="slider"] + div > div {{
        color: #1A729A !important; font-weight: 800; font-size: 1.1rem !important;
    }}
    </style>
    """, unsafe_allow_html=True)

# --- [4. 사이드바: 이메일 로그인 및 다국어] ---
with st.sidebar:
    st.markdown(f"<h1 style='text-align: center; color: #1A729A;'>SynoCore</h1>", unsafe_allow_html=True)
    st.caption(f"Status: {IP_MARK}")
    
    st.divider()
    st.subheader("🔐 Professional Login")
    # [변경] ID를 이메일 형식으로, placeholder 설정
    u_email = st.text_input("ID", placeholder="company email")
    u_pw = st.text_input("Password", type="password")
    
    if st.button("Login"):
        if u_email == "wschoi@synotech.co.kr" and u_pw == "synotech0773!":
            st.session_state.is_pro = True
            st.success(f"Authorized: {u_email}")
        else:
            st.error("Invalid Credentials")
    
    st.divider()
    if st.button("🗑️ History Clear"):
        st.session_state.history = []
        st.rerun()

# --- [5. 메인 레이아웃: 동적 레시피 설계] ---
st.title("SIB 레시피 설계 및 IP 진단 플랫폼")
st.markdown("---")

col_main, col_target = st.columns([3, 1])

with col_main:
    st.subheader("🧪 소재 레시피 (CSV 연동)")
    r1, r2, r3 = st.columns(3)
    
    # CSV 데이터 기반 동적 선택 박스
    c_list = mat_df[mat_df['Category'] == 'Cathode']['Name'].tolist()
    a_list = mat_df[mat_df['Category'] == 'Anode']['Name'].tolist()
    e_list = mat_df[mat_df['Category'] == 'Electrolyte']['Name'].tolist()
    s_list = mat_df[mat_df['Category'] == 'Separator']['Name'].tolist()

    cathode = r1.selectbox("양극재 (Cathode)", c_list)
    anode = r2.selectbox("음극재 (Anode)", a_list)
    electrolyte = r3.selectbox("전해질 (Electrolyte)", e_list)
    
    r4, r5, r6 = st.columns(3)
    additives = r4.multiselect("첨가제 & 도전재", ["VC", "FEC", "CNT", "Graphene", "Super P"], default=["VC", "CNT"])
    separator = r5.selectbox("분리막 (Separator)", s_list)
    v_window = r6.selectbox("전압 구간 (V)", ["4.2V-2.0V", "4.0V-2.0V", "3.8V-2.0V"])

    st.subheader("⚙️ 공정 설계 파라미터 (CSV 범위 연동)")
    p1, p2, p3 = st.columns(3)
    
    # CSV에서 슬라이더 범위 로드
    def get_cfg(param, key, default):
        try: return float(config_df.loc[param, key])
        except: return default

    c_loading = p1.slider("양극 로딩량 (mg/cm²)", get_cfg('Loading','Min',5.0), get_cfg('Loading','Max',30.0), get_cfg('Loading','Default',13.0))
    ice_val = p2.slider("초기 효율 (ICE %)", get_cfg('ICE','Min',70.0), get_cfg('ICE','Max',98.0), get_cfg('ICE','Default',85.0))
    np_ratio = p3.slider("N/P Ratio", get_cfg('NP_Ratio','Min',1.0), get_cfg('NP_Ratio','Max',1.5), get_cfg('NP_Ratio','Default',1.15))

with col_target:
    st.subheader("🎯 목표 설정")
    target_whkg = st.number_input("Target Energy (Wh/kg)", value=160.0, step=1.0)
    st.divider()
    st.write("**Design Snapshot**")
    st.caption(f"C: {cathode}")
    st.caption(f"A: {anode}")
    st.caption(f"E: {electrolyte}")

# --- [6. 분석 및 보고서 (로그 보관 로직 포함)] ---
if st.button("🚀 분석 실행 및 기술 보고서 생성", use_container_width=True):
    # 연산 로직 (기존 마스터 로직 유지)
    c_cap = mat_df[mat_df['Name'] == cathode]['Base_Capacity'].values[0]
    v_eff = {"4.2V-2.0V": 1.0, "4.0V-2.0V": 0.88, "3.8V-2.0V": 0.72}.get(v_window, 1.0)
    eff_cap = c_cap * v_eff * (ice_val/100.0) * 0.9 # 간이 C-rate 보정
    whkg = (eff_cap * 3.1 * 0.38 * (c_loading / (c_loading + 5.0))) * 10
    
    # [로그 보관] 파일이 바뀌어도 당시 선택한 '소재명'과 '수치'가 그대로 히스토리에 남음
    st.session_state.history.append({
        "Date": time.strftime("%Y-%m-%d %H:%M"),
        "Cathode": cathode,
        "Anode": anode,
        "Loading": c_loading,
        "Wh/kg": round(whkg, 1),
        "Target": target_whkg
    })

    # 보고서 렌더링
    st.markdown('<div class="report-container">', unsafe_allow_html=True)
    st.markdown(f'<div class="report-header"><h2 style="color:#1A729A; margin:0;">SIB DESIGN REPORT</h2><p style="color:#666;">{IP_MARK}</p></div>', unsafe_allow_html=True)
    
    k1, k2, k3 = st.columns(3)
    diff = whkg - target_whkg
    k1.markdown(f'<div class="stat-card"><div style="font-size:1.8rem; font-weight:bold; color:{"#28a745" if diff>=0 else "#dc3545"};">{whkg} Wh/kg</div><div>예상 에너지 밀도</div></div>', unsafe_allow_html=True)
    k2.markdown(f'<div class="stat-card"><div style="font-size:1.8rem; font-weight:bold;">{eff_cap:.1f} mAh/g</div><div>실효 가역 용량</div></div>', unsafe_allow_html=True)
    k3.markdown(f'<div class="stat-card"><div style="font-size:1.8rem; font-weight:bold;">{np_ratio}</div><div>N/P Ratio</div></div>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- [7. 히스토리 섹션] ---
if st.session_state.history:
    st.divider()
    st.subheader("🔄 설계 로그 (Design Logs)")
    st.table(pd.DataFrame(st.session_state.history).iloc[::-1])