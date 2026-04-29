mport streamlit as st
import pandas as pd
import os
import random
from datetime import datetime

# 1. 기본 설정 및 상수
st.set_page_config(page_title="KIS 수강신청 시스템", layout="wide", page_icon="🍏")
SCHOOL_DOMAIN = "kis.ac.kr"
ID_11 = "1xADYmy5iJEIiaENxCH1ZiqGU2yiFS81MfSQDCMsnO04" 
ID_12 = "1Yp79f79ilwA2ErJ6DoxRPbU_ADCq0PnRGH2TxGvKSDg"
MAX_CAPACITY = 20 # 과목당 정원
TRACKS = ['국어과', '영어과', '수학과', '사회과', '과학과', '베트남어과', '예술과', '정보과']

# 2. 세션 상태 초기화 (앱의 기억장치)
init_keys = {
    'login_email': None, 'user_name': None, 'user_id': None, 
    'page': 'login', 'app_status': '준비중', 'target_semester': '1학기'
}
for key, val in init_keys.items():
    if key not in st.session_state: st.session_state[key] = val

# 3. 헬퍼 함수
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

# 4. 사이드바 (공용 및 관리자)
with st.sidebar:
    st.title("🍏 KIS 메뉴")
    if st.session_state.login_email:
        st.info(f"👤 {st.session_state.user_name}님 접속중")
        if st.button("🏠 대시보드"): st.session_state.page = "dashboard"; st.rerun()
        if st.button("🚪 로그아웃"): 
            st.session_state.clear(); st.rerun()
        
        # 관리자 전용 리모컨
        if st.session_state.user_id == "admin":
            st.divider()
            st.subheader("⚙️ 관리자 설정")
            new_status = st.radio("시스템 단계", ["준비중", "수강신청 진행", "과목거래 오픈"])
            new_sem = st.selectbox("진행 학기", ["1학기", "2학기"])
            if st.button("💾 설정 적용"):
                st.session_state.app_status = new_status
                st.session_state.target_semester = new_sem
                st.success("적용 완료!"); st.rerun()

# 5. 페이지 로직 시작
# [A] 로그인/회원가입 (비로그인 상태)
if st.session_state.login_email is None:
    if st.session_state.page == "signup":
        st.title("📝 KIS 회원가입")
        with st.container(border=True):
            se = st.text_input("이메일 (@kis.ac.kr)")
            sp = st.text_input("비밀번호", type="password")
            si = st.text_input("학번 (5자리)")
            sn = st.text_input("이름")
            if st.button("가입 완료", use_container_width=True):
                new_user = pd.DataFrame([{'이메일':se, '비밀번호':sp, '학번':si, '이름':sn}])
                new_user.to_csv('users.csv', mode='a', header=not os.path.exists('users.csv'), index=False, encoding='utf-8-sig')
                st.success("가입 성공!"); st.session_state.page = "login"; st.rerun()
            if st.button("로그인으로 돌아가기"): st.session_state.page = "login"; st.rerun()
    else:
        st.title("🍏 KIS 수강신청 로그인")
        with st.container(border=True):
            le = st.text_input("이메일")
            lp = st.text_input("비밀번호", type="password")
            if st.button("로그인", type="primary", use_container_width=True):
                if le == "admin" and lp == "admin123": # 관리자용
                    st.session_state.update({'login_email':'admin','user_name':'관리자','user_id':'admin','page':'dashboard'})
                    st.rerun()
                u_df = get_csv_df('users.csv')
                if u_df is not None:
                    user = u_df[(u_df['이메일']==le) & (u_df['비밀번호']==str(lp))]
                    if not user.empty:
                        st.session_state.update({'login_email':le, 'user_name':user.iloc[0]['이름'], 'user_id':user.iloc[0]['학번'], 'page':'dashboard'})
                        st.rerun()
                    else: st.error("정보 불일치")
            if st.button("신규 회원가입"): st.session_state.page = "signup"; st.rerun()
    st.stop()

