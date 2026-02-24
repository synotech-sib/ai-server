# synobot.py

import os
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# =====================================================================
# [AI 지식 베이스 (Knowledge Base)]
# 추후 이 부분을 Vector DB(RAG)를 통해 문서를 검색해오는 로직으로 고도화합니다.
# 현재는 1단계로 Altris 핵심 양산 레퍼런스를 프롬프트에 직접 주입합니다.
# =====================================================================
ALTRIS_KNOWLEDGE_BASE = """
[Altris SIB 양산 설계 핵심 노하우 (Reference)]
1. 건조 조건 (PW 양극재): 수분 재흡수가 매우 빠르므로 반드시 진공(<1mBar) 상태에서 170~200°C로 최소 12~24시간 건조해야 합니다. 단면 코팅 시 컬링(Curling) 방지 처리가 필수입니다.
2. N/P Ratio: Na 금속 극판 석출(Plating) 방지를 위해 최소 1.15 (15% 마진) 이상으로 보수적으로 설계해야 합니다. 특히 1C 이상의 고율 충방전 시 떨어지는 음극 용량을 기준으로 N/P Ratio를 설정하십시오.
3. 슬러리 레시피 (표준 권장 사항):
   - 양극(Cathode): Fennac 93 : C65 3 : CMC 1 : SBR 3
   - 음극(Anode): Hard Carbon 94 : Graphite 2 : CMC 2 : SBR 2
4. 전해액 (Electrolyte): 하프셀(Coin-half) 테스트 시에는 1M NaPF6 in Diglyme을 권장하며, 양산용 풀셀(Full-cell)은 표준 카보네이트계(EC/PC/EMC/DEC)에 VC/DTD 첨가제를 사용합니다.
5. 수명(Cycle Life): Energy Cell은 C/2에서 12,000 사이클 이상, Power Cell(Pathfinder)은 3C/3C 가혹 조건에서 40,000 사이클 이상을 투사(Projection)합니다.
"""

# =====================================================================
# [AI 시스템 프롬프트 (Persona & Rules)]
# =====================================================================
SYSTEM_PROMPT = f"""
You are 'SynoBot', an expert SIB R&D engineer powered by OpenAI.
Answer questions accurately and professionally in Korean based on SIB knowledge.
- 반드시 SIB 수석 연구원(엔지니어)의 전문적인 브리핑 스타일로 작성하되, 사무적이고 정중한 '합쇼체(~입니다, ~합니다)'로 답변하십시오.
- 모든 답변은 도트 블릿('- ')을 사용하여 핵심을 명확히 나열하십시오.
- "아래는 분석 내용입니다", "다음은 데이터에 대한 브리핑입니다" 등과 같은 불필요한 서론이나 인사말은 절대 쓰지 말고, 곧바로 핵심 데이터 분석 본론부터 출력하십시오.
- 유저의 데이터나 질문을 [Altris SIB 양산 설계 핵심 노하우]와 비교하여 조언할 점이 있다면 적극적으로 가이드를 제시하십시오.

{ALTRIS_KNOWLEDGE_BASE}
"""

def get_openai_client(api_key):
    if OpenAI is None:
        raise ImportError("openai library is not installed.")
    return OpenAI(api_key=api_key)

def generate_auto_briefing(sim_result, api_key):
    """시뮬레이션 직후 자동 생성되는 진단 리포트 로직"""
    client = get_openai_client(api_key)
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT + f"\n\n[Current Simulation State]\n{sim_result}"},
        {"role": "user", "content": "입력된 시뮬레이션 데이터를 분석하여 핵심 엔지니어링 브리핑을 3~4줄로 명확히 작성해 주십시오. (서론 생략)"}
    ]
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.3  # 브리핑은 팩트 기반이므로 창의성(온도)을 낮춤
    )
    return response.choices[0].message.content

def generate_chat_reply(chat_history, sim_result, api_key):
    """유저와의 자유 대화(챗봇) 로직"""
    client = get_openai_client(api_key)
    messages = [{"role": "system", "content": SYSTEM_PROMPT + (f"\n\n[Current Simulation State]\n{sim_result}" if sim_result else "")}]
    
    # 누적된 대화 기록 주입
    for msg in chat_history:
        messages.append({"role": msg["role"], "content": msg["content"]})
        
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=messages,
        temperature=0.7  # 대화는 약간 유연하게 설정
    )
    return response.choices[0].message.content