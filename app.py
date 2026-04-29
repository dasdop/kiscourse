import streamlit as st
import pandas as pd
import os
from datetime import datetime

# 1. 시스템 설정
st.set_page_config(page_title="KIS 통합 수강관리", layout="wide", page_icon="🍏")

# ==========================================
# 2. 학년별 시간표 데이터셋 (이미지 및 요청사항 반영)
# ==========================================

GRADE_CONFIG = {
    "11학년": {
        "common": {
            "영어 I": [("월", "1교시"), ("수", "5교시"), ("목", "3교시")],
            "창의적 사고 설계": [("수", "2교시"), ("목", "6교시")],
            "스포츠 문화": [("화", "8교시"), ("목", "8교시")]
        },
        "groups": {
            "Group A": ["물리학 I", "세계사"], "Group B": ["화학 I", "경제"],
            "Group C": ["생명과학 I", "정치와 법"], "Group D": ["지구과학 I", "사회문화"],
            "Group E": ["기하", "윤리와 사상"], "Group F": ["프로그래밍", "미술 감상"],
            "Group G": ["일본어 I", "중국어 I"]
        },
        "slots": {
            "Group A": [("월", "2교시"), ("수", "3교시")], "Group B": [("화", "4교시"), ("금", "5교시")],
            "Group C": [("월", "3교시"), ("화", "6교시")], "Group D": [("화", "7교시"), ("수", "4교시")],
            "Group E": [("월", "4교시"), ("금", "6교시")], "Group F": [("월", "5교시"), ("화", "2교시")],
            "Group G": [("수", "7교시"), ("목", "7교시")]
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

# ==========================================
# 3. 핵심 로직 함수
# ==========================================

def get_target_grade(user_id):
    """학번과 현재 시즌을 고려하여 대상 학년 결정"""
    uid = str(user_id)
    # 10학번이 신청할 때 -> 11학년 과목
    if uid.startswith("10"): return "11학년"
    # 11학번이 신청할 때 -> (2학기면 11학년, 내년 대비면 12학년) -> 여기선 12학년으로 우선 처리 가능
    if uid.startswith("11"): return "12학년"
    if uid.startswith("12"): return "12학년"
    return "11학년"

def draw_timetable(confirmed_list, grade):
    """지정된 학년 레이아웃으로 시간표 생성"""
    config = GRADE_CONFIG[grade]
    days, periods = ["월", "화", "수", "목", "금"], ["1교시", "2교시", "3교시", "4교시", "5교시", "6교시", "7교시", "8교시"]
    tt = pd.DataFrame(index=periods, columns=days).fillna("")
    
    # 1. 공통 배치
    for sub, slots in config["common"].items():
        for d, p in slots: tt.at[p, d] = f"⭐ {sub}"
    
    # 2. 선택 배치
    for sub in confirmed_list:
        for g_name, g_subs in config["groups"].items():
            if sub in g_subs:
                for d, p in config["slots"][g_name]:
                    if tt.at[p, d] == "": tt.at[p, d] = sub
    
    # 3. 고정 일과
    tt.at["7교시", "금"] = "창체"; tt.at["8교시", "금"] = "창체"
    return tt

# ==========================================
# 4. 화면 구성 (Streamlit)
# ==========================================

if 'page' not in st.session_state:
    st.session_state.update({'login_email': None, 'page': 'login', 'user_id': None})

# [로그인 화면]
if st.session_state.login_email is None:
    st.title("🍏 KIS 통합 수강관리")
    le = st.text_input("Email (@kis.ac.kr)")
    if st.button("Login"):
        st.session_state.update({'login_email':le, 'user_id':le.split('@')[0], 'page':'dashboard'})
        st.rerun()
    st.stop()

# [메인 대시보드]
if st.session_state.page == "dashboard":
    target_grade = get_target_grade(st.session_state.user_id)
    st.title(f"👋 {st.session_state.user_id}님, 반갑습니다!")
    st.info(f"현재 시스템은 **{target_grade}** 기준으로 설정되어 있습니다.")
    
    if st.button("📊 나의 시간표 확인", use_container_width=True):
        st.session_state.page = "result"; st.rerun()

# [결과 조회]
elif st.session_state.page == "result":
    target_grade = get_target_grade(st.session_state.user_id)
    st.title(f"📅 {target_grade} 확정 시간표")
    
    if st.button("⬅️ 메인으로"): st.session_state.page = "dashboard"; st.rerun()

    # 가상 확정 데이터 (실제론 파일에서 읽음)
    my_subs = ["미적분 II", "심화 국어", "물리학 II"] if target_grade == "12학년" else ["물리학 I", "경제"]
    
    final_tt = draw_timetable(my_subs, target_grade)
    
    def style_tt(val):
        if "⭐" in val: return 'background-color: white; color: black; border: 1px solid #ddd; font-weight: bold'
        if val == "": return 'background-color: #f8f9fa'
        return 'background-color: #D1E9FF; color: #004085; font-weight: bold'

    st.table(final_tt.style.applymap(style_tt))
