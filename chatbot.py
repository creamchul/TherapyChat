import os
import openai
import streamlit as st
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# OpenAI API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")

# 감정 목록
EMOTIONS = {
    "기쁨": "행복하고 즐거운 상태",
    "슬픔": "마음이 아프고 우울한 상태",
    "분노": "화가 나고 짜증이 나는 상태",
    "불안": "걱정이 많고 초조한 상태",
    "스트레스": "압박감과 중압감을 느끼는 상태",
    "외로움": "혼자라고 느끼는 상태",
    "후회": "과거의 선택이나 행동에 대해 아쉬움을 느끼는 상태",
    "좌절": "목표 달성에 실패하고 실망한 상태",
    "혼란": "명확한 방향이나 생각을 잡지 못하는 상태",
    "감사": "고마움을 느끼는 상태"
}

def get_system_prompt(emotion=None):
    """
    시스템 프롬프트를 생성합니다.
    emotion: 사용자가 선택한 감정
    """
    base_prompt = """
    당신은 감정 치유를 도와주는 공감적이고 따뜻한 상담사입니다. 
    사용자의 감정과 상황에 공감하고, 이해하며, 적절한 위로와 조언을 제공해주세요.
    대화는 한국어로 진행합니다.
    
    지켜야 할 원칙:
    1. 항상 공감하고 경청하는 태도를 보여주세요.
    2. 사용자의 감정을 인정하고 존중해주세요.
    3. 간결하고 명확하게 대화하세요.
    4. 판단하지 말고 이해하려고 노력하세요.
    5. 필요한 경우 전문적인 도움을 권유하세요.
    """
    
    if emotion:
        emotion_context = f"사용자는 현재 '{emotion}' 감정을 느끼고 있습니다. {EMOTIONS.get(emotion, '')}에 대한 이해와 공감이 필요합니다."
        return base_prompt + "\n\n" + emotion_context
    
    return base_prompt

def get_ai_response(messages):
    """
    OpenAI API를 사용하여 AI 응답을 생성합니다.
    """
    try:
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=1000
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"AI 응답 생성 중 오류가 발생했습니다: {e}")
        return "죄송합니다. 응답을 생성하는 중에 문제가 발생했습니다. 잠시 후 다시 시도해주세요."

def initialize_chat_history():
    """
    채팅 기록을 초기화합니다.
    """
    if "messages" not in st.session_state:
        st.session_state.messages = []

def add_message(role, content):
    """
    메시지를 채팅 기록에 추가합니다.
    """
    st.session_state.messages.append({"role": role, "content": content})

def display_chat_history():
    """
    채팅 기록을 표시합니다.
    """
    for message in st.session_state.messages:
        if message["role"] == "user":
            st.chat_message("user").write(message["content"])
        else:
            st.chat_message("assistant").write(message["content"])

def start_new_chat(emotion=None):
    """
    새 채팅을 시작합니다.
    """
    st.session_state.messages = []
    system_prompt = get_system_prompt(emotion)
    st.session_state.messages.append({"role": "system", "content": system_prompt})
    
    # 감정에 따른 인사말 설정
    if emotion:
        greeting_message = f"안녕하세요. 오늘 '{emotion}'을(를) 느끼고 계시는군요. 어떤 일이 있으셨나요? 저에게 편하게 말씀해주세요."
    else:
        greeting_message = "안녕하세요. 오늘은 어떤 감정을 느끼고 계신가요? 저에게 편하게 말씀해주세요."
        
    add_message("assistant", greeting_message)
    return greeting_message

def analyze_emotion(text):
    """
    텍스트에서 감정을 분석합니다.
    """
    try:
        messages = [
            {"role": "system", "content": "당신은 텍스트에서 감정을 분석하는 전문가입니다. 주어진 텍스트에서 주요 감정을 파악하여 '기쁨', '슬픔', '분노', '불안', '스트레스', '외로움', '후회', '좌절', '혼란', '감사' 중 하나만 선택하여 응답하세요. 다른 말은 덧붙이지 말고 감정 단어 하나만 응답하세요."},
            {"role": "user", "content": text}
        ]
        
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.3,
            max_tokens=50
        )
        
        detected_emotion = response.choices[0].message.content.strip()
        
        # 감정 목록에 있는지 확인
        for emotion in EMOTIONS.keys():
            if emotion in detected_emotion:
                return emotion
        
        return None
    except Exception as e:
        st.error(f"감정 분석 중 오류가 발생했습니다: {e}")
        return None 