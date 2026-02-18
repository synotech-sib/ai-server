import streamlit as st
import pandas as pd
import numpy as np
import time
import matplotlib.pyplot as plt

# 모듈 및 설정 임포트
from config.security_cfg import SECURITY_MODE, verify_admin_access
from modules.engine import calculate_battery_specs
from modules.database import init_db, save_lead, get_leads, log_action, get_audit_logs
from modules.reporter import generate_expert_report

# --- [1. 시스템 초기화 & Syno Blue 테마 적용] ---
st.set_page_config(page_title="SynoCore V1.2 | SynoTech Strategic Platform", layout="wide")

# [Step 6 고도화] 시노텍 로고 칼라 #1A729A 반영 및 타이틀 크기 조정 CSS
st.markdown("""
    <style>
    /* 전체 배경 및 폰트 */
    .stApp { background-color: #ffffff; }
    
    /* 메인 타이틀 스타일: 글자 크기 축소 및 Syno Blue 적용 */
    h1 { 
        color: #1A729A !important; 
        font-weight: 700 !important; 
        font-size: 2.0rem !important; /* 타이틀 크기 조절 */
        border-bottom: 2px solid #1A729A; 
        padding-bottom: 8px; 
        margin-bottom: 20px;
    }
    
    /* 서브 헤더 스타일 */
    h2, h3 { color: #1A729A !important; font-weight: 600 !important; }
    
    /* 버튼 스타일 커스텀: #1A729A */
    .stButton>button {
        background-color: #1A729A;
        color: white;
        border-radius: 6px;
        border: none;
        height: 3em;
        width: 100%;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        background-color: #145d7d;
        border: none;
        color: #ffffff;
        box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    }
    
    /* 사이드바 스타일 */
    [data-testid="stSidebar"] { background-color: #f1f6f9; border-right: 1px solid #1A729A; }
    
    /* 입력창 테두리 강조 */
    .stNumberInput div[data-baseweb="input"] { border: 1px solid #1A729A; }
    
    /* 화이트 라벨링: 메인 메뉴 숨기기 */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
    """, unsafe_allow_html=True)

if 'initialized' not in st.session_state:
    init_db()
    log_action("System", "SynoBlue Theme & Adjusted Typography Applied")
    st.session_state.initialized = True

# --- [2. 다국어 사전 설정] ---
LANG_DICT = {
    "English": {
        "title": "SynoCore V1.2: Strategic SIB Intelligence",
        "subtitle": "Developed by Woosuk Choi & SeoYeon Choi | SynoTech Co., Ltd.",
        "btn_run": "🚀 EXECUTE STRATEGIC ANALYSIS",
        "res_h": "📊 Design Performance Metrics",
        "pdf_btn": "📥 Download Expert Intelligence