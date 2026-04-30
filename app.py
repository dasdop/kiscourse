import streamlit as st
import pandas as pd
import os
import random
from datetime import datetime

# ==========================================
# 1. 공용 설정 관리 함수 (관리자-학생 동기화)
# ==========================================
def save_settings(status, semester):
    df = pd.DataFrame([{'app_status': status, 'target_semester': semester}])
    df.to_csv('settings.csv', index=False, encoding='utf-8-sig')

def load_settings():
    if os.path.exists('settings.csv'):
        try:
            df = pd.read_csv('settings.csv')
            return df.iloc[0]['app_status'], df.iloc[0]['target_semester']
        except: return "준비중", "1학기"
    return "준비중", "1학기"

# ==========================================
# 2. 기본 설정 및 시간표 데이터
# ==========================================
st.set_page_config(page_title="KIS 수강신청 시스템", layout="wide", page_icon="🍏")

# 실시간 설정 로드
current_status, current_sem = load_settings()

if 'page' not in st.session_state: st.session_state.page = 'login'
if 'login_email' not in st.session_state: st.session_state.login_email = None
# 파일에서 읽어온 값을 세션에 강제 주입
st.session_state.app_status = current_status
st.session_state.target_semester = current_sem

GRADE_CONFIG = {
    "11학년": {
        "common": {
            "영어 I": [("월", "1교시"), ("수", "5교시"), ("목", "3교시")],
            "창의적 사고 설계": [("수", "2교시"), ("목", "6교시")],
            "스포츠 문화": [("화", "3교시")]
        },
        "groups": {
            "Group A": ["물리학", "미적분 II"], "Group B": ["생명과학", "미디어와 비판적사고"],
            "Group C": ["토론과 글쓰기", "Introduction to Biology"], "Group D": ["미적분 I", "물리학 실험"],
            "Group E": ["대수", "소프트웨어와 생활"], "Group F": ["화학", "물질과 에너지"],
            "Group G": ["Introduction to Chemistry", "확률과 통계"]
        },
        "slots": {
            "Group A": [("월", "3교시"), ("수", "3교시"), ("금", "6교시")],
            "Group B": [("월", "6교시"), ("화", "5교시"), ("금", "3교시")],
            "Group C": [("화", "1교시"), ("목", "1교시"), ("월", "7교시"), ("목", "7교시")],
            "Group D": [("수", "1교시"), ("목", "4교시"), ("금", "4교시"), ("화", "6교시")],
            "Group E": [("목", "2교시"), ("화", "4교시"), ("월", "5교시"), ("금", "1교시"), ("금", "5교시")],
            "Group F": [("금", "1교시"), ("화", "2교시"), ("월", "4교시"), ("수", "6교시")],
            "Group G": [("월", "2교시"), ("목", "2교시"), ("화", "7교시"), ("수", "7교시")]
        }
    },
    "12학년": {
        "common": {
            "심화 영어": [("월", "1교시"), ("수", "5교시")],
            "졸업 프로젝트": [("화", "1교시"), ("목", "3교시")]
        },
        "groups": {
            "Group A": ["미적분 II", "경제 수학"], "Group B": ["심화 국어", "고전 읽기"],
            "Group C": ["물리학 II", "화학 II"], "Group D": ["생명과학 II", "지구과학 II"],
            "Group E": ["세계 지리", "동아시아사"], "Group F": ["생활과 윤리", "사회문제 탐구"],
            "Group G": ["AP 컴퓨터 과학", "인공지능 수학"], "Group H": ["심화 영어 회화", "영미 문학 읽기"]
        },
        "slots": {
            "Group A": [("월", "2교시"), ("수", "3교시")], "Group B": [("화", "4교시"), ("금", "5교시")],
            "Group C": [("월", "3교시"), ("화", "6교시")], "Group D": [("화", "7교시"), ("수", "4교시")],
            "Group E": [("월", "4교시"), ("금", "6교시")], "Group F": [("월", "5교시"), ("화", "2교시")],
            "Group G": [("수", "7교시"), ("목", "7교시")], "Group H": [("월", "6교시"), ("목", "1교시")]
        }
    }
}

ID_11 = "1xADYmy5iJEIiaENxCH1ZiqGU2yiFS81MfSQDCMsnO04" 
ID_12 = "1Yp79f79ilwA2ErJ6DoxRPbU_ADCq0PnRGH2TxGvKSDg"

# ==========================================
# 3. 데이터 로드 및 사이드바
# ==========================================
def get_csv_df(filename):
    if os.path.exists(filename): return pd.read_csv(filename, dtype=str)
    return None

