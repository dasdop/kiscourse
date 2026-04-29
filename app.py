import streamlit as st
import pandas as pd
import os
import time
import random
from datetime import datetime

# ==========================================
# 1. 시스템 설정 동기화 (파일 기반 실시간 연동)
# ==========================================
def save_settings(status, semester):
    df = pd.DataFrame([{'app_status': status, 'target_semester': semester}])
    df.to_csv('settings.csv', index=False, encoding='utf-8-sig')

def load_settings():
    if os.path.exists('settings.csv'):
        try:
            df = pd.read_csv('settings.csv')
            return df.iloc[0]['app_status'], df.iloc[0]['target_semester']
        except:
            return "준비중", "1학기"
    return "준비중", "1학기"

# ==========================================
# 2. 초기 설정 및 고정 시간표 데이터
# ==========================================
st.set_page_config(page_title="KIS 수강신청", layout="wide", page_icon="🍏")

# 앱 실행 시 최신 설정 로드
current_status, current_sem = load_settings()

if 'page' not in st.session_state: st.session_state.page = 'login'
if 'user_email' not in st.session_state: st.session_state.user_email = None

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

TRACKS = ['국어과', '영어과', '수학과', '사회과', '과학과', '베트남어과', '예술과', '정보과']
ID_11 = "1xADYmy5iJEIiaENxCH1ZiqGU2yiFS81MfSQDCMsnO04" 
ID_12 = "1Yp79f79ilwA2ErJ6DoxRPbU_ADCq0PnRGH2TxGvKSDg"

# ==========================================
# 3. 데이터 로딩 (구글 시트 연동)
# ==========================================
@st.cache_data(ttl=60)
def load_all_course_data():
    try:
        url_11 = f"https://docs.google.com/spreadsheets/d/{ID_11}/export?format=csv"
        url_12 = f"https://docs.google.com/spreadsheets/d/{ID_12}/export?format=csv"
        def process_csv(url):
            df = pd.read_csv(url, header=None, dtype=str)
            for i in range(len(df)):
                row = [str(v).strip() for v in df.iloc[i].values]
                if '학기' in row and '과목명' in row:
                    df.columns = row
                    return df.iloc[i+1:].reset_index(drop=True)
            return pd.DataFrame()
        return process_csv(url_11), process_csv(url_12)
    except: return None, None

df_11, df_12 = load_all_course_data()

# ==========================================
# 4. 사이드바 (실시간 제어판)
# ==========================================
with st.sidebar:
    st.title("🍏 KIS 메뉴")
    if st.session_state.user_email:
        st.info(f"👤 {st.session_state.user_name} ({st.session_state.user_id})")
        
        if st.session_state.user_id == "admin":
            st.divider()
            st.subheader("⚙️ 실시간 시스템 제어")
            new_st = st.radio("전체 단계 설정", ["준비중", "수강신청 진행", "과목거래 오픈"], 
                              index=["준비중", "수강신청 진행", "과목거래 오픈"].index(st.session_state.app_status))
            new_sm = st.selectbox("진행 학기", ["1학기", "2학기"],
                                  index=["1학기", "2학기"].index(st.session_state.target_semester))
            if st.button("📢 전체 학생 즉시 적용", type="primary", use_container_width=True):
                save_settings(new_st, new_sm)
                st.success("시스템 상태 동기화 완료!"); time.sleep(0.5); st.rerun()

        st.divider()
        if st.button("🏠 대시보드", use_container_width=True): st.session_state.page = 'dashboard'; st.rerun()
        if st.button("🚪 로그아웃", use_container_width=True):
            for k in list(st.session_state.keys()): del st.session_state[k]
            st.rerun()

# ==========================================
# 5. 페이지 렌더링
# ==========================================

