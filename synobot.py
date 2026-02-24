# synobot.py
import os
import glob
import streamlit as st

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    import google.generativeai as genai
except ImportError:
    genai = None

# =====================================================================
# [글로벌 AI 시스템 프롬프트] - 언어 제한 해제
# =====================================================================
SYSTEM_PROMPT = """
You are 'SynoBot', an elite SIB R&D engineer and global technical advisor for SynoCore.
- 질문자가 사용하는 언어(한국어, 영어 등)에 맞춰 유연하게 대답하십시오.
- 한국어로 답변하더라도, 알트리스(Altris) 관련 기술 용어나 주요 지표(예: ICE, Cathode)는 영어 원문을 병기하여 전문성을 높이십시오.
- 불필요한 서론("아래는 분석 내용입니다" 등)은 생략하고, 도트 블릿('- ')을 사용하여 핵심을 명확히 나열하십시오.
- 제공된 [Retrieved Context(참고 문서)]가 있다면 반드시 그 사실을 기반으로 답변하고 출처를 명시하십시오.
"""

# =====================================================================
# [동적 지식 창고 연동] - SynoCore/SynoBot_db 폴더 읽기
# =====================================================================
TDB_DIR = "./SynoBot_db" 

def load_tdb_documents():
    context = ""
    if os.path.exists(TDB_DIR):
        txt_files = glob.glob(os.path.join(TDB_DIR, "**/*.txt"), recursive=True)
        for file_path in txt_files:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    file_name = os.path.basename(file_path)
                    context += f"\n\n--- [출처: {file_name}] ---\n"
                    context += f.read()
            except Exception as e:
                pass
    else:
        context = "지정된 SynoBot_db 폴더를 찾을 수 없거나 파일이 없습니다."
    return context

# =====================================================================
# [엔진 1] 제미나이(Gemini 1.5 Flash) 스트리밍
# =====================================================================
def get_gemini_response_stream(messages, sim_result, api_key):
    if genai is None:
        yield "⚠️ google-generativeai 라이브러리가 필요합니다."
        return
        
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=SYSTEM_PROMPT
    )
    
    history = []
    for msg in messages[:-1]:
        if msg["role"] == "system": continue 
        role = "user" if msg["role"] == "user" else "model"
        history.append({"role": role, "parts": [msg["content"]]})
        
    chat = model.start_chat(history=history)
    
    last_user_msg = ""
    for msg in reversed(messages):
        if msg["role"] == "user":
            last_user_msg = msg["content"]
            break
            
    retrieved_context = load_tdb_documents()
    full_prompt = f"[Retrieved Context]\n{retrieved_context}\n\n"
    if sim_result:
        full_prompt += f"[Current Simulation State]\n{sim_result}\n\n"
    full_prompt += f"User Question: {last_user_msg}"
    
    try:
        response = chat.send_message(full_prompt, stream=True)
        for chunk in response:
            yield chunk.text
    except Exception as e:
        yield f"\n⚠️ Gemini API 오류: {e}"

# =====================================================================
# [엔진 2] OpenAI(GPT-4o) 스트리밍 (비상용/정밀 추론)
# =====================================================================
def get_openai_response_stream(messages, sim_result, api_key):
    if OpenAI is None:
        yield "⚠️ openai 라이브러리가 필요합니다."
        return
        
    client = OpenAI(api_key=api_key)
    
    retrieved_context = load_tdb_documents()
    sys_content = SYSTEM_PROMPT + f"\n\n[Retrieved Context]\n{retrieved_context}"
    if sim_result:
        sys_content += f"\n\n[Current Simulation State]\n{sim_result}"
        
    sys_msg = [{"role": "system", "content": sys_content}]
    
    user_msgs = [m for m in messages if m["role"] != "system"]
    full_messages = sys_msg + user_msgs

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini", 
            messages=full_messages,
            temperature=0.3,
            stream=True
        )
        for chunk in response:
            if chunk.choices[0].delta.content is not None:
                yield chunk.choices[0].delta.content
    except Exception as e:
        yield f"\n⚠️ OpenAI API 오류: {e}"
        
# Auto Briefing (스트리밍 아님) - 시뮬레이션 직후 자동 분석용
def generate_auto_briefing(sim_result, engine_choice, openai_key, gemini_key):
    retrieved_context = load_tdb_documents()
    sys_content = SYSTEM_PROMPT + f"\n\n[Retrieved Context]\n{retrieved_context}\n\n[Current Simulation State]\n{sim_result}"
    user_prompt = "입력된 시뮬레이션 데이터를 분석하여 핵심 엔지니어링 브리핑을 3~4줄로 명확히 작성해 주십시오. (서론 생략)"
    
    if "Gemini" in engine_choice and genai is not None:
        try:
            genai.configure(api_key=gemini_key)
            model = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction=sys_content)
            response = model.generate_content(user_prompt)
            return response.text
        except Exception as e:
            return f"Gemini 자동 브리핑 오류: {e}"
    else:
        if OpenAI is None: return "OpenAI 라이브러리 없음"
        try:
            client = OpenAI(api_key=openai_key)
            messages = [{"role": "system", "content": sys_content}, {"role": "user", "content": user_prompt}]
            response = client.chat.completions.create(model="gpt-4o-mini", messages=messages, temperature=0.3)
            return response.choices[0].message.content
        except Exception as e:
            return f"OpenAI 자동 브리핑 오류: {e}"