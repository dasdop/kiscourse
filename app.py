import streamlit as st
import pandas as pd
import os
import random
from datetime import datetime

# 1. 기본 설정 및 상수
st.set_page_config(page_title="KIS 수강신청", layout="wide", page_icon="🍏")
SCHOOL_DOMAIN = "kis.ac.kr"
ID_11 = "1xADYmy5iJEIiaENxCH1ZiqGU2yiFS81MfSQDCMsnO04" 
ID_12 = "1Yp79f79ilwA2ErJ6DoxRPbU_ADCq0PnRGH2TxGvKSDg"
MAX_CAPACITY = 20 # 과목당 최대 인원 예시
TRACKS = ['국어과', '영어과', '수학과', '사회과', '과학과', '베트남어과', '예술과', '정보과']

# 2. 세션 상태 초기화
if 'login_email' not in st.session_state: st.session_state.login_email = None
if 'user_name' not in st.session_state: st.session_state.user_name = None
if 'user_id' not in st.session_state: st.session_state.user_id = None
if 'page' not in st.session_state: st.session_state.page = "login"
if 'app_status' not in st.session_state: st.session_state.app_status = "준비중"
if 'target_semester' not in st.session_state: st.session_state.target_semester = "1학기"

# 3. 데이터 로드 및 헬퍼 함수
def get_csv_df(filename):
    if os.path.exists(filename): return pd.read_csv(filename)
    return None

def save_csv(df, filename):
    df.to_csv(filename, index=False, encoding='utf-8-sig')

def is_valid_sid_format(sid):
    return sid.isdigit() and len(sid) == 5

@st.cache_data(ttl=60)
def load_full_data():
    try:
        url_11 = f"https://docs.google.com/spreadsheets/d/{ID_11}/export?format=csv"
        url_12 = f"https://docs.google.com/spreadsheets/d/{ID_12}/export?format=csv"
        def safe_load(url):
            df = pd.read_csv(url, header=None, dtype=str)
            header_idx = 0
            for i in range(len(df)):
                row = [str(val).strip() for val in df.iloc[i].values]
                if '학기' in row and '과목명' in row:
                    header_idx = i
                    break
            df.columns = [str(val).strip() for val in df.iloc[header_idx].values]
            return df.iloc[header_idx + 1:].reset_index(drop=True)
        return safe_load(url_11), safe_load(url_12)
    except: return None, None

df_11, df_12 = load_full_data()

# 4. 사이드바 (관리자 메뉴)
with st.sidebar:
    st.title("⚙️ 시스템 설정")
    if st.session_state.user_id == "admin":
        st.header("👑 관리자 제어판")
        app_status = st.radio("단계 설정", ["준비중", "수강신청 진행", "과목거래 오픈"])
        target_sem = st.selectbox("학기 설정", ["1학기", "2학기"])
        if st.button("💾 설정 저장"):
            st.session_state.app_status = app_status
            st.session_state.target_semester = target_sem
            st.success("설정 완료!")
            st.rerun()
    
    st.divider()
    if st.session_state.login_email:
        st.write(f"🧑‍🎓 {st.session_state.user_name}님")
        if st.button("🏠 대시보드로"): st.session_state.page = "dashboard"; st.rerun()
        if st.button("🚪 로그아웃"): 
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()

# 5. 페이지 로직 (로그인/회원가입)
if st.session_state.login_email is None:
    if st.session_state.page == "login":
        st.title("🍏 KIS 수강신청 로그인")
        email = st.text_input("이메일")
        pw = st.text_input("비밀번호", type="password")
        if st.button("로그인", use_container_width=True, type="primary"):
            users = get_csv_df('users.csv')
            if email == "admin" and pw == "admin123": # 관리자 계정 예시
                st.session_state.update({'login_email':'admin', 'user_name':'관리자', 'user_id':'admin', 'page':'dashboard'})
                st.rerun()
            elif users is not None:
                user = users[(users['이메일']==email) & (users['비밀번호']==str(pw))]
                if not user.empty:
                    st.session_state.update({'login_email':email, 'user_name':user.iloc[0]['이름'], 'user_id':user.iloc[0]['학번'], 'page':'dashboard'})
                    st.rerun()
                else: st.error("정보가 틀립니다.")
        if st.button("회원가입"): st.session_state.page = "signup"; st.rerun()

    elif st.session_state.page == "signup":
        st.title("📝 회원가입")
        new_email = st.text_input("이메일")
        new_pw = st.text_input("비밀번호", type="password")
        new_id = st.text_input("학번 (5자리)")
        new_name = st.text_input("이름")
        if st.button("가입하기"):
            if is_valid_sid_format(new_id):
                new_data = pd.DataFrame([{'이메일':new_email, '비밀번호':new_pw, '학번':new_id, '이름':new_name}])
                new_data.to_csv('users.csv', mode='a', header=not os.path.exists('users.csv'), index=False, encoding='utf-8-sig')
                st.success("가입 성공! 로그인하세요."); st.session_state.page = "login"; st.rerun()
            else: st.error("학번을 확인하세요.")
        if st.button("돌아가기"): st.session_state.page = "login"; st.rerun()
    st.stop()

# 6. 메인 대시보드 (로그인 완료 후)
if st.session_state.page == "dashboard":
    st.title(f"👋 반갑습니다, {st.session_state.user_name}님!")
    st.info(f"현재 시스템 상태: **[{st.session_state.app_status}]** / 학기: **[{st.session_state.target_semester}]**")
    
    c1, c2 = st.columns(2); c3, c4 = st.columns(2)
    with c1:
        if st.button("📝 수강신청 하기", use_container_width=True, height=150):
            if st.session_state.app_status == "수강신청 진행": st.session_state.page = "apply"; st.rerun()
            else: st.error("지금은 신청 기간이 아닙니다.")
    with c2:
        if st.button("📊 결과 조회", use_container_width=True, height=150):
            st.session_state.page = "result"; st.rerun()
    with c3:
        if st.button("🤝 거래소", use_container_width=True, height=150):
            if st.session_state.app_status == "과목거래 오픈": st.session_state.page = "trade"; st.rerun()
            else: st.warning("거래소 준비중입니다.")
    with c4:
        if st.button("🔔 알림함", use_container_width=True, height=150):
            st.session_state.page = "noti"; st.rerun()

# 7. 상세 기능 페이지들
elif st.session_state.page == "apply":
    st.title("📝 수강신청")
    if st.button("⬅️ 메인으로"): st.session_state.page = "dashboard"; st.rerun()
    # 여기에 신청 폼 코드 삽입...
    st.write(f"{st.session_state.target_semester} 신청을 진행합니다.")

elif st.session_state.page == "result":
    st.title("📊 결과 조회")
    if st.button("⬅️ 메인으로"): st.session_state.page = "dashboard"; st.rerun()
    # 여기에 결과 조회 코드 삽입...

# (나머지 trade, noti 페이지도 동일한 방식으로 구성)
