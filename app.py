import streamlit as st
import os
import datetime
import time
import pandas as pd
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

# 한국 시간대 설정
KST = pytz.timezone('Asia/Seoul')

# 페이지 설정
st.set_page_config(
    page_title="감정 치유 AI 챗봇",
    page_icon="❤️",
    layout="wide",
    initial_sidebar_state="expanded"
)

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

# 감정 목표 업데이트 함수
def update_emotion_goal(emotion):
    """
    감정에 따라 사용자의 감정 목표 진행도를 업데이트하는 함수
    """
    if not st.session_state.logged_in:
        return
    
    username = st.session_state.username
    user_data = st.session_state.user_data
    
    # 활성화된 감정 목표 확인
    emotion_goals = user_data.get("emotion_goals", {"active_goal": None, "history": []})
    active_goal = emotion_goals.get("active_goal", None)
    
    if not active_goal:
        return
    
    # 목표 감정과 현재 감정 비교
    target_emotion = active_goal.get("target_emotion")
    if emotion == target_emotion:
        # 목표 감정과 일치하는 경우 진행도 증가
        progress = active_goal.get("progress", 0)
        # 5% 증가, 최대 100%
        progress = min(progress + 5, 100)
        active_goal["progress"] = progress
        
        # 성과 기록
        today = datetime.datetime.now().strftime("%Y-%m-%d")
        active_goal.setdefault("achievements", []).append({
            "date": today,
            "description": f"목표 감정 '{target_emotion}'을(를) 경험했습니다."
        })
        
        # 목표 달성 시 자동 완료
        if progress >= 100:
            active_goal["completed"] = True
            active_goal["completion_date"] = today
            emotion_goals["history"].append(active_goal)
            emotion_goals["active_goal"] = None
    
    # 사용자 데이터 업데이트
    user_data["emotion_goals"] = emotion_goals
    st.session_state.user_data = user_data
    
    # 데이터 저장
    save_user_data(username, user_data)

# 감정 선택 저장 처리
def handle_emotion_selection(emotion):
    """
    선택된 감정 처리 및 저장 함수
    """
    # 감정 설정
    st.session_state.selected_emotion = emotion
    
    # 현재 채팅 세션에 감정 저장
    if 'chat_id' not in st.session_state:
        timestamp = datetime.datetime.now().isoformat()
        st.session_state.chat_id = f"chat_{timestamp}"
    
    chat_id = st.session_state.chat_id
    
    # 채팅 세션 업데이트
    if 'user_data' in st.session_state and 'chat_sessions' in st.session_state.user_data:
        chat_sessions = st.session_state.user_data['chat_sessions']
        found = False
        for i, chat in enumerate(chat_sessions):
            if chat['id'] == chat_id:
                chat['emotion'] = emotion
                found = True
                break
                
        if not found:
            # 새 채팅 세션 생성
            chat_sessions.append({
                "id": chat_id,
                "date": datetime.datetime.now().isoformat(),
                "emotion": emotion,
                "preview": "새로운 대화",
                "messages": []
            })
        
        # 채팅 기록 업데이트
        st.session_state.user_data['chat_sessions'] = chat_sessions
        
        # 사용자 데이터 저장
        save_user_data(st.session_state.username, st.session_state.user_data)
        
        # 감정 목표 업데이트
        update_emotion_goal(emotion)
    
    # 새 채팅 시작
    st.session_state.chat_started = True
    start_new_chat(emotion)
    
    # 화면 갱신
    st.rerun()

