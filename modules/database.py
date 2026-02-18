# modules/database.py (보안 강화 버전)
import sqlite3
import pandas as pd
from datetime import datetime
import os
import shutil

# 경로 설정
STORAGE_DIR = 'storage'
LOG_DIR = os.path.join(STORAGE_DIR, 'audit_logs')
DB_PATH = os.path.join(STORAGE_DIR, 'synotech_leads.db')
LOG_DB_PATH = os.path.join(LOG_DIR, 'audit.db')

def init_db():
    # 폴더 생성 로직 보강
    try:
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR, exist_ok=True)
    except FileExistsError:
        # 만약 같은 이름의 '파일'이 있다면 제거하고 폴더로 생성
        if not os.path.isdir(LOG_DIR):
            os.remove(LOG_DIR) if os.path.isfile(LOG_DIR) else shutil.rmtree(LOG_DIR)
            os.makedirs(LOG_DIR, exist_ok=True)

    # 고객 리드 DB 초기화
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leads 
                 (id INTEGER PRIMARY KEY, name TEXT, company TEXT, 
                  mobile TEXT, email TEXT, reg_date TEXT)''')
    conn.commit()
    conn.close()
    
    # 감사 로그 DB 초기화
    conn_log = sqlite3.connect(LOG_DB_PATH)
    cl = conn_log.cursor()
    cl.execute('''CREATE TABLE IF NOT EXISTS audit_logs 
                  (id INTEGER PRIMARY KEY, user TEXT, action TEXT, timestamp TEXT)''')
    conn_log.commit()
    conn_log.close()

# 나머지 함수들 (log_action, save_lead, get_leads, get_audit_logs)은 이전과 동일하게 유지
def log_action(user, action):
    conn = sqlite3.connect(LOG_DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO audit_logs (user, action, timestamp) VALUES (?, ?, ?)",
              (user, action, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def save_lead(name, company, mobile, email):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO leads (name, company, mobile, email, reg_date) VALUES (?, ?, ?, ?, ?)",
              (name, company, mobile, email, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_leads():
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT * FROM leads ORDER BY reg_date DESC", conn)
    conn.close()
    return df

def get_audit_logs():
    conn = sqlite3.connect(LOG_DB_PATH)
    df = pd.read_sql_query("SELECT * FROM audit_logs ORDER BY timestamp DESC", conn)
    conn.close()
    return df