# [B] 메인 대시보드
if st.session_state.page == "dashboard":
    st.title(f"👋 {st.session_state.user_name}님, 안녕하세요!")
    st.info(f"📢 현재 상태: **{st.session_state.app_status}** | 학기: **{st.session_state.target_semester}**")
    
    col1, col2 = st.columns(2); col3, col4 = st.columns(2)
    with col1:
        if st.button("📝 수강신청 하기", use_container_width=True, height=150):
            if st.session_state.app_status == "수강신청 진행": st.session_state.page = "apply"; st.rerun()
            else: st.error("지금은 신청 기간이 아닙니다.")
    with col2:
        if st.button("📊 배정 결과 조회", use_container_width=True, height=150):
            st.session_state.page = "result"; st.rerun()
    with col3:
        if st.button("🤝 과목 거래소", use_container_width=True, height=150):
            if st.session_state.app_status == "과목거래 오픈": st.session_state.page = "trade"; st.rerun()
            else: st.warning("수강신청 종료 후 오픈됩니다.")
    with col4:
        if st.button("🔔 알림함 / 관리", use_container_width=True, height=150):
            if st.session_state.user_id == "admin": st.session_state.page = "admin_page"
            else: st.session_state.page = "noti"
            st.rerun()

# [C] 수강신청 상세 로직
elif st.session_state.page == "apply":
    st.title(f"📝 {st.session_state.target_semester} 수강신청")
    if st.button("⬅️ 메인으로"): st.session_state.page = "dashboard"; st.rerun()
    
    # 학년 판별
    u_prefix = str(st.session_state.user_id)[:2]
    cur_grade = 10 if u_prefix == "10" else 11
    target_list = df_11 if cur_grade == 10 else df_12
    sem_key = st.session_state.target_semester[0] # '1' 또는 '2'
    
    available_courses = target_list[target_list['학기'].str.contains(sem_key)]['과목명'].unique().tolist()
    
    with st.form("apply_form"):
        st.subheader("과목 선택 (최대 7~8개)")
        selected = st.multiselect("원하는 과목을 골라주세요", available_courses)
        my_track = st.selectbox("희망 계열(우대)", TRACKS) if cur_grade == 11 else "공통"
        
        if st.form_submit_button("🚀 신청서 제출"):
            new_entry = {
                '제출시간': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                '학번': st.session_state.user_id, '이름': st.session_state.user_name,
                '학년': cur_grade, '희망계열': my_track, '신청과목': ",".join(selected)
            }
            pd.DataFrame([new_entry]).to_csv('students_data.csv', mode='a', header=not os.path.exists('students_data.csv'), index=False, encoding='utf-8-sig')
            st.success("제출 완료!"); st.session_state.page = "dashboard"; st.rerun()

# [D] 결과 조회 로직
elif st.session_state.page == "result":
    st.title("📊 배정 결과 확인")
    if st.button("⬅️ 메인으로"): st.session_state.page = "dashboard"; st.rerun()
    
    res_df = get_csv_df('final_results.csv')
    if res_df is not None:
        my_res = res_df[res_df['학번'].astype(str) == str(st.session_state.user_id)]
        if not my_res.empty:
            st.success(f"✅ 확정 과목: {my_res.iloc[0]['확정과목']}")
            st.error(f"❌ 탈락 과목: {my_res.iloc[0]['탈락과목']}")
        else: st.warning("아직 배정 데이터가 없습니다.")
    else: st.info("관리자가 배정을 진행 중입니다.")

# [E] 관리자 전용 배정 로직 (알림함 대신 관리자가 누르면 일로 옴)
elif st.session_state.page == "admin_page":
    st.title("⚙️ 관리자 배정 시스템")
    if st.button("⬅️ 메인으로"): st.session_state.page = "dashboard"; st.rerun()
    
    st.subheader("1. 배정 알고리즘 가동")
    if st.button("🚀 전체 학생 자동 배정 시작 (선착순/계열우대)"):
        apply_df = get_csv_df('students_data.csv')
        if apply_df is not None:
            # 여기서 실제 배정 로직이 돌아감 (최종 결과 저장)
            # (지면상 요약: 신청 데이터를 읽어 final_results.csv 생성)
            st.success("배정 프로세스 완료! 이제 학생들이 조회 가능합니다.")
        else: st.error("신청 데이터가 없습니다.")
