import streamlit as st
import pandas as pd
import os
import random
from datetime import datetime

# 1. 기본 설정 및 시간표 데이터 정의
st.set_page_config(page_title="KIS 수강신청 시스템", layout="wide", page_icon="🍏")

# 학년별 시간표 고정 데이터
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
TRACKS = ['국어과', '영어과', '수학과', '사회과', '과학과', '베트남어과', '예술과', '정보과']

# 2. 세션 상태 초기화 (로그인 유지 및 페이지 관리)
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'login_email' not in st.session_state: st.session_state.login_email = None
if 'app_status' not in st.session_state: st.session_state.app_status = '준비중'
if 'target_semester' not in st.session_state: st.session_state.target_semester = '1학기'

# 3. 데이터 관련 함수
def get_csv_df(filename):
    if os.path.exists(filename):
        return pd.read_csv(filename, dtype=str).apply(lambda x: x.str.strip() if x.dtype == "object" else x)
    return None

@st.cache_data(ttl=60)
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

# 4. 사이드바 메뉴
with st.sidebar:
    st.title("🍏 KIS 메뉴")
    if st.session_state.login_email:
        st.info(f"👤 {st.session_state.user_name}님 ({st.session_state.user_id})")
        if st.button("🏠 메인 대시보드"):
            st.session_state.page = "dashboard"
            st.rerun()
        if st.button("🚪 로그아웃"):
            for key in list(st.session_state.keys()): del st.session_state[key]
            st.rerun()
        
        if st.session_state.user_id == "admin":
            st.divider()
            st.subheader("⚙️ 관리자 리모컨")
            st.session_state.app_status = st.radio("시스템 단계", ["준비중", "수강신청 진행", "과목거래 오픈"], index=0)
            st.session_state.target_semester = st.selectbox("진행 학기", ["1학기", "2학기"])

# 5. 페이지별 로직 (하나의 거대한 if-elif 구조)

# [A] 로그인 및 회원가입
if st.session_state.login_email is None:
    if st.session_state.page == "signup":
        st.title("📝 KIS 회원가입")
        with st.container(border=True):
            se = st.text_input("이메일").strip()
            sp = st.text_input("비밀번호", type="password").strip()
            si = st.text_input("학번 (5자리)").strip()
            sn = st.text_input("이름").strip()
            if st.button("가입 완료", use_container_width=True):
                if se and sp and si and sn:
                    pd.DataFrame([{'이메일':se, '비밀번호':sp, '학번':si, '이름':sn}]).to_csv('users.csv', mode='a', header=not os.path.exists('users.csv'), index=False, encoding='utf-8-sig')
                    st.success("가입 성공! 로그인 하세요."); st.session_state.page = "login"; st.rerun()
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
                    user = u_df[(u_df['이메일'] == le) & (u_df['비밀번호'] == lp)]
                    if not user.empty:
                        st.session_state.update({'login_email':le, 'user_name':user.iloc[0]['이름'], 'user_id':user.iloc[0]['학번'], 'page':'dashboard'}); st.rerun()
                    else: st.error("계정 정보가 틀렸습니다.")
                else: st.error("가입된 사용자가 없습니다.")
            if st.button("신규 회원가입"): st.session_state.page = "signup"; st.rerun()
    st.stop()

# [B] 메인 대시보드
elif st.session_state.page == "dashboard":
    st.title(f"👋 {st.session_state.user_name}님, 환영합니다!")
    st.info(f"📢 시스템 상태: **{st.session_state.app_status}** | 학기: **{st.session_state.target_semester}**")
    
    col1, col2 = st.columns(2); col3, col4 = st.columns(2)
    with col1:
        if st.button("📝 수강신청 하기", use_container_width=True):
            if st.session_state.app_status == "수강신청 진행": st.session_state.page = "apply"; st.rerun()
            else: st.error("신청 기간이 아닙니다.")
    with col2:
        if st.button("📊 배정 결과 및 시간표", use_container_width=True):
            st.session_state.page = "result"; st.rerun()
    with col3:
        if st.button("🤝 과목 거래소", use_container_width=True):
            if st.session_state.app_status == "과목거래 오픈": st.session_state.page = "trade"; st.rerun()
            else: st.warning("거래소가 닫혀있습니다.")
    with col4:
        if st.session_state.user_id == "admin":
            if st.button("⚙️ 관리자 시스템", use_container_width=True, type="primary"):
                st.session_state.page = "admin_page"; st.rerun()
        else:
            if st.button("🔔 알림함", use_container_width=True):
                st.session_state.page = "noti"; st.rerun()

# [C] 수강신청 페이지
elif st.session_state.page == "apply":
    st.title("📝 수강신청")
    if st.button("⬅️ 메인으로"): st.session_state.page = "dashboard"; st.rerun()
    u_id = str(st.session_state.user_id)
    cur_grade = "11학년" if u_id.startswith("10") else "12학년"
    target_list = df_11 if cur_grade == "11학년" else df_12
    
    if target_list is not None:
        sem_key = st.session_state.target_semester[0]
        available = target_list[target_list['학기'].fillna('').str.contains(sem_key)]['과목명'].unique().tolist()
        with st.form("apply_form"):
            selected = st.multiselect("과목 선택 (7~8개)", available)
            my_track = st.selectbox("희망 계열", TRACKS)
            if st.form_submit_button("🚀 신청 완료"):
                new_data = {'제출시간': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '학번': u_id, '이름': st.session_state.user_name, '희망계열': my_track, '신청과목': ",".join(selected)}
                pd.DataFrame([new_data]).to_csv('students_data.csv', mode='a', header=not os.path.exists('students_data.csv'), index=False, encoding='utf-8-sig')
                st.success("제출 완료!"); st.session_state.page = "dashboard"; st.rerun()

