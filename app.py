import streamlit as st
import os
import datetime
import time
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
    }
    .chat-card:active {
        transform: translateY(0);
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    /* 버튼 숨기기 */
    button[key^="chat_card_"] {
        position: absolute;
        opacity: 0;
        width: 100%;
        height: 100%;
        top: 0;
        left: 0;
        z-index: 2;
        cursor: pointer;
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
                            
                            # 현재 채팅 ID 초기화
                            if 'current_chat_id' in st.session_state:
                                del st.session_state.current_chat_id
                            
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
    st.info("로그인하면 AI 챗봇과 대화할 수 있습니다. 왼쪽 사이드바에서 로그인해주세요.")
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
                    with st.container():
                        # 카드 클릭 감지를 위한 버튼 (숨김)
                        card_clicked = st.button(
                            "보기",
                            key=f"chat_card_{chat['id']}",
                            help="이 대화 보기",
                            label_visibility="collapsed",
                            use_container_width=True
                        )
                        
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
                        
                        if card_clicked:
                            st.session_state.selected_chat_id = chat['id']
                            st.rerun()

# 주기적 자동 저장
if (st.session_state.logged_in and 
    'messages' in st.session_state and 
    len(st.session_state.messages) > 1 and
    st.session_state.get('selected_emotion')):
    auto_save()

# 푸터
st.markdown("---")
st.markdown("© 2025 감정 치유 AI 챗봇 | 개인 정보는 안전하게 보호됩니다.") 