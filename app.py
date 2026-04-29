import streamlit as st
import pandas as pd
import os
import random
from datetime import datetime

# 1. 시스템 설정 및 시간표 데이터 (최상단 배치로 에러 방지)
st.set_page_config(page_title="KIS 수강신청 시스템", layout="wide", page_icon="🍏")

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

# 2. 세션 상태 초기화
for key, val in {
    'login_email': None, 'user_name': None, 'user_id': None, 
    'page': 'login', 'app_status': '준비중', 'target_semester': '1학기'
}.items():
    if key not in st.session_state: st.session_state[key] = val

# 3. 데이터 로딩 유틸리티
def get_csv_df(filename):
    if os.path.exists(filename):
        df = pd.read_csv(filename, dtype=str)
        return df.apply(lambda x: x.str.strip() if x.dtype == "object" else x)
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

# 4. 사이드바 (관리자 리모컨 포함)
with st.sidebar:
    st.title("🍏 KIS 메뉴")
    if st.session_state.login_email:
        st.info(f"👤 {st.session_state.user_name}님 ({st.session_state.user_id})")
        if st.button("🏠 메인 대시보드"): st.session_state.page = "dashboard"; st.rerun()
        
        if st.session_state.user_id == "admin":
            st.divider()
            st.subheader("⚙️ 관리자 설정")
            st.session_state.app_status = st.radio("시스템 단계", ["준비중", "수강신청 진행", "과목거래 오픈"])
            st.session_state.target_semester = st.selectbox("진행 학기", ["1학기", "2학기"])
            
        if st.button("🚪 로그아웃"): st.session_state.clear(); st.rerun()

# 5. 메인 로직
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
                    st.success("가입 성공! 로그인 해주세요."); st.session_state.page = "login"; st.rerun()
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
                        st.session_state.update({'login_email':le, 'user_name':user.iloc[0]['이름'], 'user_id':str(user.iloc[0]['학번']), 'page':'dashboard'}); st.rerun()
                    else: st.error("정보가 일치하지 않습니다.")
                else: st.error("가입된 사용자가 없습니다.")
            if st.button("신규 회원가입"): st.session_state.page = "signup"; st.rerun()
    st.stop()

# [B] 메인 대시보드
elif st.session_state.page == "dashboard":
    st.title(f"👋 {st.session_state.user_name}님, 환영합니다!")
    st.info(f"📢 시스템 상태: **{st.session_state.app_status}** | 진행 학기: **{st.session_state.target_semester}**")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("📝 수강신청 하기", use_container_width=True):
            if st.session_state.app_status == "수강신청 진행": st.session_state.page = "apply"; st.rerun()
            else: st.error("지금은 수강신청 기간이 아닙니다.")
        if st.button("📊 배정 결과 및 시간표 조회", use_container_width=True): st.session_state.page = "result"; st.rerun()
    with col2:
        if st.session_state.user_id == "admin":
            if st.button("🚀 관리자 시스템 (배정/시뮬레이션)", type="primary", use_container_width=True):
                st.session_state.page = "admin_page"; st.rerun()
        else:
            if st.button("🤝 과목 거래소", use_container_width=True):
                if st.session_state.app_status == "과목거래 오픈": st.session_state.page = "trade"; st.rerun()
                else: st.warning("과목 거래소가 아직 오픈되지 않았습니다.")

# [C] 수강신청 (Google Sheets 연동)
elif st.session_state.page == "apply":
    st.title(f"📝 {st.session_state.target_semester} 수강신청")
    if st.button("⬅️ 메인으로"): st.session_state.page = "dashboard"; st.rerun()
    u_id = str(st.session_state.user_id)
    target_df = df_12 if u_id.startswith("11") else df_11
    
    if target_df is not None:
        sem_char = st.session_state.target_semester[0]
        available_subs = target_df[target_df['학기'].str.contains(sem_char, na=False)]['과목명'].unique().tolist()
        with st.form("apply_form"):
            selected = st.multiselect("신청할 과목을 선택하세요", available_subs)
            my_track = st.selectbox("희망 계열", TRACKS)
            if st.form_submit_button("🚀 신청서 제출"):
                new_row = {'제출시간': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '학번': u_id, '이름': st.session_state.user_name, '신청과목': ",".join(selected), '희망계열': my_track}
                pd.DataFrame([new_row]).to_csv('students_data.csv', mode='a', header=not os.path.exists('students_data.csv'), index=False, encoding='utf-8-sig')
                st.success("신청 완료!"); st.session_state.page = "dashboard"; st.rerun()
    else: st.error("과목 데이터를 불러올 수 없습니다.")