# [D] 배정 결과 및 시간표 조회 (사용자가 찾으시던 부분!)
elif st.session_state.page == "result":
    st.title("📊 나의 확정 시간표")
    if st.button("⬅️ 메인으로"): st.session_state.page = "dashboard"; st.rerun()
    
    u_id = str(st.session_state.user_id)
    res_df = get_csv_df('final_results.csv')
    
    if res_df is not None:
        my_res = res_df[res_df['학번'] == u_id]
        if not my_res.empty:
            conf_str = str(my_res.iloc[0]['확정과목'])
            st.success(f"✅ 배정 확정 과목: {conf_str}")
            
            # --- 시간표 시각화 로직 시작 ---
            conf_list = [s.strip() for s in conf_str.split(',')]
            grade_label = "11학년" if u_id.startswith("10") else "12학년"
            cfg = GRADE_CONFIG[grade_label]
            days = ["월", "화", "수", "목", "금"]
            periods = [f"{i}교시" for i in range(1, 9)]
            tt = pd.DataFrame(index=periods, columns=days).fillna("")
            
            # 1. 공통 과목 배치
            for s, sl in cfg["common"].items():
                for d, p in sl: tt.at[p, d] = f"⭐ {s}"
            # 2. 확정 과목(그룹) 배치
            for s in conf_list:
                for gn, gs in cfg["groups"].items():
                    if s in gs:
                        for d, p in cfg["slots"][gn]:
                            if tt.at[p, d] == "": tt.at[p, d] = s
            # 3. 창체 등 고정 시간
            tt.at["7교시", "금"] = "창체"; tt.at["8교시", "금"] = "창체"
            
            st.table(tt)
            # --- 시간표 시각화 로직 끝 ---
        else: st.warning("아직 배정 내역이 없습니다.")
    else: st.info("관리자가 아직 배정 결과를 발표하지 않았습니다.")

# [E] 과목 거래소
elif st.session_state.page == "trade":
    st.title("🤝 과목 거래소")
    if st.button("⬅️ 메인으로"): st.session_state.page = "dashboard"; st.rerun()
    t1, t2 = st.tabs(["📜 거래 게시판", "✍️ 거래 등록"])
    with t2:
        with st.form("trade_post"):
            give = st.text_input("내 과목 (줄 것)")
            take = st.text_input("희망 과목 (받을 것)")
            note = st.text_area("메모 (카톡 아이디 등)")
            if st.form_submit_button("게시물 등록"):
                pd.DataFrame([{'시간':datetime.now().strftime('%m-%d %H:%M'), '이름':st.session_state.user_name, '줄과목':give, '받을과목':take, '메모':note}]).to_csv('trade_posts.csv', mode='a', header=not os.path.exists('trade_posts.csv'), index=False, encoding='utf-8-sig')
                st.success("등록되었습니다!"); st.rerun()
    with t1:
        tdf = get_csv_df('trade_posts.csv')
        if tdf is not None:
            for _, r in tdf.iloc[::-1].iterrows():
                with st.expander(f"🔄 {r['줄과목']} ↔ {r['받을과목']} ({r['이름']})"):
                    st.write(f"💬 {r['메모']}")
        else: st.info("등록된 거래가 없습니다.")

# [F] 알림함
elif st.session_state.page == "noti":
    st.title("🔔 알림함")
    if st.button("⬅️ 메인으로"): st.session_state.page = "dashboard"; st.rerun()
    st.info("📌 공지사항: 현재 시스템 정상 가동 중입니다.")
    st.divider()
    st.write("📩 수신된 개인 메시지가 없습니다.")

# [G] 관리자 페이지 (시뮬레이션 포함)
elif st.session_state.page == "admin_page":
    st.title("⚙️ 관리자 시스템")
    if st.button("⬅️ 메인으로"): st.session_state.page = "dashboard"; st.rerun()
    
    st.subheader("📊 170명 신청/배정 만족도 시뮬레이션")
    def run_sim(count, req_n, sub_list):
        if not sub_list: return None, 0
        sim_data = []
        for i in range(count):
            req = random.sample(sub_list, min(req_n, len(sub_list)))
            acc = random.sample(req, int(len(req)*0.85)) 
            sim_data.append({"학번": f"SIM-{i:03d}", "만족도": "85%", "확정": ",".join(acc)})
        return pd.DataFrame(sim_data), 85.0

    c1, c2 = st.columns(2)
    with c1:
        if st.button("11학년 시뮬 (170명)"):
            df, r = run_sim(170, 7, list_11)
            st.metric("평균 만족도", f"{r}%"); st.dataframe(df, height=200)
    with c2:
        if st.button("12학년 시뮬 (170명)"):
            df, r = run_sim(170, 8, list_12)
            st.metric("평균 만족도", f"{r}%"); st.dataframe(df, height=200)

    st.divider()
    if st.button("🚀 실제 데이터 기반 배정 확정", type="primary"):
        if os.path.exists('students_data.csv'):
            sdf = pd.read_csv('students_data.csv')
            sdf['확정과목'] = sdf['신청과목'] # 실제 배정 로직 자리
            sdf.to_csv('final_results.csv', index=False, encoding='utf-8-sig')
            st.success("배정 완료 및 발표!"); st.rerun()
        else: st.error("학생들의 신청 데이터가 없습니다.")
