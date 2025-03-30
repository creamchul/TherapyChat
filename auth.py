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
        hasher = stauth.Hasher()
        hashed_password = hasher.hash("guest")
        credentials = {
            'usernames': {
                'guest': {
                    'name': '게스트',
                    'password': hashed_password,
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

    # 인증자 생성
    authenticator = stauth.Authenticate(
        config['credentials'],
        config['cookie']['name'],
        config['cookie']['key'],
        config['cookie']['expiry_days']
    )
    
    return authenticator

# 새 사용자 등록 기능
def register_user(authenticator):
    try:
        if 'username' not in st.session_state:
            # 새 사용자 등록 폼
            with st.form("회원가입"):
                st.subheader("새 계정 만들기")
                username = st.text_input("사용자 이름")
                name = st.text_input("이름")
                email = st.text_input("이메일")
                password = st.text_input("비밀번호", type="password")
                confirm_password = st.text_input("비밀번호 확인", type="password")
                
                submit = st.form_submit_button("가입하기")
                
                if submit:
                    try:
                        if password != confirm_password:
                            st.error("비밀번호가 일치하지 않습니다.")
                            return
                            
                        config_file = 'config.yaml'
                        with open(config_file) as file:
                            config = yaml.load(file, Loader=SafeLoader)
                            
                        if username in config['credentials']['usernames']:
                            st.error("이미 존재하는 사용자 이름입니다.")
                            return
                            
                        # 새 사용자 추가
                        hasher = stauth.Hasher()
                        hashed_password = hasher.hash(password)
                        config['credentials']['usernames'][username] = {
                            'name': name,
                            'password': hashed_password,
                            'email': email
                        }
                        
                        with open(config_file, 'w') as file:
                            yaml.dump(config, file, default_flow_style=False)
                            
                        st.success("계정이 생성되었습니다. 로그인해 주세요.")
                        st.experimental_rerun()
                    except Exception as e:
                        st.error(f"오류가 발생했습니다: {e}")
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