# modules/database.py
import sqlite3
import pandas as pd
from datetime import datetime
import os

DB_PATH = 'storage/synotech_leads.db'
LOG_PATH = 'storage/audit_logs/audit.db'

def init_db():
    os.makedirs('storage/audit_logs', exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leads 
                 (id INTEGER PRIMARY KEY, name TEXT, company TEXT, 
                  mobile TEXT, email TEXT, reg_date TEXT)''')
    conn.commit()
    conn.close()
    
    # 감사 로그 테이블 생성
    conn_log = sqlite3.connect(LOG_PATH)
    cl = conn_log.cursor()
    cl.execute('''CREATE TABLE IF NOT EXISTS audit_logs 
                  (id INTEGER PRIMARY KEY, user TEXT, action TEXT, timestamp TEXT)''')
    conn_log.commit()
    conn_log.close()

def log_action(user, action):
    conn = sqlite3.connect(LOG_PATH)
    c = conn.cursor()
    c.execute("INSERT INTO audit_logs (user, action, timestamp) VALUES (?, ?, ?)",
              (user, action, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

# (save_lead, get_leads 함수는 기존과 동일하게 유지하되 DB_PATH 사용)
