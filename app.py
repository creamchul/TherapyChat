import streamlit as st
import os
import datetime
import time
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import seaborn as sns
from dotenv import load_dotenv
from auth import setup_auth, register_user, save_user_data, load_user_data, login, logout, hash_password, CONFIG_PATH
from chatbot import EMOTIONS, initialize_chat_history, display_chat_history, add_message, get_ai_response, start_new_chat, analyze_emotion, get_system_prompt
from pathlib import Path
import yaml
import numpy as np
from collections import Counter
import pytz

# 환경 변수 로드
load_dotenv()

# 한글 폰트 설정
plt.rcParams['font.family'] = 'Malgun Gothic'  # 윈도우 기본 한글 폰트
plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지

# 한국 시간대 설정
KST = pytz.timezone('Asia/Seoul')

# 페이지 설정
st.set_page_config(
    page_title="감정 치유 AI 챗봇",
    page_icon="❤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS 스타일 적용
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #4f8bf9;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #4f8bf9;
        margin-bottom: 1rem;
    }
    .emotion-button {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 10px;
        margin: 5px;
        text-align: center;
        cursor: pointer;
        transition: background-color 0.3s;
    }
    .emotion-button:hover {
        background-color: #e0e2e6;
    }
    .emotion-selected {
        background-color: #c0c2c6;
        font-weight: bold;
    }
    .chat-container {
        border-radius: 10px;
        padding: 20px;
        background-color: #f9f9f9;
        height: 400px;
        overflow-y: auto;
    }
    .stTextInput > div > div > input {
        border-radius: 20px;
    }
    .st-emotion-cache-1q7pdpx e1vs0wn31 {
        border-radius: 20px;
    }
    .emoji {
        font-size: 1.2rem;
        margin-right: 8px;
    }
    .chat-card {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        background-color: white;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        transition: transform 0.2s, box-shadow 0.2s;
        position: relative;
        z-index: 1;
        cursor: pointer;
    }
    .chat-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        background-color: #f9f9ff;
        border-color: #6a89cc;
    }
    .chat-card:after {
        content: "›";
        position: absolute;
        right: 15px;
        top: 50%;
        transform: translateY(-50%);
        font-size: 24px;
        color: #6a89cc;
        opacity: 0;
        transition: opacity 0.2s;
    }
    .chat-card:hover:after {
        opacity: 1;
    }
    /* Streamlit 버튼 스타일링 - 보이지 않지만 클릭 가능하게 */
    div.chat-history-card div.stButton {
        position: absolute;
        top: 0;
        left: 0;
        width: 100%;
        height: 100%;
        z-index: 2;
    }
    div.chat-history-card div.stButton > button {
        position: absolute;
        top: 0;
        left: 0;
        width: 100% !important;
        height: 100% !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: transparent !important;
        opacity: 0 !important;
    }
    .chat-card-header {
        border-bottom: 1px solid #f0f0f0;
        padding-bottom: 10px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
    }
    .chat-card-emotion {
        font-weight: bold;
        color: #4f8bf9;
    }
    .chat-card-date {
        color: #888;
        font-size: 0.9rem;
    }
    .chat-card-preview {
        color: #555;
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
    }
    .filter-section {
        background-color: #f9f9f9;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 20px;
    }
    .filter-title {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .filter-item {
        margin-bottom: 5px;
    }
    .action-button {
        border-radius: 20px;
        padding: 10px 15px;
        font-weight: bold;
        transition: all 0.3s;
    }
    .icon-button {
        display: flex;
        justify-content: center;
        align-items: center;
        width: 36px;
        height: 36px;
        border-radius: 50%;
        font-size: 1.2rem;
        cursor: pointer;
        transition: background-color 0.3s;
    }
    .view-button {
        background-color: #f0f2f6;
        color: #4f8bf9;
    }
    .view-button:hover {
        background-color: #e0e2e6;
    }
    .delete-button {
        background-color: #ffebee;
        color: #f44336;
    }
    .delete-button:hover {
        background-color: #ffcdd2;
    }
    .filter-badge {
        display: inline-block;
        background-color: #e8f0fe;
        color: #4f8bf9;
        border-radius: 16px;
        padding: 5px 10px;
        margin-right: 5px;
        margin-bottom: 5px;
        font-size: 0.85rem;
    }
    /* 날짜 선택 입력 필드 스타일 개선 */
    .stDateInput > div > div > input {
        border-radius: 8px;
    }
    /* 로그인 및 회원가입 버튼 스타일 */
    div.auth-container button {
        display: block !important;
        opacity: 1 !important;
        position: relative !important;
        background-color: #6a89cc !important;
        color: white !important;
        border-radius: 5px !important;
        border: none !important;
        padding: 0.5rem 1rem !important;
        margin: 0.5rem 0 !important;
        width: auto !important;
        height: auto !important;
        font-weight: 500 !important;
        text-align: center !important;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1) !important;
    }
    div.auth-container button:hover {
        background-color: #5679c1 !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.15) !important;
    }
    /* 특정 스타일 적용을 위한 클래스 */
    .login-button {
        display: block !important;
        width: 100% !important;
        background-color: #6a89cc !important;
        color: white !important;
        border-radius: 4px !important;
        border: none !important;
        padding: 0.5rem !important;
        margin-top: 1rem !important;
        font-weight: 500 !important;
        cursor: pointer !important;
    }
    .login-button:hover {
        background-color: #5679c1 !important;
    }