# DataFrames를 페이지네이션과 함께 표시하는 함수
def display_dataframe_with_pagination(df, page_size=10, key="pagination"):
    """
    DataFrame을 페이지네이션과 함께 표시하는 함수
    """
    # 세션 상태 초기화
    if f'{key}_page' not in st.session_state:
        st.session_state[f'{key}_page'] = 0
    
    # 전체 페이지 수 계산
    total_pages = max(len(df) // page_size, 1)
    
    # 현재 페이지 데이터 가져오기
    start_idx = st.session_state[f'{key}_page'] * page_size
    end_idx = min(start_idx + page_size, len(df))
    page_df = df.iloc[start_idx:end_idx]
    
    # 하단 컨트롤
    cols = st.columns([1, 3, 1])
    
    # 이전 페이지 버튼
    with cols[0]:
        if st.button("← 이전", key=f"{key}_prev", disabled=st.session_state[f'{key}_page'] == 0):
            st.session_state[f'{key}_page'] = max(0, st.session_state[f'{key}_page'] - 1)
            st.rerun()
    
    # 페이지 정보
    with cols[1]:
        st.markdown(f"**{st.session_state[f'{key}_page'] + 1}/{total_pages} 페이지** (총 {len(df)}개)")
    
    # 다음 페이지 버튼
    with cols[2]:
        if st.button("다음 →", key=f"{key}_next", disabled=st.session_state[f'{key}_page'] >= total_pages - 1):
            st.session_state[f'{key}_page'] = min(total_pages - 1, st.session_state[f'{key}_page'] + 1)
            st.rerun()
    
    # 현재 페이지 데이터 표시
    st.dataframe(page_df, use_container_width=True)

# CSS 스타일 적용
st.markdown("""
<style>
    /* 기본 스타일 */
    :root {
        --primary-color: #4f8bf9;
        --secondary-color: #f6a8cc;
        --background-color: #f9f9f9;
        --card-background: white;
        --text-color: #333;
        --secondary-text-color: #666;
        --border-color: #e0e0e0;
        --hover-color: #f9f9ff;
        --button-color: #6a89cc;
        --button-hover: #5679c1;
        --warning-color: #f44336;
        --success-color: #4CAF50;
        --emotion-grid-columns: 4;
    }
    
    /* 다크 모드 */
    [data-theme="dark"] {
        --primary-color: #6a89cc;
        --secondary-color: #f6a8cc;
        --background-color: #1e1e1e;
        --card-background: #2d2d2d;
        --text-color: #f0f0f0;
        --secondary-text-color: #aaaaaa;
        --border-color: #444444;
        --hover-color: #3d3d3d;
        --button-color: #5679c1;
        --button-hover: #4a6cb3;
        --warning-color: #ff5252;
        --success-color: #81c784;
    }
    
    /* 기본적으로 라이트 모드 */
    body {
        color: var(--text-color);
        background-color: var(--background-color);
        transition: all 0.3s ease;
    }
    
    /* 반응형 디자인 */
    @media (max-width: 768px) {
        .main-header {
            font-size: 1.8rem !important;
        }
        
        .sub-header {
            font-size: 1.2rem !important;
        }
        
        :root {
            --emotion-grid-columns: 2;
        }
        
        .emotion-button {
            padding: 8px !important;
            margin: 4px !important;
            font-size: 0.9rem !important;
        }
        
        .emotion-grid {
            display: grid;
            grid-template-columns: repeat(var(--emotion-grid-columns), 1fr);
            gap: 8px;
            margin-bottom: 16px;
        }
        
        .chat-container {
            height: 350px !important;
            padding: 15px !important;
        }
        
        .chat-card {
            padding: 10px !important;
            margin-bottom: 10px !important;
        }
        
        /* 모바일에서 테이블 스크롤 가능하게 */
        .dataframe-container {
            overflow-x: auto !important;
            width: 100% !important;
        }
        
        /* 모바일에서 사이드바가 너무 좁지 않게 */
        .css-1d391kg, .css-1lcbmhc {
            width: 100% !important;
        }
    }
    
    /* 공통 스타일 */
    .main-header {
        font-size: 2.5rem;
        color: var(--primary-color);
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .sub-header {
        font-size: 1.5rem;
        color: var(--primary-color);
        margin-bottom: 1rem;
    }
    
    /* 감정 선택 UI 개선 */
    .emotion-container {
        padding: 15px;
        border-radius: 10px;
        background-color: var(--card-background);
        margin-bottom: 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    
    .emotion-grid {
        display: grid;
        grid-template-columns: repeat(var(--emotion-grid-columns), 1fr);
        gap: 12px;
        margin: 15px 0;
    }
    
    .emotion-button {
        background-color: var(--card-background);
        color: var(--text-color);
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 15px 10px;
        text-align: center;
        cursor: pointer;
        transition: all 0.3s ease;
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    
    .emotion-button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.1);
        background-color: var(--hover-color);
    }
    
    .emotion-button .emoji {
        font-size: 2rem;
        margin-bottom: 8px;
        display: block;
    }
    
    .emotion-button.selected {
        background-color: var(--button-color);
        color: white;
        border-color: transparent;
    }
    
    /* 채팅 컨테이너 개선 */
    .chat-container {
        border-radius: 10px;
        padding: 20px;
        background-color: var(--card-background);
        height: 400px;
        overflow-y: auto;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin-bottom: 15px;
        border: 1px solid var(--border-color);
    }
    
    /* 입력 필드 개선 */
    .stTextInput > div > div > input {
        border-radius: 20px;
        padding: 10px 15px;
        border: 1px solid var(--border-color);
        background-color: var(--card-background);
        color: var(--text-color);
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: var(--primary-color);
        box-shadow: 0 0 0 2px rgba(79, 139, 249, 0.2);
    }
    
    .stTextInput input, .stSelectbox, .stDateInput input, .stTextArea textarea {
        background-color: var(--card-background) !important;
        color: var(--text-color) !important;
        border-color: var(--border-color) !important;
    }
    
    .stDataFrame {
        background-color: var(--card-background) !important;
    }
    
    .stDataFrame th {
        background-color: var(--primary-color) !important;
        color: white !important;
    }
    
    .stDataFrame td {
        color: var(--text-color) !important;
    }
    
    /* 테이블 스타일 개선 */
    .dataframe-container {
        border-radius: 10px;
        overflow: hidden;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin-bottom: 20px;
    }
    
    .table-controls {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 10px;
        flex-wrap: wrap;
    }
    
    .table-search {
        flex: 1;
        max-width: 300px;
        margin-right: 10px;
    }
    
    .table-page-controls {
        display: flex;
        align-items: center;
    }
    
    .table-page-controls button {
        margin: 0 5px;
        min-width: 30px;
    }
    
    .sortable-header {
        cursor: pointer;
        position: relative;
    }
    
    .sortable-header:hover {
        background-color: rgba(0,0,0,0.05);
    }
    
    .sortable-header::after {
        content: "↕";
        position: absolute;
        right: 8px;
        opacity: 0.5;
    }
    
    .sort-asc::after {
        content: "↑";
        opacity: 1;
    }
    
    .sort-desc::after {
        content: "↓";
        opacity: 1;
    }
    
    /* 채팅 카드 스타일 */
    .chat-card {
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 15px;
        background-color: var(--card-background);
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        transition: transform 0.2s, box-shadow 0.2s;
        position: relative;
        z-index: 1;
        cursor: pointer;
    }
    
    .chat-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        background-color: var(--hover-color);
        border-color: var(--button-color);
    }
    
    .chat-card:after {
        content: "›";
        position: absolute;
        right: 15px;
        top: 50%;
        transform: translateY(-50%);
        font-size: 24px;
        color: var(--button-color);
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
        border-bottom: 1px solid var(--border-color);
        padding-bottom: 10px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
    }
    
    .chat-card-emotion {
        font-weight: bold;
        color: var(--primary-color);
    }
    
    .chat-card-date {
        color: var(--secondary-text-color);
        font-size: 0.9rem;
    }
    
    .chat-card-preview {
        color: var(--text-color);
        overflow: hidden;
        text-overflow: ellipsis;
        display: -webkit-box;
        -webkit-line-clamp: 2;
        -webkit-box-orient: vertical;
    }
    
    .filter-section {
        background-color: var(--background-color);
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 20px;
        border: 1px solid var(--border-color);
    }
    
    .filter-title {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 10px;
        color: var(--primary-color);
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
        background-color: var(--background-color);
        color: var(--primary-color);
    }
    
    .view-button:hover {
        background-color: var(--hover-color);
    }
    
    .delete-button {
        background-color: #ffebee;
        color: var(--warning-color);
    }
    
    .delete-button:hover {
        background-color: #ffcdd2;
    }
    
    .pagination-button {
        margin: 0 4px;
        padding: 6px 12px;
        border-radius: 4px;
        background-color: var(--background-color);
        color: var(--text-color);
        border: 1px solid var(--border-color);
        cursor: pointer;
        transition: all 0.3s;
    }
    
    .pagination-button:hover {
        background-color: var(--hover-color);
    }
    
    .pagination-active {
        background-color: var(--primary-color);
        color: white;
        border-color: var(--primary-color);
    }
    
    .filter-badge {
        display: inline-block;
        padding: 4px 8px;
        margin: 2px;
        border-radius: 4px;
        background-color: var(--button-color);
        color: white;
        font-size: 0.8rem;
    }
    
    /* 로그인/회원가입 버튼 스타일 */
    .login-button, .auth-container button {
        display: block;
        width: 100%;
        background-color: var(--button-color);
        color: white;
        padding: 8px 15px;
        border-radius: 5px;
        border: none;
        cursor: pointer;
        font-weight: 500;
        margin: 8px 0;
        text-align: center;
        opacity: 1;
        position: relative;
    }
    
    .login-button:hover, .auth-container button:hover {
        background-color: var(--button-hover);
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
if 'theme' not in st.session_state:
    st.session_state.theme = "light"

# 자동 저장 함수 정의
def auto_save():
    """
    현재 채팅을 자동으로 저장하는 함수
    """
    if not st.session_state.logged_in or not st.session_state.selected_emotion:
        return
    
    # 현재 채팅 ID가 없으면 생성
    if 'current_chat_id' not in st.session_state:
        timestamp = datetime.datetime.now().isoformat()
        st.session_state.current_chat_id = f"chat_{timestamp}"
    
    # 채팅 세션 업데이트
    if 'user_data' not in st.session_state:
        st.session_state.user_data = {"chat_history": [], "chat_sessions": []}
    
    chat_sessions = st.session_state.user_data.get('chat_sessions', [])
    current_chat_id = st.session_state.current_chat_id
    
    # 현재 채팅 찾기 또는 새로 생성
    current_chat = None
    for chat in chat_sessions:
        if chat['id'] == current_chat_id:
            current_chat = chat
            break
    
    if not current_chat:
        current_chat = {
            "id": current_chat_id,
            "date": datetime.datetime.now().isoformat(),
            "emotion": st.session_state.selected_emotion,
            "messages": []
        }
        chat_sessions.append(current_chat)
    
    # 메시지 업데이트
    if 'messages' in st.session_state:
        current_chat['messages'] = st.session_state.messages
        # 미리보기 업데이트 (마지막 사용자 메시지)
        user_messages = [msg for msg in st.session_state.messages if msg['role'] == 'user']
        if user_messages:
            current_chat['preview'] = user_messages[-1]['content'][:100]
    
    # 사용자 데이터 업데이트
    st.session_state.user_data['chat_sessions'] = chat_sessions
    save_user_data(st.session_state.username, st.session_state.user_data)

def save_current_chat():
    """
    현재 채팅을 저장하는 함수
    """
    if not st.session_state.logged_in or not st.session_state.selected_emotion:
        return
    
    # 현재 채팅 ID가 없으면 생성
    if 'current_chat_id' not in st.session_state:
        timestamp = datetime.datetime.now().isoformat()
        st.session_state.current_chat_id = f"chat_{timestamp}"
    
    # 채팅 세션 업데이트
    if 'user_data' not in st.session_state:
        st.session_state.user_data = {"chat_history": [], "chat_sessions": []}
    
    chat_sessions = st.session_state.user_data.get('chat_sessions', [])
    current_chat_id = st.session_state.current_chat_id
    
    # 현재 채팅 찾기 또는 새로 생성
    current_chat = None
    for chat in chat_sessions:
        if chat['id'] == current_chat_id:
            current_chat = chat
            break
    
    if not current_chat:
        current_chat = {
            "id": current_chat_id,
            "date": datetime.datetime.now().isoformat(),
            "emotion": st.session_state.selected_emotion,
            "messages": []
        }
        chat_sessions.append(current_chat)
    
    # 메시지 업데이트
    if 'messages' in st.session_state:
        current_chat['messages'] = st.session_state.messages
        # 미리보기 업데이트 (마지막 사용자 메시지)
        user_messages = [msg for msg in st.session_state.messages if msg['role'] == 'user']
        if user_messages:
            current_chat['preview'] = user_messages[-1]['content'][:100]
    
    # 사용자 데이터 업데이트
    st.session_state.user_data['chat_sessions'] = chat_sessions
    save_user_data(st.session_state.username, st.session_state.user_data)

# 사이드바 - 로그인/로그아웃
with st.sidebar:
    if st.button("로그아웃"):
        logout()
        st.session_state.logged_in = False
        st.session_state.selected_emotion = None
        st.session_state.chat_started = False
        st.session_state.active_page = "chat"
        st.session_state.selected_chat_id = None
        st.session_state.confirm_delete_dialog = False
        st.success("로그아웃되었습니다.")
        st.rerun()

# 채팅 세션 정보 표시
if st.session_state.selected_chat_id:
    selected_chat = None
    for chat in st.session_state.user_data['chat_sessions']:
        if chat['id'] == st.session_state.selected_chat_id:
            selected_chat = chat
            break

    if selected_chat:
        with st.container():
            conf_col1, conf_col2 = st.columns(2)
            with conf_col1:
                if st.button("채팅 삭제", key="confirm_delete_yes"):
                    st.session_state.selected_chat_id = None
                    st.session_state.confirm_delete_dialog = False
                    st.session_state.user_data['chat_sessions'].remove(selected_chat)
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

# 주기적 자동 저장
if (st.session_state.logged_in and 
    'messages' in st.session_state and 
    len(st.session_state.messages) > 1 and
    'selected_emotion' in st.session_state and
    st.session_state.selected_emotion and
    'auto_save' not in st.session_state):
    st.session_state.auto_save = True
    auto_save()

# 푸터
st.markdown("---")
st.markdown("© 2025 감정 치유 AI 챗봇 | 개인 정보는 안전하게 보호됩니다.")