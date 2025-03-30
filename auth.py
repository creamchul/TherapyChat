import streamlit as st
import streamlit_authenticator as stauth
import yaml
from yaml.loader import SafeLoader
import os
import pickle
from pathlib import Path

# 사용자 인증 설정
def setup_auth():
    # 설정 파일이 없는 경우 생성
    config_file = Path("config.yaml")
    if not config_file.exists():
        # 기본 사용자 생성
        passwords = ["guest"]
        hashed_passwords = stauth.Hasher(passwords).generate()
        credentials = {
            'usernames': {
                'guest': {
                    'name': '게스트',
                    'password': hashed_passwords[0],
                    'email': 'guest@example.com'
                }
            }
        }
        config = {
            'credentials': credentials,
            'cookie': {
                'expiry_days': 30,
                'key': 'emotion_healing_app',
                'name': 'emotion_healing_cookie'
            }
        }
        with open(config_file, 'w') as file:
            yaml.dump(config, file, default_flow_style=False)

    # 설정 파일 로드
    with open(config_file) as file:
        config = yaml.load(file, Loader=SafeLoader)

    # 인증자 생성 - 0.1.5 버전 형식으로 변경
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['expiry_days'],
        config['cookie']['key']
    )
    
    return authenticator

# 새 사용자 등록 기능
def register_user(authenticator):
    st.subheader("새 계정 만들기")
    
    # 폼 입력 필드 생성
    with st.form("회원가입_폼", clear_on_submit=True):
        username = st.text_input("사용자 이름", key="reg_username")
        name = st.text_input("이름", key="reg_name")
        email = st.text_input("이메일", key="reg_email")
        password = st.text_input("비밀번호", type="password", key="reg_password")
        password_confirm = st.text_input("비밀번호 확인", type="password", key="reg_password_confirm")
        
        # 가입 버튼
        submit = st.form_submit_button("가입하기", use_container_width=True)
        
        if submit:
            # 입력 검증
            if not username or not name or not email or not password:
                st.error("모든 필드를 입력해주세요.")
                return
                
            if password != password_confirm:
                st.error("비밀번호가 일치하지 않습니다.")
                return
                
            # 설정 파일 로드
            config_file = Path("config.yaml")
            try:
                with open(config_file) as file:
                    config = yaml.load(file, Loader=SafeLoader)
                    
                # 사용자 이름 중복 확인
                if username in config['credentials']['usernames']:
                    st.error("이미 존재하는 사용자 이름입니다.")
                    return
                    
                # 새 사용자 추가
                hashed_passwords = stauth.Hasher([password]).generate()
                config['credentials']['usernames'][username] = {
                    'name': name,
                    'password': hashed_passwords[0],
                    'email': email
                }
                
                # 설정 파일 저장
                with open(config_file, 'w') as file:
                    yaml.dump(config, file, default_flow_style=False)
                    
                st.success("계정이 생성되었습니다. 로그인해 주세요.")
                
                # 세션 상태 업데이트
                st.session_state.active_tab = "로그인"
                st.rerun()
            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")

# 사용자 데이터 관리
def save_user_data(username, data):
    """사용자 데이터를 저장합니다."""
    os.makedirs("user_data", exist_ok=True)
    with open(f"user_data/{username}.pkl", "wb") as f:
        pickle.dump(data, f)

def load_user_data(username):
    """사용자 데이터를 로드합니다."""
    try:
        with open(f"user_data/{username}.pkl", "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return {"chat_history": [], "emotions": []} 