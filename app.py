import streamlit as st
import pandas as pd
import os
import random
from datetime import datetime

# 1. 기본 설정 및 상수
st.set_page_config(page_title="KIS 수강신청 시스템", layout="wide", page_icon="🍏")

# 시간표 데이터 정의 (NameError 방지)
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

# 세션 상태 초기화
if 'login_email' not in st.session_state:
    st.session_state.update({
        'login_email': None, 'user_name': None, 'user_id': None, 
        'page': 'login', 'app_status': '준비중', 'target_semester': '1학기'
    })

# 데이터 관련 함수
def get_csv_df(filename):
    if os.path.exists(filename):
        return pd.read_csv(filename, dtype=str)
    return None

# 2. 로그인 및 회원가입 로직 (들여쓰기 오류 수정 지점)
if st.session_state.login_email is None:
    if st.session_state.page == "signup":
        st.title("📝 KIS 회원가입")
        with st.container(border=True):
            se = st.text_input("이메일 (@kis.ac.kr)").strip()
            sp = st.text_input("비밀번호", type="password").strip()
            si = st.text_input("학번 (5자리)").strip()
            sn = st.text_input("이름").strip()
            if st.button("가입 완료", use_container_width=True):
                if se and sp and si and sn:
                    new_user = pd.DataFrame([{'이메일':se, '비밀번호':sp, '학번':si, '이름':sn}])
                    new_user.to_csv('users.csv', mode='a', header=not os.path.exists('users.csv'), index=False, encoding='utf-8-sig')
                    st.success("가입 성공! 로그인을 진행하세요."); st.session_state.page = "login"; st.rerun()
                else: st.error("모든 정보를 입력하세요.")
            if st.button("돌아가기"): st.session_state.page = "login"; st.rerun()
    else:
        st.title("🍏 KIS 수강신청 로그인")
        with st.container(border=True):
            le = st.text_input("이메일").strip()
            lp = st.text_input("비밀번호", type="password").strip()
            if st.button("로그인", type="primary", use_container_width=True):
                if le == "admin" and lp == "admin123":
                    st.session_state.update({'login_email':'admin','user_name':'관리자','user_id':'admin','page':'dashboard'}); st.rerun()
                
                u_df = get_csv_df('users.csv')
                if u_df is not None:
                    # 모든 열 공백 제거 후 비교
                    u_df = u_df.apply(lambda x: x.str.strip())
                    user = u_df[(u_df['이메일'] == le) & (u_df['비밀번호'] == lp)]
                    if not user.empty:
                        st.session_state.update({
                            'login_email': le, 
                            'user_name': user.iloc[0]['이름'], 
                            'user_id': str(user.iloc[0]['학번']), 
                            'page': 'dashboard'
                        }); st.rerun()
                    else: st.error("정보 불일치! 이메일이나 비밀번호를 확인하세요.")
                else: st.error("가입된 정보가 없습니다.")
            if st.button("신규 회원가입"): st.session_state.page = "signup"; st.rerun()
    st.stop()

# 3. 메인 대시보드 및 결과 페이지
if st.session_state.page == "dashboard":
    st.title(f"👋 {st.session_state.user_name}님, 환영합니다!")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📊 배정 결과 조회", use_container_width=True): st.session_state.page = "result"; st.rerun()
    with col2:
        if st.button("🚪 로그아웃", use_container_width=True): st.session_state.clear(); st.rerun()

elif st.session_state.page == "result":
    st.title("📊 나의 확정 시간표")
    if st.button("⬅️ 메인으로"): st.session_state.page = "dashboard"; st.rerun()

    u_id = str(st.session_state.user_id)
    target_grade = "12학년" if u_id.startswith("11") else "11학년"
    grade_cfg = GRADE_CONFIG[target_grade]

    res_df = get_csv_df('final_results.csv')
    if res_df is not None:
        # 데이터프레임 공백 제거
        res_df['학번'] = res_df['학번'].str.strip()
        my_res = res_df[res_df['학번'] == u_id]
        if not my_res.empty:
            confirmed_subs = [s.strip() for s in str(my_res.iloc[0]['확정과목']).split(',')]
            
            # 시간표 그리기
            days, periods = ["월", "화", "수", "목", "금"], ["1교시", "2교시", "3교시", "4교시", "5교시", "6교시", "7교시", "8교시"]
            tt = pd.DataFrame(index=periods, columns=days).fillna("")
            
            for sub, slots in grade_cfg["common"].items():
                for d, p in slots: tt.at[p, d] = f"⭐ {sub}"
            for sub in confirmed_subs:
                for g_name, g_subs in grade_cfg["groups"].items():
                    if sub in g_subs:
                        for d, p in grade_cfg["slots"][g_name]:
                            if tt.at[p, d] == "": tt.at[p, d] = sub
            
            tt.at["7교시", "금"] = "창체"; tt.at["8교시", "금"] = "창체"
            st.table(tt)
        else: st.warning("배정 결과가 없습니다.")
    else: st.info("결과가 발표되지 않았습니다.")
