import streamlit as st
import os
from dotenv import load_dotenv
from auth import setup_auth, register_user, save_user_data, load_user_data, login, logout
from chatbot import EMOTIONS, initialize_chat_history, display_chat_history, add_message, get_ai_response, start_new_chat, analyze_emotion

# 환경 변수 로드
load_dotenv()

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
if 'api_key' not in st.session_state:
    st.session_state.api_key = os.getenv("OPENAI_API_KEY", "")

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
                login_form = st.empty()
                with login_form.container():
                    username = st.text_input("사용자 이름", key="login_username")
                    password = st.text_input("비밀번호", type="password", key="login_password")
                    login_button = st.button("로그인")
                    
                    if login_button:
                        success, name = login(credentials, username, password)
                        if success:
                            st.session_state.logged_in = True
                            st.session_state.username = username
                            st.success(f"환영합니다, {name}님!")
                            
                            # 사용자 데이터 로드
                            st.session_state.user_data = load_user_data(username)
                            
                            # 채팅 초기화
                            initialize_chat_history()
                            login_form.empty()
                            st.rerun()
                        else:
                            st.error("사용자 이름 또는 비밀번호가 잘못되었습니다.")
            except Exception as e:
                st.error(f"로그인 중 오류가 발생했습니다: {e}")

            # 회원가입으로 이동 버튼
            st.markdown("---")
            if st.button("계정이 없으신가요? 회원가입 하기"):
                st.session_state.active_tab = "회원가입"
                st.rerun()
        
        elif selected_tab == "회원가입":
            register_user(credentials)
            
            # 로그인으로 이동 버튼
            st.markdown("---")
            if st.button("이미 계정이 있으신가요? 로그인 하기"):
                st.session_state.active_tab = "로그인"
                st.rerun()
    else:
        st.subheader(f"사용자: {st.session_state.username}")
        if st.button("로그아웃", key="logout_button"):
            # 사용자 데이터 저장
            if 'messages' in st.session_state:
                if 'user_data' not in st.session_state:
                    st.session_state.user_data = {"chat_history": [], "emotions": []}
                
                # 최신 채팅 기록 저장
                if 'selected_emotion' in st.session_state and st.session_state.selected_emotion:
                    st.session_state.user_data["emotions"].append(st.session_state.selected_emotion)
                
                # 채팅 기록 저장
                chat_history = [msg for msg in st.session_state.messages if msg["role"] != "system"]
                st.session_state.user_data["chat_history"] = chat_history
                
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
    st.info("로그인하면 AI 챗봇과 대화할 수 있습니다. 왼쪽 사이드바에서 로그인해주세요.")
else:
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
        
        # 새 감정 선택 버튼
        if st.button("다른 감정 선택하기"):
            st.session_state.selected_emotion = None
            st.session_state.chat_started = False
            st.rerun()

# 푸터
st.markdown("---")
st.markdown("© 2023 감정 치유 AI 챗봇 | 개인 정보는 안전하게 보호됩니다.") 