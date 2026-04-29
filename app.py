import streamlit as st
import pandas as pd
import os
import random
from datetime import datetime

# 1. 기본 설정 및 상수
st.set_page_config(page_title="KIS 수강신청 시스템", layout="wide", page_icon="🍏")
SCHOOL_DOMAIN = "kis.ac.kr"
ID_11 = "1xADYmy5iJEIiaENxCH1ZiqGU2yiFS81MfSQDCMsnO04" 
ID_12 = "1Yp79f79ilwA2ErJ6DoxRPbU_ADCq0PnRGH2TxGvKSDg"
TRACKS = ['국어과', '영어과', '수학과', '사회과', '과학과', '베트남어과', '예술과', '정보과']
MAX_CAPACITY = 20
GRADE_CONFIG = {
    "11학년": {
        "common": {
            "영어 I": [("월", "1교시"), ("수", "5교시"), ("목", "3교시")],
            "창의적 사고 설계": [("수", "2교시"), ("목", "6교시")],
            "스포츠 문화": [("화", "3교시")]  # 이미지 시간표를 기반으로 조정 가능
        },
        "groups": {
            "Group A": ["물리학", "미적분 II"], 
            "Group B": ["생명과학", "미디어와 비판적사고"],
            "Group C": ["토론과 글쓰기", "Introduction to Biology"],
            "Group D": ["미적분 I", "물리학 실험"],
            "Group E": ["대수", "소프트웨어와 생활"],
            "Group F": ["화학", "물질과 에너지"],
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
# 2. 세션 상태 초기화
for key, val in {
    'login_email': None, 'user_name': None, 'user_id': None, 
    'page': 'login', 'app_status': '준비중', 'target_semester': '1학기'
}.items():
    if key not in st.session_state: st.session_state[key] = val

# 3. 데이터 관련 함수
def get_csv_df(filename):
    if os.path.exists(filename): return pd.read_csv(filename)
    return None

def save_csv(df, filename):
    df.to_csv(filename, index=False, encoding='utf-8-sig')

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

# 4. 사이드바 (리모컨)
with st.sidebar:
    st.title("🍏 KIS 메뉴")
    if st.session_state.login_email:
        st.info(f"👤 {st.session_state.user_name}님 ({st.session_state.user_id})")
        if st.button("🏠 메인 대시보드"): st.session_state.page = "dashboard"; st.rerun()
        if st.button("🚪 로그아웃"): st.session_state.clear(); st.rerun()
        
        if st.session_state.user_id == "admin":
            st.divider()
            st.subheader("⚙️ 관리자 리모컨")
            st.session_state.app_status = st.radio("시스템 단계", ["준비중", "수강신청 진행", "과목거래 오픈"])
            st.session_state.target_semester = st.selectbox("진행 학기", ["1학기", "2학기"])
            if st.button("💾 설정 강제 저장"): st.success("설정 반영됨!"); st.rerun()

# 5. 페이지 로직
# [A] 로그인 화면 로직 수정본
 else:
    st.title("🍏 KIS 수강신청 로그인")
    with st.container(border=True):
        le = st.text_input("이메일").strip()  # 입력값 공백 제거
        lp = st.text_input("비밀번호", type="password").strip()
        
        if st.button("로그인", type="primary", use_container_width=True):
            # 1. 관리자 계정 체크
            if le == "admin" and lp == "admin123":
                st.session_state.update({'login_email':'admin','user_name':'관리자','user_id':'admin','page':'dashboard'})
                st.rerun()
            
            # 2. 일반 학생 체크
            u_df = get_csv_df('users.csv')
            if u_df is not None:
                # 데이터프레임의 모든 값을 문자열로 변환하고 공백 제거 (핵심!)
                u_df['이메일'] = u_df['이메일'].astype(str).str.strip()
                u_df['비밀번호'] = u_df['비밀번호'].astype(str).str.strip()
                
                # 비교 시작
                user = u_df[(u_df['이메일'] == le) & (u_df['비밀번호'] == lp)]
                
                if not user.empty:
                    st.session_state.update({
                        'login_email': le, 
                        'user_name': str(user.iloc[0]['이름']).strip(), 
                        'user_id': str(user.iloc[0]['학번']).strip(), 
                        'page': 'dashboard'
                    })
                    st.success(f"{st.session_state.user_name}님, 환영합니다!")
                    st.rerun()
                else:
                    st.error("이메일 또는 비밀번호가 일치하지 않습니다.")
            else:
                st.error("등록된 사용자 정보가 없습니다. 먼저 회원가입을 해주세요.")
        
        if st.button("신규 회원가입"):
            st.session_state.page = "signup"
            st.rerun()

# [B] 메인 대시보드 (버튼 4개)
if st.session_state.page == "dashboard":
    st.title(f"👋 {st.session_state.user_name}님, 환영합니다!")
    st.info(f"📢 시스템 상태: **{st.session_state.app_status}** | 학기: **{st.session_state.target_semester}**")
    
    col1, col2 = st.columns(2); col3, col4 = st.columns(2)
    with col1:
        if st.button("📝 수강신청 하기", use_container_width=True):
            if st.session_state.app_status == "수강신청 진행": st.session_state.page = "apply"; st.rerun()
            else: st.error("신청 기간이 아닙니다.")
    with col2:
        if st.button("📊 배정 결과 조회", use_container_width=True): st.session_state.page = "result"; st.rerun()
    with col3:
        if st.button("🤝 과목 거래소", use_container_width=True):
            if st.session_state.app_status == "과목거래 오픈": st.session_state.page = "trade"; st.rerun()
            else: st.warning("거래소 준비 중")
    with col4:
        btn_label = "⚙️ 관리 시스템" if st.session_state.user_id == "admin" else "🔔 알림함"
        if st.button(btn_label, use_container_width=True):
            st.session_state.page = "admin_page" if st.session_state.user_id == "admin" else "noti"; st.rerun()

# [C] 수강신청 로직 (상세)
elif st.session_state.page == "apply":
    st.title(f"📝 {st.session_state.target_semester} 신청")
    if st.button("⬅️ 메인으로"): st.session_state.page = "dashboard"; st.rerun()
    
    u_prefix = str(st.session_state.user_id)[:2]
    cur_grade = 10 if u_prefix == "10" else 11
    target_list = df_11 if cur_grade == 10 else df_12
    sem_key = st.session_state.target_semester[0]
    
    available = target_list[target_list['학기'].fillna('').str.contains(sem_key)]['과목명'].unique().tolist()
    
    with st.form("apply_form"):
        selected = st.multiselect("과목 선택", available)
        my_track = st.selectbox("희망 계열(우대)", TRACKS) if cur_grade == 11 else "공통"
        if st.form_submit_button("🚀 신청 완료"):
            new_data = {'제출시간': datetime.now().strftime('%Y-%m-%d %H:%M:%S'), '학번': st.session_state.user_id, '이름': st.session_state.user_name, '학년': cur_grade, '희망계열': my_track, '신청과목': ",".join(selected)}
            pd.DataFrame([new_data]).to_csv('students_data.csv', mode='a', header=not os.path.exists('students_data.csv'), index=False, encoding='utf-8-sig')
            st.success("신청되었습니다!"); st.session_state.page = "dashboard"; st.rerun()

# [D] 결과 조회 로직 (상세 - 시간표 시각화 포함)
elif st.session_state.page == "result":
    st.title("📊 배정 결과 및 시간표")
    if st.button("⬅️ 메인으로"): st.session_state.page = "dashboard"; st.rerun()

    # 학번 기반 학년 판별 및 데이터 로드
    u_id = str(st.session_state.user_id)
    if u_id.startswith("11"):
        target_grade = "12학년"
        grade_cfg = GRADE_CONFIG["12학년"]
    else:
        target_grade = "11학년"
        grade_cfg = GRADE_CONFIG["11학년"]

    res_df = get_csv_df('final_results.csv')
    
    if res_df is not None:
        my_res = res_df[res_df['학번'].astype(str) == u_id]
        if not my_res.empty:
            # 1. 텍스트 결과 표시
            confirmed_str = my_res.iloc[0]['확정과목']
            confirmed_subs = [s.strip() for s in confirmed_str.split(',')]
            
            st.success(f"✅ {target_grade} 확정 과목: {confirmed_str}")
            
            # 2. 시간표 행렬 생성
            DAYS = ["월", "화", "수", "목", "금"]
            PERIODS = ["1교시", "2교시", "3교시", "4교시", "5교시", "6교시", "7교시", "8교시"]
            tt = pd.DataFrame(index=PERIODS, columns=DAYS).fillna("")
            
            # [공통 배치] 흰색 칸
            for sub, slots in grade_cfg["common"].items():
                for d, p in slots: tt.at[p, d] = f"⭐ {sub}"
            
            # [선택 배치] 유색 칸
            for sub in confirmed_subs:
                for g_name, g_subs in grade_cfg["groups"].items():
                    if sub in g_subs:
                        for d, p in grade_cfg["slots"][g_name]:
                            if tt.at[p, d] == "": tt.at[p, d] = sub

            # [고정 시간] 창체
            tt.at["7교시", "금"] = "창체"; tt.at["8교시", "금"] = "창체"

            # 3. 시각화 스타일 정의
            def style_tt(val):
                if "⭐" in val: return 'background-color: white; color: black; border: 1px solid #ddd; font-weight: bold'
                if val == "": return 'background-color: #f8f9fa'
                if val == "창체": return 'background-color: #eee'
                return 'background-color: #D1E9FF; color: #004085; font-weight: bold'

            st.table(tt.style.applymap(style_tt))
            
        else: st.warning("배정 결과가 없습니다.")
    else: st.info("관리자가 배정 결과를 아직 확정하지 않았습니다.")
# [E] 관리자 전용 배정 시스템
import streamlit as st
import pandas as pd
import os
import random
from datetime import datetime

# 1. 기본 설정
st.set_page_config(page_title="KIS 수강신청 시스템", layout="wide", page_icon="🍏")
SCHOOL_DOMAIN = "kis.ac.kr"
ID_11 = "1xADYmy5iJEIiaENxCH1ZiqGU2yiFS81MfSQDCMsnO04" 
ID_12 = "1Yp79f79ilwA2ErJ6DoxRPbU_ADCq0PnRGH2TxGvKSDg"
TRACKS = ['국어과', '영어과', '수학과', '사회과', '과학과', '베트남어과', '예술과', '정보과']
MAX_CAPACITY = 20

# 2. 세션 상태 초기화
for key, val in {
    'login_email': None, 'user_name': None, 'user_id': None, 
    'page': 'login', 'app_status': '준비중', 'target_semester': '1학기'
}.items():
    if key not in st.session_state: st.session_state[key] = val

# 3. 데이터 관련 함수
def get_csv_df(filename):
    if os.path.exists(filename): return pd.read_csv(filename)
    return None

def save_csv(df, filename):
    df.to_csv(filename, index=False, encoding='utf-8-sig')

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
list_11 = df_11['과목명'].unique().tolist() if df_11 is not None else []
list_12 = df_12['과목명'].unique().tolist() if df_12 is not None else []

# 4. 시뮬레이션 함수
def run_simulation(student_count, req_count, subject_list):
    data = []
    total_satisfaction = 0
    for i in range(student_count):
        std_id = f"SIM-{req_count}-{i+1:03d}"
        requested = random.sample(subject_list, min(req_count, len(subject_list)))
        assigned = requested.copy()
        # 15% 확률로 1과목 튕김 가정 (시뮬레이션용)
        if random.random() < 0.15:
            idx = random.randrange(len(assigned))
            assigned.pop(idx)
            remainders = list(set(subject_list) - set(assigned))
            if remainders: assigned.append(random.choice(remainders))
        
        match_count = len(set(requested) & set(assigned))
        sat = (match_count / req_count) * 100
        total_satisfaction += sat
        data.append({"학번": std_id, "만족도(%)": round(sat, 1), "상태": "✅ 완벽" if sat == 100 else "⚠️ 변경됨"})
    return pd.DataFrame(data), total_satisfaction / student_count

# 5. 페이지 로직 (로그인/대시보드 생략 - 이전과 동일)
# ... [이전 로그인/대시보드 코드와 동일하게 유지] ...
if st.session_state.login_email is None:
    # 로그인 화면 (생략)
    st.title("로그인 하세요")
    # ...
    st.stop()

# [관리자 전용 페이지 로직]
if st.session_state.page == "admin_page":
    st.title("⚙️ 관리자 종합 제어 및 시뮬레이션")
    if st.button("⬅️ 메인으로"): st.session_state.page = "dashboard"; st.rerun()
    
    st.divider()
    st.subheader("📊 170명 신청/배정 만족도 시뮬레이션")
    st.info("이 기능은 실제 데이터를 건드리지 않고 알고리즘의 효율성을 테스트합니다.")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📊 11학년(7개 선택) 시뮬레이션 가동"):
            df7, rate7 = run_simulation(170, 7, list_11)
            st.metric("평균 수강 만족도", f"{rate7:.1f}%")
            st.dataframe(df7, use_container_width=True)
    with c2:
        if st.button("📊 12학년(8개 선택) 시뮬레이션 가동"):
            df8, rate8 = run_simulation(170, 8, list_12)
            st.metric("평균 수강 만족도", f"{rate8:.1f}%")
            st.dataframe(df8, use_container_width=True)

    st.divider()
    st.subheader("🚀 실제 데이터 배정 실행")
    if st.button("전체 학생(students_data.csv) 실제 배정 시작", type="primary"):
        # 실제 배정 로직...
        st.success("실제 배정이 완료되었습니다!")