</style>
""", unsafe_allow_html=True)

# 인증 정보 설정
credentials = setup_auth()

# 감정 아이콘 매핑
EMOTION_ICONS = {
    "기쁨": "😊",
    "슬픔": "😢",
    "분노": "😠",
    "불안": "😰",
    "스트레스": "😫",
    "외로움": "😔",
    "후회": "😞",
    "좌절": "😩",
    "혼란": "😕",
    "감사": "🙏"
}

# 세션 상태 초기화
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'selected_emotion' not in st.session_state:
    st.session_state.selected_emotion = None
if 'chat_started' not in st.session_state:
    st.session_state.chat_started = False
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = "로그인"
if 'active_page' not in st.session_state:
    st.session_state.active_page = "chat"
if 'api_key' not in st.session_state:
    st.session_state.api_key = os.getenv("OPENAI_API_KEY", "")
if 'selected_chat_id' not in st.session_state:
    st.session_state.selected_chat_id = None

# 현재 채팅 저장 함수
def save_current_chat():
    if 'messages' in st.session_state and len(st.session_state.messages) > 1:
        chat_messages = [msg for msg in st.session_state.messages if msg["role"] != "system"]
        if not chat_messages:
            return False
            
        # 사용자가 입력한 메시지가 있는지 확인 (어시스턴트의 인사말만 있는 경우는 제외)
        has_user_message = False
        for msg in chat_messages:
            if msg["role"] == "user":
                has_user_message = True
                break
                
        # 사용자 메시지가 없으면 저장하지 않음
        if not has_user_message:
            return False
            
        # 감정 값이 없으면 저장하지 않음
        if not st.session_state.selected_emotion:
            return False
            
        # 기존 채팅 세션 리스트 확인
        if 'chat_sessions' not in st.session_state.user_data:
            st.session_state.user_data['chat_sessions'] = []
            
        # 현재 채팅의 ID 확인 또는 생성
        if 'current_chat_id' not in st.session_state:
            # 채팅 세션 정보 생성
            timestamp = datetime.datetime.now().isoformat()
            st.session_state.current_chat_id = f"chat_{timestamp}"
            
        chat_id = st.session_state.current_chat_id
        
        # 미리보기 텍스트로 사용자 메시지 사용 (없으면 어시스턴트 메시지)
        chat_preview = "새로운 대화"
        for msg in chat_messages:
            if msg["role"] == "user":
                chat_preview = msg["content"]
                break
                
        # 채팅 세션 정보 구성
        chat_session = {
            "id": chat_id,
            "date": datetime.datetime.now().isoformat(),  # 마지막 수정 시간으로 업데이트
            "emotion": st.session_state.selected_emotion,
            "preview": chat_preview,
            "messages": chat_messages
        }
        
        # 기존 채팅이 있는지 확인하고 업데이트하거나 새로 추가
        existing_chat_index = None
        for i, chat in enumerate(st.session_state.user_data['chat_sessions']):
            if chat['id'] == chat_id:
                existing_chat_index = i
                break
                
        if existing_chat_index is not None:
            # 기존 채팅 업데이트
            st.session_state.user_data['chat_sessions'][existing_chat_index] = chat_session
        else:
            # 새 채팅 추가
            st.session_state.user_data['chat_sessions'].append(chat_session)
        
        # 사용자 데이터 저장
        save_user_data(st.session_state.username, st.session_state.user_data)
        return True
    return False

# 자동 저장 함수
def auto_save():
    if (st.session_state.logged_in and 
        'user_data' in st.session_state and 
        'username' in st.session_state and
        'selected_emotion' in st.session_state and 
        st.session_state.selected_emotion):
        if 'messages' in st.session_state and len(st.session_state.messages) > 1:
            save_current_chat()

# 마지막 저장 시간 추적
if 'last_save_time' not in st.session_state:
    st.session_state.last_save_time = time.time()

# 주기적으로 저장 (5분마다)
current_time = time.time()
if (current_time - st.session_state.last_save_time > 300 and  # 300초 = 5분
    st.session_state.get('logged_in', False) and
    st.session_state.get('selected_emotion')):
    auto_save()
    st.session_state.last_save_time = current_time

# 사이드바 - 로그인/로그아웃
with st.sidebar:
    st.markdown("<h2 class='sub-header'>사용자 인증</h2>", unsafe_allow_html=True)
    
    # API 키 설정
    if st.session_state.logged_in:
        with st.expander("OpenAI API 키 설정"):
            api_key = st.text_input("OpenAI API 키", 
                                    value=st.session_state.api_key,
                                    type="password",
                                    key="api_key_input")
            if st.button("저장", key="save_api_key"):
                st.session_state.api_key = api_key
                os.environ["OPENAI_API_KEY"] = api_key
                st.success("API 키가 저장되었습니다!")
    
    if not st.session_state.logged_in:
        # 탭 선택
        tab_options = ["로그인", "회원가입"]
        selected_tab = st.radio("", tab_options, index=tab_options.index(st.session_state.active_tab))
        st.session_state.active_tab = selected_tab
        
        if selected_tab == "로그인":
            st.subheader("로그인")
            try:
                # 로그인 폼
                username = st.text_input("사용자 이름", key="login_username")
                password = st.text_input("비밀번호", type="password", key="login_password")
                
                # 로그인 버튼
                login_button = st.button("로그인", type="primary", key="login_btn", use_container_width=True)
                
                if login_button:
                    success, name = login(credentials, username, password)
                    if success:
                        st.session_state.logged_in = True
                        st.session_state.username = username
                        st.success(f"환영합니다, {name}님!")
                        
                        # 사용자 데이터 로드
                        st.session_state.user_data = load_user_data(username)
                        
                        # 현재 채팅 ID 초기화
                        if 'current_chat_id' in st.session_state:
                            del st.session_state.current_chat_id
                        
                        # 채팅 초기화
                        initialize_chat_history()
                        st.rerun()
                    else:
                        st.error("사용자 이름 또는 비밀번호가 잘못되었습니다.")
            except Exception as e:
                st.error(f"로그인 중 오류가 발생했습니다: {e}")

            # 회원가입으로 이동 버튼
            st.markdown("---")
            if st.button("계정이 없으신가요? 회원가입", type="secondary", key="goto_signup", use_container_width=True):
                st.session_state.active_tab = "회원가입"
                st.rerun()
        elif selected_tab == "회원가입":
            st.subheader("회원가입")
            try:
                # 회원가입 폼
                username = st.text_input("사용자 이름", key="signup_username")
                name = st.text_input("이름", key="signup_name")
                email = st.text_input("이메일", key="signup_email")
                password = st.text_input("비밀번호", type="password", key="signup_password")
                password_confirm = st.text_input("비밀번호 확인", type="password", key="signup_password_confirm")
                
                # 회원가입 버튼
                signup_button = st.button("회원가입", type="primary", key="signup_btn", use_container_width=True)
                
                if signup_button:
                    # 입력 검증
                    if not username or not name or not password:
                        st.error("필수 항목을 모두 입력해주세요.")
                    elif password != password_confirm:
                        st.error("비밀번호가 일치하지 않습니다.")
                    elif username in credentials['usernames']:
                        st.error("이미 존재하는 사용자 이름입니다.")
                    else:
                        # 새 사용자 추가
                        try:
                            # 설정 파일 로드
                            config_file = Path(CONFIG_PATH)
                            
                            # 새 사용자 추가
                            hashed_password = hash_password(password)
                            credentials['usernames'][username] = {
                                'name': name,
                                'password': hashed_password,
                                'email': email
                            }
                            
                            # 설정 파일 저장
                            with open(config_file, 'w') as file:
                                config = {
                                    'credentials': credentials,
                                    'cookie': {
                                        'expiry_days': 30
                                    }
                                }
                                yaml.dump(config, file, default_flow_style=False)
                                
                            # 사용자 데이터 파일 초기화
                            initial_data = {"chat_history": [], "emotions": [], "chat_sessions": []}
                            save_user_data(username, initial_data)
                            
                            st.success("계정이 생성되었습니다. 로그인해 주세요.")
                            
                            # 세션 상태 업데이트
                            st.session_state.active_tab = "로그인"
                            st.rerun()
                        except Exception as e:
                            st.error(f"회원가입 중 오류가 발생했습니다: {e}")
            except Exception as e:
                st.error(f"회원가입 중 오류가 발생했습니다: {e}")
            
            # 로그인으로 이동 버튼
            st.markdown("---")
            if st.button("이미 계정이 있으신가요? 로그인", type="secondary", key="goto_login", use_container_width=True):
                st.session_state.active_tab = "로그인"
                st.rerun()
    else:
        st.subheader(f"사용자: {st.session_state.username}")
        
        # 네비게이션 메뉴
        st.markdown("### 메뉴")
        if st.button("💬 채팅", key="nav_chat", use_container_width=True):
            st.session_state.active_page = "chat"
            st.session_state.selected_chat_id = None
            st.rerun()
            
        if st.button("📋 채팅 기록", key="nav_history", use_container_width=True):
            # 현재 채팅 저장 (감정 값이 있는 경우에만)
            if st.session_state.selected_emotion:
                auto_save()
            st.session_state.active_page = "history"
            st.rerun()
            
        if st.button("📊 감정 분석", key="nav_analysis", use_container_width=True):
            # 현재 채팅 저장 (감정 값이 있는 경우에만)
            if st.session_state.selected_emotion:
                auto_save()
            st.session_state.active_page = "analysis"
            st.rerun()
            
        st.markdown("---")
        if st.button("로그아웃", key="logout_button"):
            # 사용자 데이터 저장
            if 'messages' in st.session_state:
                if 'user_data' not in st.session_state:
                    st.session_state.user_data = {"chat_history": [], "chat_sessions": []}
                
                # 활성화된 채팅이 있으면 저장 (selected_emotion이 있을 때만)
                if 'messages' in st.session_state and len(st.session_state.messages) > 1 and st.session_state.selected_emotion:
                    save_current_chat()
                
                save_user_data(st.session_state.username, st.session_state.user_data)
            
            # 로그아웃 처리
            try:
                logout()
                st.session_state.active_tab = "로그인"
                st.rerun()
            except Exception as e:
                st.error(f"로그아웃 중 오류가 발생했습니다: {e}")

# 메인 컨텐츠
st.markdown("<h1 class='main-header'>감정 치유 AI 챗봇</h1>", unsafe_allow_html=True)

if not st.session_state.logged_in:
    # 로그인하지 않았을 때는 간단한 안내 메시지만 표시
    st.info("왼쪽 사이드바에서 로그인해주세요.")
else:
    # 선택된 페이지에 따라 다른 내용 표시
    if st.session_state.active_page == "chat":
        # 감정 선택 페이지 또는 채팅 페이지 표시
        if not st.session_state.selected_emotion:
            st.markdown("<h2 class='sub-header'>감정 선택</h2>", unsafe_allow_html=True)
            st.write("현재 느끼는 감정을 선택해주세요:")
            
            # 감정 버튼 그리드 생성
            col1, col2 = st.columns(2)
            
            for i, (emotion, description) in enumerate(EMOTIONS.items()):
                col = col1 if i % 2 == 0 else col2
                icon = EMOTION_ICONS.get(emotion, "")
                
                if col.button(f"{icon} {emotion}", 
                             key=f"emotion_{emotion}", 
                             help=description,
                             use_container_width=True):
                    # 이전 채팅이 있다면 저장
                    if 'messages' in st.session_state and len(st.session_state.messages) > 1:
                        save_current_chat()
                        
                    # 새로운 채팅 ID 생성
                    timestamp = datetime.datetime.now().isoformat()
                    st.session_state.current_chat_id = f"chat_{timestamp}"
                    
                    # displayed_messages 초기화
                    if 'displayed_messages' in st.session_state:
                        del st.session_state.displayed_messages
                    
                    st.session_state.selected_emotion = emotion
                    st.session_state.chat_started = True
                    start_new_chat(emotion)
                    st.rerun()
        else:
            # 감정이 선택된 경우
            st.markdown(f"<h2 class='sub-header'>선택한 감정: {EMOTION_ICONS.get(st.session_state.selected_emotion, '')} {st.session_state.selected_emotion}</h2>", unsafe_allow_html=True)
            
            # 감정 설명
            emotion_description = EMOTIONS.get(st.session_state.selected_emotion, "")
            st.write(f"**{emotion_description}**")
            
            # 채팅 인터페이스
            initialize_chat_history()
            display_chat_history()
            
            # 사용자 입력
            user_input = st.chat_input("메시지를 입력하세요...")
            if user_input:
                # API 키 확인
                if not st.session_state.api_key:
                    st.warning("OpenAI API 키를 입력해주세요. 왼쪽 사이드바의 'OpenAI API 키 설정'에서 설정할 수 있습니다.")
                    st.stop()
                    
                # 사용자 메시지 추가
                add_message("user", user_input)
                st.chat_message("user").write(user_input)
                
                # 채팅 기록에서 시스템 메시지를 제외한 메시지 컨텍스트 생성
                messages_for_api = [msg for msg in st.session_state.messages if msg["role"] != "assistant" or st.session_state.messages.index(msg) == 0]
                
                # API 키 설정
                os.environ["OPENAI_API_KEY"] = st.session_state.api_key
                
                # AI 응답 생성
                with st.spinner("응답 생성 중..."):
                    ai_response = get_ai_response(messages_for_api)
                
                # AI 메시지 추가
                add_message("assistant", ai_response)
                st.chat_message("assistant").write(ai_response)
                
                # 채팅 자동 저장
                save_current_chat()
            
            # 새 감정 선택 버튼
            if st.button("다른 감정 선택하기"):
                # 현재 채팅 저장 (감정 상태가 변경되기 전에 저장)
                save_current_chat()
                
                # 현재 채팅 ID 제거
                if 'current_chat_id' in st.session_state:
                    del st.session_state.current_chat_id
                
                # displayed_messages 초기화
                if 'displayed_messages' in st.session_state:
                    del st.session_state.displayed_messages
                
                # 상태 초기화 (저장 후에 초기화)
                st.session_state.selected_emotion = None
                st.session_state.chat_started = False
                
                st.rerun()
    
    elif st.session_state.active_page == "history":
        st.markdown("<h2 class='sub-header'>채팅 기록</h2>", unsafe_allow_html=True)
        
        # 채팅 기록이 없는 경우
        if 'user_data' not in st.session_state or 'chat_sessions' not in st.session_state.user_data or not st.session_state.user_data['chat_sessions']:
            st.info("저장된 채팅 기록이 없습니다.")
        else:
            # 채팅 기록이 있는 경우
            if st.session_state.selected_chat_id:
                # 선택된 채팅 세션 표시
                selected_chat = None
                selected_chat_index = None
                for i, chat in enumerate(st.session_state.user_data['chat_sessions']):
                    if chat['id'] == st.session_state.selected_chat_id:
                        selected_chat = chat
                        selected_chat_index = i
                        break
                
                if selected_chat:
                    # 뒤로가기 버튼과 삭제 버튼을 나란히 배치
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        if st.button("← 기록 목록으로 돌아가기"):
                            st.session_state.selected_chat_id = None
                            st.rerun()
                    
                    with col2:
                        # 삭제 확인 상태 확인
                        if 'confirm_delete_dialog' not in st.session_state:
                            st.session_state.confirm_delete_dialog = False
                            
                        if not st.session_state.confirm_delete_dialog:
                            if st.button("🗑️ 이 대화 삭제하기", type="primary", use_container_width=True):
                                st.session_state.confirm_delete_dialog = True
                                st.rerun()
                        else:
                            st.warning("정말 이 대화를 삭제하시겠습니까?")
                            conf_col1, conf_col2 = st.columns(2)
                            
                            with conf_col1:
                                if st.button("예, 삭제합니다", key="confirm_delete_yes"):
                                    # 선택된 채팅 삭제
                                    st.session_state.user_data['chat_sessions'].pop(selected_chat_index)
                                    save_user_data(st.session_state.username, st.session_state.user_data)
                                    st.session_state.selected_chat_id = None
                                    st.session_state.confirm_delete_dialog = False
                                    st.success("대화가 삭제되었습니다.")
                                    st.rerun()
                            
                            with conf_col2:
                                if st.button("아니오", key="confirm_delete_no"):
                                    st.session_state.confirm_delete_dialog = False
                                    st.rerun()
                    
                    # 채팅 세션 정보 표시
                    chat_date = datetime.datetime.fromisoformat(selected_chat['date']).strftime("%Y년 %m월 %d일 %H:%M")
                    emotion = selected_chat.get('emotion', '알 수 없음')
                    emotion_icon = EMOTION_ICONS.get(emotion, "")
                    
                    st.markdown(f"**날짜:** {chat_date}")
                    st.markdown(f"**감정:** {emotion_icon} {emotion}")
                    st.markdown("---")
                    
                    # 채팅 내용 표시
                    for msg in selected_chat['messages']:
                        role = msg.get('role', '')
                        content = msg.get('content', '')
                        
                        if role == 'user':
                            st.chat_message("user").write(content)
                        elif role == 'assistant':
                            st.chat_message("assistant").write(content)
                    
                    # 채팅 계속하기 버튼
                    if st.button("이 대화 계속하기"):
                        st.session_state.active_page = "chat"
                        st.session_state.selected_emotion = selected_chat.get('emotion', None)
                        st.session_state.chat_started = True
                        
                        # 기존 채팅 ID 사용
                        st.session_state.current_chat_id = selected_chat['id']
                        
                        # displayed_messages 초기화
                        if 'displayed_messages' in st.session_state:
                            del st.session_state.displayed_messages
                        
                        # 채팅 메시지 복원
                        st.session_state.messages = []
                        
                        # 시스템 메시지 추가
                        system_prompt = get_system_prompt(selected_chat.get('emotion', None))
                        st.session_state.messages.append({"role": "system", "content": system_prompt})
                        
                        # 대화 메시지 추가
                        for msg in selected_chat['messages']:
                            st.session_state.messages.append(msg)
                        
                        st.rerun()
                else:
                    st.error("선택한 채팅을 찾을 수 없습니다.")
                    st.session_state.selected_chat_id = None
            else:
                # 필터링 옵션 초기화
                if 'filter_emotion' not in st.session_state:
                    st.session_state.filter_emotion = []
                if 'filter_date_start' not in st.session_state:
                    st.session_state.filter_date_start = None
                if 'filter_date_end' not in st.session_state:
                    st.session_state.filter_date_end = None
                
                # 필터링 옵션 UI
                with st.expander("필터 옵션", expanded=False):
                    st.markdown("<div class='filter-section'>", unsafe_allow_html=True)
                    st.markdown("<div class='filter-title'>채팅 기록 필터링</div>", unsafe_allow_html=True)
                    
                    # 감정 필터
                    st.markdown("<div class='filter-item'><strong>감정 선택</strong></div>", unsafe_allow_html=True)
                    emotions_list = list(EMOTIONS.keys())
                    
                    # 감정 필터 UI를 더 효율적으로 표시
                    cols = st.columns(5)  # 한 행에 5개씩 표시
                    selected_emotions = []
                    
                    for i, emotion in enumerate(emotions_list):
                        col_idx = i % 5
                        emotion_icon = EMOTION_ICONS.get(emotion, "")
                        emotion_selected = cols[col_idx].checkbox(
                            f"{emotion_icon} {emotion}", 
                            value=emotion in st.session_state.filter_emotion,
                            key=f"filter_{emotion}"
                        )
                        if emotion_selected:
                            selected_emotions.append(emotion)
                    
                    st.session_state.filter_emotion = selected_emotions
                    
                    # 날짜 필터 (시작 및 종료 날짜)
                    st.markdown("<div class='filter-item'><strong>날짜 범위 선택</strong></div>", unsafe_allow_html=True)
                    
                    date_col1, date_col2 = st.columns(2)
                    
                    with date_col1:
                        start_date = st.date_input(
                            "시작 날짜", 
                            value=st.session_state.filter_date_start if st.session_state.filter_date_start else None,
                            format="YYYY-MM-DD"
                        )
                        if start_date:
                            st.session_state.filter_date_start = datetime.datetime.combine(start_date, datetime.time.min)
                        
                    with date_col2:
                        end_date = st.date_input(
                            "종료 날짜", 
                            value=st.session_state.filter_date_end if st.session_state.filter_date_end else None,
                            format="YYYY-MM-DD"
                        )
                        if end_date:
                            st.session_state.filter_date_end = datetime.datetime.combine(end_date, datetime.time.max)
                    
                    # 필터 초기화 버튼
                    if st.button("필터 초기화", type="secondary", use_container_width=True):
                        st.session_state.filter_emotion = []
                        st.session_state.filter_date_start = None
                        st.session_state.filter_date_end = None
                        st.rerun()
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                
                # 채팅 기록 목록 표시
                chat_sessions = st.session_state.user_data['chat_sessions']
                
                # 필터링 적용
                filtered_sessions = []
                for chat in chat_sessions:
                    # 감정 필터링
                    emotion_match = True
                    if st.session_state.filter_emotion:
                        chat_emotion = chat.get('emotion', '')
                        if chat_emotion not in st.session_state.filter_emotion:
                            emotion_match = False
                    
                    # 날짜 필터링
                    date_match = True
                    if st.session_state.filter_date_start or st.session_state.filter_date_end:
                        chat_date = datetime.datetime.fromisoformat(chat.get('date', ''))
                        
                        if st.session_state.filter_date_start and chat_date < st.session_state.filter_date_start:
                            date_match = False
                        
                        if st.session_state.filter_date_end and chat_date > st.session_state.filter_date_end:
                            date_match = False
                    
                    # 필터 조건에 맞는 경우만 추가
                    if emotion_match and date_match:
                        filtered_sessions.append(chat)
                
                # 필터링 결과 안내
                if st.session_state.filter_emotion or st.session_state.filter_date_start or st.session_state.filter_date_end:
                    st.markdown("<div style='margin-bottom: 15px;'>", unsafe_allow_html=True)
                    st.markdown("<strong>적용된 필터:</strong>", unsafe_allow_html=True)
                    
                    # 감정 필터 배지
                    if st.session_state.filter_emotion:
                        st.markdown("<div>", unsafe_allow_html=True)
                        for emotion in st.session_state.filter_emotion:
                            emotion_icon = EMOTION_ICONS.get(emotion, "")
                            st.markdown(f"<span class='filter-badge'>{emotion_icon} {emotion}</span>", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    # 날짜 필터 배지
                    if st.session_state.filter_date_start or st.session_state.filter_date_end:
                        st.markdown("<div>", unsafe_allow_html=True)
                        if st.session_state.filter_date_start:
                            start_date_str = st.session_state.filter_date_start.strftime("%Y-%m-%d")
                            st.markdown(f"<span class='filter-badge'>시작일: {start_date_str}</span>", unsafe_allow_html=True)
                        
                        if st.session_state.filter_date_end:
                            end_date_str = st.session_state.filter_date_end.strftime("%Y-%m-%d")
                            st.markdown(f"<span class='filter-badge'>종료일: {end_date_str}</span>", unsafe_allow_html=True)
                        st.markdown("</div>", unsafe_allow_html=True)
                    
                    st.markdown("</div>", unsafe_allow_html=True)
                    
                    if not filtered_sessions:
                        st.warning("필터 조건에 맞는 채팅 기록이 없습니다.")
                
                # 최신 순으로 정렬
                filtered_sessions.sort(key=lambda x: x.get('date', ''), reverse=True)
                
                # 결과 갯수 표시
                if filtered_sessions:
                    st.markdown(f"<div style='margin-bottom: 10px;'><strong>{len(filtered_sessions)}개</strong>의 대화 기록이 있습니다.</div>", unsafe_allow_html=True)
                
                # 필터링된 채팅 기록 표시
                for chat in filtered_sessions:
                    # 카드 컨테이너 (상대 위치로 설정)
                    card_container = st.container()
                    
                    with card_container:
                        # 로그인 버튼과 충돌하지 않도록 div에 특정 클래스 추가
                        st.markdown('<div class="chat-history-card">', unsafe_allow_html=True)
                        
                        # 카드 스타일 컨테이너
                        st.markdown(f"""
                        <div class="chat-card">
                            <div class="chat-card-header">
                                <span class="chat-card-emotion">{EMOTION_ICONS.get(chat.get('emotion', ''), '')} {chat.get('emotion', '알 수 없음')}</span>
                                <span class="chat-card-date">{datetime.datetime.fromisoformat(chat.get('date', '')).strftime("%Y년 %m월 %d일 %H:%M")}</span>
                            </div>
                            <div class="chat-card-preview">{chat.get('preview', '대화 내용 없음')[:100]}...</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                        # 카드 클릭 감지를 위한 버튼 (숨김)
                        card_clicked = st.button(
                            "보기",
                            key=f"chat_card_{chat['id']}"
                        )
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        if card_clicked:
                            st.session_state.selected_chat_id = chat['id']
                            st.rerun()

    elif st.session_state.active_page == "analysis":
        st.markdown("<h2 class='sub-header'>감정 분석</h2>", unsafe_allow_html=True)
        
        # 채팅 기록이 없는 경우
        if 'user_data' not in st.session_state or 'chat_sessions' not in st.session_state.user_data or not st.session_state.user_data['chat_sessions']:
            st.info("분석할 채팅 기록이 없습니다. 먼저 대화를 진행해주세요.")
        else:
            # 탭 설정
            tab1, tab2, tab3 = st.tabs(["감정 변화 그래프", "주간/월간 리포트", "감정 패턴 분석"])
            
            # 채팅 세션에서 감정 데이터 추출
            chat_sessions = st.session_state.user_data['chat_sessions']
            
            # 날짜와 감정 데이터 추출
            emotion_data = []
            for chat in chat_sessions:
                if 'date' in chat and 'emotion' in chat and chat['emotion']:
                    date = datetime.datetime.fromisoformat(chat['date'])
                    # UTC를 KST로 변환 (9시간 추가)
                    date = date.replace(tzinfo=pytz.UTC).astimezone(KST)
                    emotion_data.append({
                        'date': date,
                        'emotion': chat['emotion'],
                        'year': date.year,
                        'month': date.month,
                        'week': date.isocalendar()[1],
                        'day': date.day,
                    })
            
            if not emotion_data:
                st.warning("감정 데이터가 충분하지 않습니다. 더 많은 대화를 진행해주세요.")
            else:
                # 데이터프레임으로 변환
                df = pd.DataFrame(emotion_data)
                df = df.sort_values('date')
                
                with tab1:
                    st.subheader("시간에 따른 감정 변화")
                    
                    # 날짜 범위 선택
                    col1, col2 = st.columns(2)
                    with col1:
                        start_date = st.date_input(
                            "시작 날짜", 
                            value=df['date'].min().date(),
                            key="emotion_start_date"
                        )
                    with col2:
                        end_date = st.date_input(
                            "종료 날짜", 
                            value=df['date'].max().date(),
                            key="emotion_end_date"
                        )
                    
                    # 필터링
                    mask = (df['date'].dt.date >= start_date) & (df['date'].dt.date <= end_date)
                    filtered_df = df.loc[mask]
                    
                    if filtered_df.empty:
                        st.warning("선택한 날짜 범위에 데이터가 없습니다.")
                    else:
                        # 그래프 생성 - 크기 축소
                        fig, ax = plt.subplots(figsize=(8, 4))
                        
                        # 감정 카테고리 순서 정의
                        emotions_order = list(EMOTIONS.keys())
                        emotion_values = {e: i for i, e in enumerate(emotions_order)}
                        
                        # y축 값 변환
                        y_values = [emotion_values.get(e, 0) for e in filtered_df['emotion']]
                        
                        # 그래프 그리기
                        ax.plot(filtered_df['date'], y_values, 'o-', markersize=6)
                        
                        # 각 점에 감정 레이블 추가
                        for i, txt in enumerate(filtered_df['emotion']):
                            ax.annotate(f"{txt}", 
                                     (filtered_df['date'].iloc[i], y_values[i]),
                                     textcoords="offset points", 
                                     xytext=(0, 8), 
                                     ha='center',
                                     fontsize=8)
                        
                        # x축 날짜 포맷 설정
                        plt.gcf().autofmt_xdate()
                        
                        # y축 설정 - 감정 레이블
                        plt.yticks(range(len(emotions_order)), [f"{e}" for e in emotions_order], fontsize=8)
                        
                        # 그리드 및 레이블 추가
                        plt.grid(True, linestyle='--', alpha=0.7)
                        plt.title('감정 변화 추이', fontsize=12)
                        plt.xlabel('날짜', fontsize=10)
                        plt.ylabel('감정', fontsize=10)
                        
                        # 테마 스타일 설정
                        sns.set_style("whitegrid")
                        plt.tight_layout()
                        
                        # 그래프 표시
                        st.pyplot(fig)
                        
                        # 추가 분석 텍스트
                        most_common_emotion = filtered_df['emotion'].mode()[0]
                        st.markdown(f"**분석 기간 동안 가장 많이 느낀 감정:** {most_common_emotion}")
                
                with tab2:
                    st.subheader("주간/월간 감정 리포트")
                    
                    # 분석 기간 선택
                    report_type = st.radio(
                        "리포트 유형 선택",
                        ["주간", "월간"],
                        horizontal=True,
                        key="report_type"
                    )
                    
                    if report_type == "주간":
                        # 주간 데이터 그룹화
                        weekly_data = df.groupby(['year', 'week'])['emotion'].apply(list).reset_index()
                        weekly_data['period'] = weekly_data.apply(
                            lambda x: f"{x['year']}년 {x['week']}주차", axis=1)
                        weekly_data['count'] = weekly_data['emotion'].apply(len)
                        
                        # 기간 선택 (최근 4주 기본)
                        weeks = weekly_data['period'].unique()
                        selected_week = st.selectbox(
                            "분석할 주 선택",
                            weeks,
                            index=min(len(weeks)-1, 0),
                            key="selected_week"
                        )
                        
                        if selected_week:
                            # 선택한 주의 데이터
                            selected_data = weekly_data[weekly_data['period'] == selected_week]
                            
                            if not selected_data.empty:
                                emotions = selected_data.iloc[0]['emotion']
                                emotion_counts = Counter(emotions)
                                
                                # 원형 그래프로 시각화 - 크기 축소
                                fig, ax = plt.subplots(figsize=(6, 6))
                                
                                # 색상 설정
                                colors = plt.cm.tab10(np.arange(len(emotion_counts)))
                                
                                # 그래프 그리기
                                wedges, texts, autotexts = ax.pie(
                                    emotion_counts.values(), 
                                    labels=[f"{e}" for e in emotion_counts.keys()],
                                    autopct='%1.1f%%',
                                    colors=colors,
                                    startangle=90,
                                    textprops={'fontsize': 9}
                                )
                                
                                # 원형 그래프 가운데 원 추가해서 도넛 차트로 변경
                                centre_circle = plt.Circle((0, 0), 0.70, fc='white')
                                fig.gca().add_artist(centre_circle)
                                
                                # 폰트 크기 조정
                                plt.setp(autotexts, size=9, weight="bold")
                                
                                # 제목 추가
                                ax.set_title(f"{selected_week} 감정 분포", pad=15, fontsize=12)
                                plt.tight_layout()
                                
                                # 도넛 차트 표시
                                st.pyplot(fig)
                                
                                # 요약 통계
                                st.markdown("### 주간 감정 요약")
                                st.markdown(f"- **총 대화 수:** {sum(emotion_counts.values())}회")
                                st.markdown(f"- **가장 많이 느낀 감정:** {max(emotion_counts, key=emotion_counts.get)} ({emotion_counts[max(emotion_counts, key=emotion_counts.get)]}회)")
                                
                                # 감정 빈도 표시
                                st.markdown("### 감정 빈도")
                                for emotion, count in sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True):
                                    st.markdown(f"- **{emotion}:** {count}회")
                            else:
                                st.warning("선택한 주에 데이터가 없습니다.")
                    else:  # 월간 리포트
                        # 월간 데이터 그룹화
                        monthly_data = df.groupby(['year', 'month'])['emotion'].apply(list).reset_index()
                        monthly_data['period'] = monthly_data.apply(
                            lambda x: f"{x['year']}년 {x['month']}월", axis=1)
                        monthly_data['count'] = monthly_data['emotion'].apply(len)
                        
                        # 기간 선택
                        months = monthly_data['period'].unique()
                        selected_month = st.selectbox(
                            "분석할 월 선택",
                            months,
                            index=min(len(months)-1, 0),
                            key="selected_month"
                        )
                        
                        if selected_month:
                            # 선택한 월의 데이터
                            selected_data = monthly_data[monthly_data['period'] == selected_month]
                            
                            if not selected_data.empty:
                                emotions = selected_data.iloc[0]['emotion']
                                emotion_counts = Counter(emotions)
                                
                                # 세로 막대 그래프로 시각화 - 크기 축소
                                fig, ax = plt.subplots(figsize=(7, 4))
                                
                                # 감정 순서대로 정렬
                                ordered_emotions = [e for e in EMOTIONS.keys() if e in emotion_counts]
                                ordered_counts = [emotion_counts[e] for e in ordered_emotions]
                                
                                # 그래프 그리기
                                bars = ax.bar(
                                    range(len(ordered_emotions)), 
                                    ordered_counts, 
                                    color=plt.cm.tab10(np.arange(len(ordered_emotions)))
                                )
                                
                                # 축 설정
                                ax.set_xticks(range(len(ordered_emotions)))
                                ax.set_xticklabels([f"{e}" for e in ordered_emotions], rotation=45, ha='right', fontsize=8)
                                
                                # 막대 위에 숫자 표시
                                for bar in bars:
                                    height = bar.get_height()
                                    ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                                            f'{int(height)}',
                                            ha='center', va='bottom', fontsize=8)
                                
                                # 제목과 레이블 설정
                                ax.set_title(f"{selected_month} 감정 발생 빈도", pad=10, fontsize=12)
                                ax.set_ylabel('빈도', fontsize=10)
                                
                                # 여백 조정
                                plt.tight_layout()
                                
                                # 그래프 표시
                                st.pyplot(fig)
                                
                                # 요약 통계
                                st.markdown("### 월간 감정 요약")
                                st.markdown(f"- **총 대화 수:** {sum(emotion_counts.values())}회")
                                st.markdown(f"- **가장 많이 느낀 감정:** {max(emotion_counts, key=emotion_counts.get)} ({emotion_counts[max(emotion_counts, key=emotion_counts.get)]}회)")
                                
                                # 감정 빈도 표시
                                st.markdown("### 감정 빈도")
                                for emotion, count in sorted(emotion_counts.items(), key=lambda x: x[1], reverse=True):
                                    st.markdown(f"- **{emotion}:** {count}회")
                                
                                # 추가 분석
                                if len(emotion_counts) > 1:
                                    diversity = (len(emotion_counts) / len(EMOTIONS)) * 100
                                    st.markdown(f"- **감정 다양성:** {diversity:.1f}% (전체 감정 중 {len(emotion_counts)}개 경험)")
                            else:
                                st.warning("선택한 월에 데이터가 없습니다.")
                
                with tab3:
                    st.subheader("감정 패턴 분석")
                    
                    # 전체 감정 분포 파이 차트
                    emotion_overall = df['emotion'].value_counts()
                    
                    # 레이아웃 조정 - 파이 차트와 설명을 더 작게 표시
                    col1, col2 = st.columns([1, 1])
                    
                    with col1:
                        # 파이 차트 생성 - 크기 축소
                        fig, ax = plt.subplots(figsize=(5, 5))
                        
                        # 색상 설정
                        colors = plt.cm.tab10(np.arange(len(emotion_overall)))
                        
                        # 차트 그리기
                        wedges, texts, autotexts = ax.pie(
                            emotion_overall.values, 
                            labels=[f"{e}" for e in emotion_overall.index],
                            autopct='%1.1f%%',
                            colors=colors,
                            startangle=90,
                            textprops={'fontsize': 8}
                        )
                        
                        # 제목 추가
                        ax.set_title("전체 감정 분포", fontsize=12)
                        
                        # 폰트 크기 조정
                        plt.setp(autotexts, size=8, weight="bold")
                        plt.tight_layout()
                        
                        # 그래프 표시
                        st.pyplot(fig)
                    
                    with col2:
                        st.markdown("### 가장 자주 느끼는 감정")
                        
                        # 가장 많은 순서대로 정렬
                        for emotion, count in emotion_overall.items():
                            percentage = (count / emotion_overall.sum()) * 100
                            st.markdown(f"- **{emotion}:** {count}회 ({percentage:.1f}%)")
                    
                    # 시간대별 감정 분석
                    st.markdown("### 시간대별 감정 패턴")
                    
                    # 시간대 추가
                    df['hour'] = df['date'].dt.hour
                    df['time_category'] = pd.cut(
                        df['hour'],
                        bins=[0, 6, 12, 18, 24],
                        labels=['새벽 (0-6시)', '오전 (6-12시)', '오후 (12-18시)', '저녁 (18-24시)'],
                        include_lowest=True
                    )
                    
                    # 시간대별 감정 분포
                    time_emotion = pd.crosstab(df['time_category'], df['emotion'])
                    
                    # 히트맵 생성 - 크기 축소
                    fig, ax = plt.subplots(figsize=(8, 4))
                    sns.heatmap(
                        time_emotion, 
                        annot=True, 
                        fmt='d', 
                        cmap='Blues',
                        linewidths=.5,
                        ax=ax,
                        annot_kws={"size": 8}
                    )
                    
                    # 제목 및 레이블 설정
                    ax.set_title('시간대별 감정 발생 빈도', fontsize=12, pad=10)
                    ax.set_xlabel('감정', fontsize=10)
                    ax.set_ylabel('시간대', fontsize=10)
                    plt.tight_layout()
                    
                    # 그래프 표시
                    st.pyplot(fig)
                    
                    # 패턴 분석 문장 생성
                    try:
                        most_common_time = time_emotion.sum(axis=1).idxmax()
                        most_common_emotion_overall = emotion_overall.idxmax()
                        
                        # 시간대별 가장 많은 감정
                        time_most_emotions = {}
                        for time_cat in time_emotion.index:
                            if not time_emotion.loc[time_cat].sum() == 0:
                                time_most_emotions[time_cat] = time_emotion.loc[time_cat].idxmax()
                        
                        # 분석 결과 텍스트 표시 - 더 간결하게
                        st.markdown("### 감정 패턴 인사이트")
                        
                        # 통계 요약을 컴팩트하게 표시
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**주요 대화 시간대:** {most_common_time}")
                            st.markdown(f"**주요 감정:** {most_common_emotion_overall}")
                        
                        with col2:
                            if len(df) > 3:
                                recent_emotions = df.sort_values('date').tail(3)['emotion'].tolist()
                                if len(set(recent_emotions)) == 1:
                                    st.markdown(f"**최근 감정:** {recent_emotions[0]}")
                                else:
                                    st.markdown(f"**최근 감정 변화:** {', '.join(recent_emotions)}")
                        
                        # 시간대별 주요 감정을 표 형태로 표시
                        st.markdown("#### 시간대별 주요 감정")
                        time_emotion_data = {"시간대": [], "주요 감정": []}
                        for time_cat, emotion in time_most_emotions.items():
                            time_emotion_data["시간대"].append(time_cat)
                            time_emotion_data["주요 감정"].append(emotion)
                        
                        time_emotion_df = pd.DataFrame(time_emotion_data)
                        st.dataframe(time_emotion_df, hide_index=True, use_container_width=True)
                        
                    except:
                        st.markdown("데이터가 충분하지 않아 상세 분석을 생성할 수 없습니다.")
                    
                    # 팁 제공
                    with st.expander("감정 관리 팁"):
                        emotion_tips = {
                            "기쁨": "긍정적인 감정을 유지하고 다른 사람과 나누세요. 감사 일기를 작성하면 기쁨을 오래 간직할 수 있습니다.",
                            "슬픔": "감정을 억누르지 말고 표현하세요. 가까운 사람과 대화하거나 글로 감정을 표현해보세요.",
                            "분노": "깊게 호흡하고 10까지 세어보세요. 분노를 느끼는 상황에서 잠시 벗어나 진정할 시간을 가지세요.",
                            "불안": "마음챙김 명상을 통해 현재에 집중하세요. 불안한 생각을 종이에 적어보면 객관화하는 데 도움이 됩니다.",
                            "스트레스": "가벼운 운동이나 취미 활동으로 기분 전환하세요. 충분한 휴식과 수면도 중요합니다.",
                            "외로움": "온라인 커뮤니티나 모임에 참여해보세요. 자원봉사 활동도 사회적 연결감을 높이는 데 도움이 됩니다.",
                            "후회": "과거에서 배울 점을 찾고 미래에 적용하세요. 자기 용서도 중요한 과정입니다.",
                            "좌절": "작은 목표부터 설정하고 성취해보세요. 성공 경험이 쌓이면 자신감이 생깁니다.",
                            "혼란": "생각을 정리하기 위해 마인드맵이나 일기를 작성해보세요. 필요하다면 전문가의 조언을 구하세요.",
                            "감사": "감사한 일들을 매일 기록하는 습관을 들이세요. 감사함이 더 많은 긍정적인 경험을 끌어당깁니다."
                        }
                        
                        if not emotion_overall.empty:
                            most_common = emotion_overall.idxmax()
                            st.markdown(f"### {EMOTION_ICONS.get(most_common, '')} {most_common} 감정을 위한 팁")
                            st.markdown(emotion_tips.get(most_common, "감정을 관리하기 위해 규칙적인 생활과 자기 돌봄을 실천하세요."))
                        
                        st.markdown("### 일반적인 감정 관리 전략")
                        st.markdown("""
                        1. **규칙적인 운동**: 신체 활동은 좋은 기분을 촉진하는 호르몬을 분비합니다.
                        2. **충분한 수면**: 수면 부족은 감정 조절 능력을 저하시킵니다.
                        3. **균형 잡힌 식사**: 영양소가 풍부한 식단은 뇌 기능과 기분에 영향을 줍니다.
                        4. **명상과 호흡법**: 스트레스 감소와 현재 순간에 집중하는 데 도움이 됩니다.
                        5. **사회적 연결**: 친구, 가족과의 소통은 정서적 지원을 제공합니다.
                        """)
                        
                        st.markdown(f"감정 관련 도움이 필요하시면 언제든지 AI 챗봇과 대화하거나 전문가와 상담하세요.")
                    
                    # 추천 사항
                    st.markdown("### 개인 맞춤 추천")
                    
                    if not emotion_overall.empty:
                        dominant_emotions = emotion_overall.nlargest(2).index.tolist()
                        
                        # 추천 활동을 한 행에 복수 열로 표시
                        st.markdown("##### 추천 활동")
                        activities = {
                            "기쁨": ["긍정적인 경험 일기 쓰기", "다른 사람과 기쁨 나누기", "감사 명상"],
                            "슬픔": ["감정 일기 쓰기", "자연 속 산책", "슬픔을 표현하는 예술 활동"],
                            "분노": ["운동하기", "심호흡 연습", "감정 정리 글쓰기"],
                            "불안": ["마음챙김 명상", "점진적 근육 이완법", "걱정 목록 작성하기"],
                            "스트레스": ["요가", "충분한 휴식", "자연 속에서 시간 보내기"],
                            "외로움": ["온라인 모임 참여", "자원봉사", "새로운 취미 배우기"],
                            "후회": ["자기 용서 명상", "교훈 찾기 연습", "미래 계획 세우기"],
                            "좌절": ["작은 성취 목표 설정", "멘토 찾기", "역경 극복 사례 읽기"],
                            "혼란": ["생각 정리를 위한 글쓰기", "전문가 상담", "명상"],
                            "감사": ["감사 일기 쓰기", "타인에게 감사 표현하기", "봉사활동"]
                        }
                        
                        # 추천 활동을 표로 표시
                        activity_data = {"감정": [], "추천 활동": []}
                        for emotion in dominant_emotions:
                            if emotion in activities:
                                activity_data["감정"].append(emotion)
                                activity_data["추천 활동"].append(", ".join(activities[emotion]))
                        
                        activity_df = pd.DataFrame(activity_data)
                        st.dataframe(activity_df, hide_index=True, use_container_width=True)
                            
                        # 시간대별 추천을 표로 변경
                        st.markdown("##### 시간대별 추천")
                        time_recommendations = {
                            "새벽 (0-6시)": "충분한 수면을 취하고, 명상이나 가벼운 스트레칭으로 하루를 시작해보세요.",
                            "오전 (6-12시)": "가장 에너지가 높은 시간대입니다. 중요한 의사결정이나 창의적인 활동에 집중해보세요.",
                            "오후 (12-18시)": "가벼운 산책이나 동료와의 대화로 에너지를 유지하세요.",
                            "저녁 (18-24시)": "하루를 돌아보고 감사한 일들을 기록하세요. 편안한 활동으로 수면 준비를 시작하세요."
                        }
                        
                        # 사용자가 가장 많이 대화한 시간대 확인
                        if not df.empty:
                            user_peak_time = df['time_category'].mode()[0]
                            
                            # 시간대별 추천을 표로 표시
                            rec_data = {"시간대": [], "추천 활동": []}
                            rec_data["시간대"].append(user_peak_time)
                            rec_data["추천 활동"].append(time_recommendations.get(user_peak_time, "규칙적인 생활 패턴을 유지하세요."))
                            
                            rec_df = pd.DataFrame(rec_data)
                            st.dataframe(rec_df, hide_index=True, use_container_width=True)

# 주기적 자동 저장
if (st.session_state.logged_in and 
    'messages' in st.session_state and 
    len(st.session_state.messages) > 1 and
    st.session_state.get('selected_emotion')):
    auto_save()

# 푸터
st.markdown("---")
st.markdown("© 2025 감정 치유 AI 챗봇 | 개인 정보는 안전하게 보호됩니다.") 