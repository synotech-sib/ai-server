import sqlite3
import pandas as pd  # <--- 이 줄이 빠져서 에러가 났습니다!
from datetime import datetime

# 데이터베이스 및 테이블 초기화
def init_db():
    conn = sqlite3.connect('synotech_leads.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS leads 
                 (id INTEGER PRIMARY KEY, name TEXT, company TEXT, 
                  mobile TEXT, email TEXT, reg_date TEXT)''')
    conn.commit()
    conn.close()

# 고객 정보 저장 함수
def save_lead(name, company, mobile, email):
    conn = sqlite3.connect('synotech_leads.db')
    c = conn.cursor()
    c.execute("INSERT INTO leads (name, company, mobile, email, reg_date) VALUES (?, ?, ?, ?, ?)",
              (name, company, mobile, email, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

# 저장된 데이터 불러오기 (관리자용)
def get_leads():
    conn = sqlite3.connect('synotech_leads.db')
    # pandas를 이용해 DB를 표(DataFrame) 형태로 가져옵니다.
    df = pd.read_sql_query("SELECT * FROM leads ORDER BY reg_date DESC", conn)
    conn.close()
    return df