@st.cache_data(ttl=30)
def load_full_data():
    try:
        url_11 = f"https://docs.google.com/spreadsheets/d/{ID_11}/export?format=csv"
        url_12 = f"https://docs.google.com/spreadsheets/d/{ID_12}/export?format=csv"
        def safe_load(url):
            df = pd.read_csv(url, header=None, dtype=str)
            idx = 0
            for i in range(len(df)):
                row = [str(v).strip() for v in df.iloc[i].values]
                if '학기' in row and '과목명' in row: idx = i; break
            df.columns = [str(v).strip() for v in df.iloc[idx].values]
            return df.iloc[idx + 1:].reset_index(drop=True)
        return safe_load(url_11), safe_load(url_12)
    except: return None, None

df_11, df_12 = load_full_data()
list_11 = df_11['과목명'].unique().tolist() if df_11 is not None else []
list_12 = df_12['과목명'].unique().tolist() if df_12 is not None else []

with st.sidebar:
    st.title("🍏 KIS 메뉴")
    if st.session_state.login_email:
        st.info(f"👤 {st.session_state.user_name}님 ({st.session_state.user_id})")
        
        if st.session_state.user_id == "admin":
            st.divider()
            st.subheader("⚙️ 실시간 제어")
            # 관리자가 선택을 바꾸면
            new_status = st.radio("시스템 단계", ["준비중", "수강신청 진행", "과목거래 오픈"], 
                                  index=["준비중", "수강신청 진행", "과목거래 오픈"].index(st.session_state.app_status))
            new_sem = st.selectbox("진행 학기", ["1학기", "2학기"], 
                                   index=["1학기", "2학기"].index(st.session_state.target_semester))
            # 버튼을 누르는 순간 settings.csv 파일이 갱신됨
            if st.button("📢 설정 전체 적용"):
                save_settings(new_status, new_sem)
                st.success("반영 완료!"); st.rerun()

        st.divider()
        if st.button("🏠 메인 대시보드"): st.session_state.page = "dashboard"; st.rerun()
        if st.button("🚪 로그아웃"): st.session_state.clear(); st.rerun()

# ==========================================
# 4. 페이지 로직 (로그인/대시보드/신청/결과)
# ==========================================

# [로그인 페이지]
if st.session_state.login_email is None:
    # (회원가입 로직 생략 없이 동일하게 유지됨)
    if st.session_state.page == "signup":
        st.title("📝 KIS 회원가입")
        with st.container(border=True):
            se, sp, si, sn = st.text_input("이메일"), st.text_input("비번", type="password"), st.text_input("학번"), st.text_input("이름")
            if st.button("가입"):
                pd.DataFrame([{'이메일':se,'비밀번호':sp,'학번':si,'이름':sn}]).to_csv('users.csv', mode='a', header=not os.path.exists('users.csv'), index=False)
                st.success("성공!"); st.session_state.page = "login"; st.rerun()
            if st.button("취소"): st.session_state.page = "login"; st.rerun()
    else:
        st.title("🍏 로그인")
        with st.container(border=True):
            le, lp = st.text_input("이메일"), st.text_input("비밀번호", type="password")
            if st.button("로그인", type="primary"):
                if le == "admin" and lp == "admin123":
                    st.session_state.update({'login_email':'admin','user_name':'관리자','user_id':'admin','page':'dashboard'}); st.rerun()
                u_df = get_csv_df('users.csv')
                if u_df is not None:
                    user = u_df[(u_df['이메일']==le) & (u_df['비밀번호']==lp)]
                    if not user.empty:
                        st.session_state.update({'login_email':le,'user_name':user.iloc[0]['이름'],'user_id':user.iloc[0]['학번'],'page':'dashboard'}); st.rerun()
            if st.button("회원가입"): st.session_state.page = "signup"; st.rerun()
    st.stop()

# [대시보드]
elif st.session_state.page == "dashboard":
    st.title(f"👋 {st.session_state.user_name}님")
    st.info(f"📢 상태: **{st.session_state.app_status}** | 학기: **{st.session_state.target_semester}**")
    col1, col2 = st.columns(2); col3, col4 = st.columns(2)
    with col1:
        if st.button("📝 수강신청", use_container_width=True): st.session_state.page = "apply"; st.rerun()
    with col2:
        if st.button("📊 결과/시간표", use_container_width=True): st.session_state.page = "result"; st.rerun()
    with col3:
        if st.button("🤝 거래소", use_container_width=True): st.session_state.page = "trade"; st.rerun()
    with col4:
        st.button("🔔 알림함", use_container_width=True) if st.session_state.user_id != "admin" else st.button("⚙️ 관리", use_container_width=True)

# [수강신청/결과조회 등] - 위에서 정의한 st.session_state.app_status를 그대로 사용
elif st.session_state.page == "apply":
    st.title("📝 수강신청")
    if st.session_state.app_status != "수강신청 진행":
        st.error("현재 신청 기간이 아닙니다."); st.button("돌아가기")
    # ... 신청 로직 (이전과 동일)

elif st.session_state.page == "result":
    st.title("📊 확정 시간표")
    # ... 시간표 시각화 로직 (이전과 동일)