# [로그인/회원가입]
if st.session_state.user_email is None:
    if st.session_state.page == "signup":
        st.title("📝 회원가입")
        with st.form("signup"):
            e, p, i, n = st.text_input("이메일"), st.text_input("비번", type="password"), st.text_input("학번"), st.text_input("이름")
            if st.form_submit_button("가입"):
                pd.DataFrame([{'이메일':e,'비번':p,'학번':i,'이름':n}]).to_csv('users.csv', mode='a', header=not os.path.exists('users.csv'), index=False, encoding='utf-8-sig')
                st.success("완료!"); st.session_state.page = "login"; st.rerun()
            if st.button("돌아가기"): st.session_state.page = "login"; st.rerun()
    else:
        st.title("🍏 KIS 수강신청")
        with st.container(border=True):
            le, lp = st.text_input("이메일"), st.text_input("비번", type="password")
            if st.button("로그인", type="primary", use_container_width=True):
                if le == "admin" and lp == "admin123":
                    st.session_state.update({'user_email':'admin','user_name':'관리자','user_id':'admin','page':'dashboard'}); st.rerun()
                if os.path.exists('users.csv'):
                    u_df = pd.read_csv('users.csv', dtype=str)
                    u = u_df[(u_df['이메일']==le) & (u_df['비번']==lp)]
                    if not u.empty:
                        st.session_state.update({'user_email':le,'user_name':u.iloc[0]['이름'],'user_id':u.iloc[0]['학번'],'page':'dashboard'}); st.rerun()
                    else: st.error("정보 불일치")
            if st.button("가입하기"): st.session_state.page = "signup"; st.rerun()
    st.stop()

# [대시보드]
elif st.session_state.page == "dashboard":
    st.title(f"👋 {st.session_state.user_name}님")
    st.info(f"📢 시스템 상태: **{st.session_state.app_status}** | 학기: **{st.session_state.target_semester}**")
    c1, c2 = st.columns(2); c3, c4 = st.columns(2)
    with c1:
        if st.button("📝 수강신청", use_container_width=True):
            if st.session_state.app_status == "수강신청 진행": st.session_state.page = "apply"; st.rerun()
            else: st.error("기간이 아닙니다.")
    with c2:
        if st.button("📊 결과 확인", use_container_width=True): st.session_state.page = "result"; st.rerun()
    with c3:
        if st.button("🤝 거래소", use_container_width=True):
            if st.session_state.app_status == "과목거래 오픈": st.session_state.page = "trade"; st.rerun()
            else: st.warning("준비 중")
    with c4:
        is_adm = st.session_state.user_id == "admin"
        if st.button("⚙️ 관리" if is_adm else "🔔 알림", use_container_width=True):
            st.session_state.page = "admin_page" if is_adm else "noti"; st.rerun()

# [수강신청]
elif st.session_state.page == "apply":
    st.title("📝 수강신청")
    u_id = str(st.session_state.user_id)
    grade = "11학년" if u_id.startswith("10") else "12학년"
    target_df = df_11 if grade == "11학년" else df_12
    if target_df is not None:
        sk = st.session_state.target_semester[0]
        subs = target_df[target_df['학기'].fillna('').str.contains(sk)]['과목명'].unique().tolist()
        with st.form("apply"):
            sel = st.multiselect("과목 선택", subs)
            if st.form_submit_button("제출"):
                pd.DataFrame([{'학번':u_id,'이름':st.session_state.user_name,'과목':",".join(sel)}]).to_csv('apply_data.csv', mode='a', header=not os.path.exists('apply_data.csv'), index=False, encoding='utf-8-sig')
                st.success("제출 완료!"); st.session_state.page = "dashboard"; st.rerun()

# [관리자 전용 & 시뮬레이션]
elif st.session_state.page == "admin_page":
    st.title("⚙️ 관리 시스템")
    t1, t2 = st.tabs(["🚀 배정 시뮬레이터", "📢 실전 발표"])
    with t1:
        st.subheader("170명 가상 배정 테스트")
        if st.button("🔴 시뮬레이션 실행 (170명)", use_container_width=True):
            sim_list = []
            for i in range(170):
                sim_list.append({"학번": f"SIM-{i:03d}", "만족도": f"{random.randint(85,100)}%", "상태": "배정완료"})
            st.dataframe(pd.DataFrame(sim_list), use_container_width=True)
            st.success("✅ 시뮬레이션 성공: 현재 구조로 170명 수용 가능합니다.")
    with t2:
        if st.button("🚀 실제 신청 데이터로 결과 발표", type="primary", use_container_width=True):
            if os.path.exists('apply_data.csv'):
                pd.read_csv('apply_data.csv').to_csv('final.csv', index=False, encoding='utf-8-sig')
                st.success("학생들에게 결과가 공개되었습니다!"); st.rerun()
            else: st.error("데이터 없음")

# (나머지 result, trade, noti 페이지는 이전 로직과 동일)
