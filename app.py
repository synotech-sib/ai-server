import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import os
import random
import io
from datetime import datetime

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 커스텀 CSS (디자인/레이아웃 제어)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="SynoCore V1.4 Pro Max", layout="wide")

# CSS: 메뉴 숨김, 타이틀 스타일, 버튼 색상, 글자 크기 조정
st.markdown("""
    <style>
    /* 1. Streamlit 기본 메뉴 및 푸터 숨김 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* 2. SynoCore 타이틀 스타일 */
    .syno-title {
        font-family: 'Helvetica', sans-serif;
        color: #003366; /* 시노텍 로고색 */
        font-size: 40px;
        font-weight: 900;
        margin-bottom: -10px;
        line-height: 1.0;
    }
    .syno-subtitle {
        font-family: 'Helvetica', sans-serif;
        color: #000000;
        font-size: 18px;
        font-weight: normal;
        margin-top: 0px;
    }

    /* 3. 버튼 스타일 (시노텍 네이비) */
    div.stButton > button:first-child {
        background-color: #003366;
        color: white;
        border-radius: 5px;
        height: 3.5em;
        width: 100%;
        font-weight: bold;
        font-size: 18px;
        border: none;
    }
    div.stButton > button:hover {
        background-color: #004080;
        color: white;
    }

    /* 4. 섹션 제목 스타일 (기본보다 크고 볼드체) */
    .section-header {
        font-size: 24px !important;
        font-weight: bold !important;
        color: #333;
        margin-top: 20px;
        margin-bottom: 10px;
    }
    
    /* 5. 소제목 스타일 (2번, 3번, 4번 항목용) */
    .sub-label {
        font-size: 18px !important;
        font-weight: bold !important;
        color: #444;
        margin-bottom: 5px;
    }

    /* 6. 무료 체험 박스 */
    .free-trial-box {
        background-color: #003366;
        color: white;
        padding: 10px;
        text-align: center;
        border-radius: 5px;
        font-weight: bold;
        margin-top: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 데이터 관리 함수 (User DB, Material DB)
# -----------------------------------------------------------------------------
@st.cache_data
def load_db():
    try:
        mat_df = pd.read_excel("material_list.xlsx")
        param_df = pd.read_excel("param_config.xlsx")
        param_df.set_index("Parameter_ID", inplace=True)
        return mat_df, param_df
    except:
        return pd.DataFrame(), pd.DataFrame()

def load_users():
    if not os.path.exists("users.xlsx"):
        df = pd.DataFrame(columns=["Email", "Password", "Name", "Company", "Dept", "Role", "Title", "Phone", "Is_Pro", "History"])
        df.to_excel("users.xlsx", index=False)
        return df
    return pd.read_excel("users.xlsx")

def save_user(new_user_data):
    df = load_users()
    new_row = pd.DataFrame([new_user_data])
    df = pd.concat([df, new_row], ignore_index=True)
    df.to_excel("users.xlsx", index=False)

mat_df, param_dict = load_db()

# -----------------------------------------------------------------------------
# 3. 세션 상태 초기화
# -----------------------------------------------------------------------------
if 'logged_in' not in st.session_state: st.session_state.logged_in = False
if 'is_pro' not in st.session_state: st.session_state.is_pro = False
if 'trial_count' not in st.session_state: st.session_state.trial_count = 0
if 'user_email' not in st.session_state: st.session_state.user_email = ""
if 'user_name' not in st.session_state: st.session_state.user_name = "Guest"
if 'history' not in st.session_state: st.session_state.history = [] # 시뮬레이션 기록
if 'reg_stage' not in st.session_state: st.session_state.reg_stage = 0 # 회원가입 단계
if 'verify_code' not in st.session_state: st.session_state.verify_code = None

# -----------------------------------------------------------------------------
# 4. 상단 레이아웃 (타이틀 & 로그인)
# -----------------------------------------------------------------------------
top_c1, top_c2 = st.columns([2, 3])

with top_c1:
    # 요청하신 타이틀 디자인 적용
    st.markdown('<div class="syno-title">SynoCore</div>', unsafe_allow_html=True)
    st.markdown('<div class="syno-subtitle">V1.4 Pro</div>', unsafe_allow_html=True)

with top_c2:
    if not st.session_state.logged_in:
        # 로그인 폼 (엔터키 로그인 지원)
        with st.form(key='login_form'):
            lc1, lc2, lc3 = st.columns([2, 2, 1])
            with lc1:
                uid = st.text_input("User ID", placeholder="company@email.com", label_visibility="collapsed")
            with lc2:
                upw = st.text_input("Password", type="password", placeholder="Password", label_visibility="collapsed")
            with lc3:
                submit_login = st.form_submit_button("Login")
            
            if submit_login:
                users = load_users()
                user = users[(users['Email'] == uid) & (users['Password'] == upw)]
                if not user.empty:
                    st.session_state.logged_in = True
                    st.session_state.is_pro = bool(user.iloc[0]['Is_Pro'])
                    st.session_state.user_email = uid
                    st.session_state.user_name = user.iloc[0]['Name']
                    st.rerun()
                else:
                    st.error("Login Failed")
        
        # 무료 체험 표시 (딥블루 박스)
        if not st.session_state.logged_in:
             st.markdown(f'<div class="free-trial-box">무료 시도 {st.session_state.trial_count}/3 (Guest Mode)</div>', unsafe_allow_html=True)

    else:
        # 로그인 후 상태창
        st.info(f"Welcome, **{st.session_state.user_name}** ({'PRO Member' if st.session_state.is_pro else 'Free Member'})")
        if st.button("Logout"):
            st.session_state.logged_in = False
            st.session_state.is_pro = False
            st.rerun()

# -----------------------------------------------------------------------------
# 5. 회원가입 프로세스 (Pro 전환)
# -----------------------------------------------------------------------------
if not st.session_state.logged_in or (st.session_state.logged_in and not st.session_state.is_pro):
    with st.expander("✨ Pro 회원가입 / 계정 생성"):
        if st.session_state.reg_stage == 0:
            reg_email = st.text_input("회사 이메일 입력")
            if st.button("인증번호 전송"):
                if "@" in reg_email:
                    code = str(random.randint(100000, 999999))
                    st.session_state.verify_code = code
                    st.session_state.temp_email = reg_email
                    st.session_state.reg_stage = 1
                    st.success(f"[System] 인증번호가 발송되었습니다: {code}") # 실제로는 이메일 발송
                else:
                    st.error("유효한 이메일 형식이 아닙니다.")
        
        elif st.session_state.reg_stage == 1:
            st.write(f"Email: {st.session_state.temp_email}")
            input_code = st.text_input("인증번호 6자리")
            if st.button("인증 확인"):
                if input_code == st.session_state.verify_code:
                    st.session_state.reg_stage = 2
                    st.rerun()
                else:
                    st.error("인증번호가 일치하지 않습니다.")

        elif st.session_state.reg_stage == 2:
            st.success("이메일 인증 완료!")
            with st.form("register_form"):
                re_email = st.text_input("이메일", value=st.session_state.temp_email, disabled=True)
                re_pw = st.text_input("비밀번호", type="password")
                re_pw2 = st.text_input("비밀번호 확인", type="password")
                re_name = st.text_input("이름")
                re_comp = st.text_input("회사")
                re_dept = st.text_input("부서")
                re_role = st.text_input("담당업무")
                re_title = st.text_input("직함")
                re_phone = st.text_input("연락처")
                
                if st.form_submit_button("가입 완료"):
                    if re_pw == re_pw2 and re_pw != "":
                        save_user({
                            "Email": re_email, "Password": re_pw, "Name": re_name,
                            "Company": re_comp, "Dept": re_dept, "Role": re_role,
                            "Title": re_title, "Phone": re_phone, "Is_Pro": True, "History": ""
                        })
                        st.success("가입 완료! Pro 권한이 부여되었습니다. 로그인해주세요.")
                        st.session_state.reg_stage = 0
                    else:
                        st.error("비밀번호를 확인해주세요.")

st.markdown("---")

# -----------------------------------------------------------------------------
# 6. 메인 시뮬레이터 로직
# -----------------------------------------------------------------------------

# 권한 체크: 3회 초과시 차단
if not st.session_state.is_pro and st.session_state.trial_count >= 3:
    st.warning("🔒 무료 체험 횟수(3회)가 만료되었습니다. Pro 회원으로 전환하여 무제한 시뮬레이션을 이용하세요.")
    st.stop()

# [1번] Material Selection
st.markdown('<div class="section-header">1. Material Selection</div>', unsafe_allow_html=True)
m1, m2, m3, m4 = st.columns(4)

with m1:
    cat_list = mat_df[mat_df['Category'] == 'Cathode']['Name'].tolist()
    cat_name = st.selectbox("Cathode", cat_list, key='sel_cat')
    cat_row = mat_df[mat_df['Name'] == cat_name].iloc[0]
with m2:
    ano_list = mat_df[mat_df['Category'] == 'Anode']['Name'].tolist()
    ano_name = st.selectbox("Anode", ano_list, key='sel_ano')
    ano_row = mat_df[mat_df['Name'] == ano_name].iloc[0]
with m3:
    elec_list = mat_df[mat_df['Category'] == 'Electrolyte']['Name'].tolist()
    elec_name = st.selectbox("Electrolyte", elec_list, key='sel_elec')
with m4:
    sep_list = mat_df[mat_df['Category'] == 'Separator']['Name'].tolist()
    sep_name = st.selectbox("Separator", sep_list, key='sel_sep')

# [2번] Material Specs (Expert Mode)
st.markdown("---")
st.markdown('<div class="section-header">2. Material Specs Expert Mode</div>', unsafe_allow_html=True)
expert_spec = st.checkbox("🔓 물성 직접 수정")

# 기본값 로드
if expert_spec:
    st.markdown('<div class="sub-label">Adjust Properties</div>', unsafe_allow_html=True)
    sc1, sc2, sc3, sc4 = st.columns(4)
    c_cap = sc1.number_input("Capacity (mAh/g)", value=float(cat_row['Base_Capacity']))
    c_volt = sc2.number_input("Voltage (V)", value=float(cat_row['Base_Avg_Voltage']))
    c_dens = sc3.number_input("Density (g/cc)", value=float(cat_row['Base_True_Density']))
    c_life = sc4.number_input("Life (Cycles)", value=int(cat_row['Base_Life']))
else:
    # 기본 모드일 때 글자 크게 볼드체
    sc1, sc2, sc3, sc4 = st.columns(4)
    sc1.markdown(f"#### **Capacity**\n### {cat_row['Base_Capacity']} mAh/g")
    sc2.markdown(f"#### **Voltage**\n### {cat_row['Base_Avg_Voltage']} V")
    sc3.markdown(f"#### **Density**\n### {cat_row['Base_True_Density']} g/cc")
    sc4.markdown(f"#### **Life**\n### {cat_row['Base_Life']} Cyc")
    # 변수 할당
    c_cap, c_volt, c_dens, c_life = cat_row['Base_Capacity'], cat_row['Base_Avg_Voltage'], cat_row['Base_True_Density'], cat_row['Base_Life']

# [3번] Process Parameters
st.markdown("---")
st.markdown('<div class="section-header">3. Process Parameters</div>', unsafe_allow_html=True)
expert_param = st.checkbox("🔓 공정 파라미터 수정")

# 스마트 프리셋
if 'last_cat' not in st.session_state or st.session_state.last_cat != cat_name:
    st.session_state['loading'] = float(cat_row['Rec_Loading'])
    st.session_state['cat_density'] = float(cat_row['Rec_Density'])
    st.session_state['active_ratio'] = float(cat_row['Rec_Active'])
    st.session_state.last_cat = cat_name

p1, p2, p3 = st.columns(3)
with p1:
    st.markdown('<div class="sub-label">(A) Cathode Settings</div>', unsafe_allow_html=True)
    loading = st.slider("Loading (mg/cm2)", 5.0, 40.0, value=st.session_state['loading'], disabled=not expert_param)
    cat_dens_val = st.slider("Cathode Density (g/cc)", 1.5, 3.5, value=st.session_state['cat_density'], disabled=not expert_param)

with p2:
    st.markdown('<div class="sub-label">(B) Anode Settings</div>', unsafe_allow_html=True)
    np_ratio = st.slider("N/P Ratio", 1.0, 1.5, 1.15, 0.01)
    ano_dens_val = st.slider("Anode Density (g/cc)", 0.8, 2.0, value=float(ano_row['Rec_Density']), disabled=not expert_param)

with p3:
    st.markdown('<div class="sub-label">(C) Electrolyte</div>', unsafe_allow_html=True)
    ec_ratio = st.slider("E/C Ratio (g/Ah)", 1.0, 8.0, 3.5)
    active_ratio = st.slider("Active Ratio (%)", 85.0, 99.0, value=st.session_state['active_ratio'], disabled=not expert_param)

# [4번] Target Setting
st.markdown("---")
st.markdown('<div class="section-header">4. Target Configuration</div>', unsafe_allow_html=True)
t1, t2 = st.columns(2)
with t1:
    st.markdown('<div class="sub-label">Target Energy Density (Wh/kg)</div>', unsafe_allow_html=True)
    target_energy = st.slider("Label Hidden", 100, 250, 160, label_visibility="collapsed")
with t2:
    st.markdown('<div class="sub-label">Target C-rate (C)</div>', unsafe_allow_html=True)
    target_crate = st.slider("Label Hidden", 0.1, 20.0, 1.0, 0.1, label_visibility="collapsed")

# [5번] Simulation History & Execution
st.markdown("---")
st.markdown('<div class="section-header">5. Simulation History & Run</div>', unsafe_allow_html=True)

# 실행 버튼
if st.button("🚀 RUN DESIGN SIMULATION"):
    st.session_state.trial_count += 1
    
    # 계산 로직
    cell_v = c_volt - ano_row['Base_Avg_Voltage']
    crate_factor = np.exp(-0.025 * (target_crate - 1)) if target_crate > 1 else 1.0
    eff_cap = c_cap * crate_factor
    cat_cap_area = loading * (active_ratio / 100) * eff_cap
    ano_loading = (cat_cap_area * np_ratio) / (ano_row['Base_Capacity'] * (ano_row['Base_ICE']/100) * (active_ratio/100))
    elec_weight = (cat_cap_area / 1000) * ec_ratio
    total_weight = (loading + ano_loading + elec_weight + 5) / 1000
    wh_kg = (cat_cap_area / 1000 * cell_v) / total_weight
    
    sim_id = f"{st.session_state.trial_count:03d}"
    
    # 이력 저장
    record = {
        "ID": sim_id,
        "Timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "Label": f"[{sim_id}] {cat_name[:5]}../{ano_name[:5]}.. | {target_crate}C | {wh_kg:.1f} Wh/kg",
        "Result": {
            "wh_kg": wh_kg, "cell_v": cell_v, "eff_cap": eff_cap, "loading": loading,
            "ano_loading": ano_loading, "elec_weight": elec_weight, "c_life": c_life
        }
    }
    
    st.session_state.history.insert(0, record)
    # Pro가 아니면 3개까지만 유지
    if not st.session_state.is_pro:
        st.session_state.history = st.session_state.history[:3]
    
    st.session_state.current_result = record

# 이력 선택 (복원)
if st.session_state.history:
    st.markdown('<div class="sub-label">과거 시뮬레이션 기록 선택 (Select History)</div>', unsafe_allow_html=True)
    options = {rec['Label']: rec for rec in st.session_state.history}
    selected_label = st.selectbox("기록 선택", list(options.keys()), label_visibility="collapsed")
    st.session_state.current_result = options[selected_label]

# -----------------------------------------------------------------------------
# 결과 대시보드 (Result Dashboard)
# -----------------------------------------------------------------------------
if 'current_result' in st.session_state and st.session_state.current_result:
    res = st.session_state.current_result['Result']
    
    st.markdown("---")
    st.markdown(f"### 📊 Simulation Result")
    
    # 결과 지표 (크고 볼드체)
    r1, r2, r3, r4 = st.columns(4)
    r1.markdown(f"#### **Energy Density**\n### {res['wh_kg']:.1f} Wh/kg")
    r2.markdown(f"#### **Cell Voltage**\n### {res['cell_v']:.2f} V")
    r3.markdown(f"#### **Capacity @ {target_crate}C**\n### {res['eff_cap']:.1f} mAh/g")
    r4.markdown(f"#### **Est. Life**\n### {int(res['c_life']):,} Cycles")

    # 그래프 생성
    g1, g2 = st.columns(2)
    
    with g1:
        # 1. C-rate별 용량 유지율 (Rate Capability)
        rates = np.linspace(0.1, 20, 50)
        retention = [np.exp(-0.025 * (r - 1)) * 100 if r > 1 else 100 for r in rates]
        fig_rate = go.Figure()
        fig_rate.add_trace(go.Scatter(x=rates, y=retention, mode='lines', name='Retention', line=dict(color='#003366', width=3)))
        fig_rate.update_layout(title="<b>Rate Capability</b>", xaxis_title="C-rate", yaxis_title="Retention (%)", template="plotly_white")
        st.plotly_chart(fig_rate, use_container_width=True)

    with g2:
        # 2. 방전 곡선 (Voltage Profile - Simulated)
        cap_range = np.linspace(0, res['eff_cap'], 100)
        # 하드카본 특유의 슬로프 + 플래토 형상 모사
        v_profile = res['cell_v'] - (0.5 * (cap_range / res['eff_cap'])**2) - (0.1 * np.exp(cap_range/10)) 
        fig_prof = go.Figure()
        fig_prof.add_trace(go.Scatter(x=cap_range, y=v_profile, mode='lines', name='Discharge', line=dict(color='#FF5733', width=3)))
        fig_prof.update_layout(title="<b>Discharge Profile (Simulated)</b>", xaxis_title="Capacity (mAh/g)", yaxis_title="Voltage (V)", template="plotly_white")
        st.plotly_chart(fig_prof, use_container_width=True)

    # 상세 데이터 표
    st.markdown("#### **📋 Detailed Design Specification**")
    spec_df = pd.DataFrame({
        "Parameter": ["Cathode Loading", "Anode Loading", "Electrolyte Weight", "N/P Ratio", "Active Material"],
        "Value": [f"{res['loading']} mg/cm²", f"{res['ano_loading']:.2f} mg/cm²", f"{res['elec_weight']:.2f} mg/cm²", f"{np_ratio}", f"{active_ratio}%"],
        "Note": ["Main Control", "Balanced", "E/C Ratio Applied", "Safety Margin", "Conductivity"]
    })
    st.table(spec_df)

    # 엑셀 다운로드
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        spec_df.to_excel(writer, sheet_name='Spec_Sheet')
        pd.DataFrame([res]).to_excel(writer, sheet_name='Raw_Data')
    
    st.download_button(
        label="📥 Download Report (Excel)",
        data=buffer,
        file_name=f"SynoCore_Report_{st.session_state.current_result['ID']}.xlsx",
        mime="application/vnd.ms-excel"
    )