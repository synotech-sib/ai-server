# modules/database.py (업데이트된 버전)
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

# [Step 3 추가] 감사 로그 불러오기 함수
def get_audit_logs():
    conn = sqlite3.connect(LOG_PATH)
    df = pd.read_sql_query("SELECT * FROM audit_logs ORDER BY timestamp DESC", conn)
    conn.close()
    return df