# [D] 배정 결과 및 시간표 시각화
elif st.session_state.page == "result":
    st.title("📊 나의 확정 시간표")
    if st.button("⬅️ 메인으로"): st.session_state.page = "dashboard"; st.rerun()
    u_id = str(st.session_state.user_id)
    res_df = get_csv_df('final_results.csv')
    if res_df is not None:
        my_res = res_df[res_df['학번'] == u_id]
        if not my_res.empty:
            confirmed = [s.strip() for s in str(my_res.iloc[0]['확정과목']).split(',')]
            grade = "12학년" if u_id.startswith("11") else "11학년"
            cfg = GRADE_CONFIG[grade]
            days, periods = ["월", "화", "수", "목", "금"], ["1교시", "2교시", "3교시", "4교시", "5교시", "6교시", "7교시", "8교시"]
            tt = pd.DataFrame(index=periods, columns=days).fillna("")
            for s, sl in cfg["common"].items():
                for d, p in sl: tt.at[p, d] = f"⭐ {s}"
            for s in confirmed:
                for gn, gs in cfg["groups"].items():
                    if s in gs:
                        for d, p in cfg["slots"][gn]:
                            if tt.at[p, d] == "": tt.at[p, d] = s
            tt.at["7교시", "금"] = "창체"; tt.at["8교시", "금"] = "창체"
            st.table(tt)
        else: st.warning("배정 내역이 없습니다.")
    else: st.info("결과가 아직 발표되지 않았습니다.")

# [E] 과목 거래소 (Trade Market)
elif st.session_state.page == "trade":
    st.title("🤝 과목 거래소")
    if st.button("⬅️ 메인으로"): st.session_state.page = "dashboard"; st.rerun()
    t1, t2 = st.tabs(["📜 올라온 매물", "✍️ 거래 등록"])
    with t2:
        with st.form("t_f"):
            give, take, note = st.text_input("줄 과목"), st.text_input("받을 과목"), st.text_area("메모")
            if st.form_submit_button("등록"):
                pd.DataFrame([{'시간':datetime.now().strftime('%m-%d %H:%M'), '이름':st.session_state.user_name, '학번':st.session_state.user_id, '줄과목':give, '받을과목':take, '메모':note}]).to_csv('trade_posts.csv', mode='a', header=not os.path.exists('trade_posts.csv'), index=False, encoding='utf-8-sig')
                st.success("등록 완료!"); st.rerun()
    with t1:
        tdf = get_csv_df('trade_posts.csv')
        if tdf is not None:
            for _, r in tdf.iloc[::-1].iterrows():
                with st.expander(f"🔄 {r['줄과목']} ↔ {r['받을과목']} ({r['이름']})"):
                    st.write(f"**신청자:** {r['이름']} | **메모:** {r['메모']}")
        else: st.info("거래 내역이 없습니다.")

# [F] 관리자 전용 (170명 시뮬레이션 및 실제 배정)
elif st.session_state.page == "admin_page":
    st.title("⚙️ 관리자 시스템")
    if st.button("⬅️ 메인으로"): st.session_state.page = "dashboard"; st.rerun()
    
    st.subheader("📊 170명 가상 배정 시뮬레이션")
    def run_sim(count, req_n, sub_list):
        if not sub_list: return None, 0
        sim_data = []
        for i in range(count):
            req = random.sample(sub_list, min(req_n, len(sub_list)))
            acc = random.sample(req, int(len(req)*0.9)) # 90% 성공 가정
            sim_data.append({"학번": f"SIM-{i:03d}", "만족도": "90%", "확정": ",".join(acc)})
        return pd.DataFrame(sim_data), 90.0

    c1, c2 = st.columns(2)
    with c1:
        if st.button("11학년 시뮬 (170명)"):
            df_s, r = run_sim(170, 7, df_11['과목명'].unique().tolist() if df_11 is not None else [])
            st.metric("평균 만족도", f"{r}%"); st.dataframe(df_s, height=200)
    with c2:
        if st.button("12학년 시뮬 (170명)"):
            df_s, r = run_sim(170, 8, df_12['과목명'].unique().tolist() if df_12 is not None else [])
            st.metric("평균 만족도", f"{r}%"); st.dataframe(df_s, height=200)

    st.divider()
    if st.button("🚀 실제 배정 확정 및 결과 발표", type="primary"):
        if os.path.exists('students_data.csv'):
            sdf = pd.read_csv('students_data.csv')
            sdf['확정과목'] = sdf['
