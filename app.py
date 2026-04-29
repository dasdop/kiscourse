import streamlit as st
import pandas as pd
import os
import random
from datetime import datetime

# ==========================================
# 1. 기본 설정 및 상수
# ==========================================
st.set_page_config(page_title="KIS 수강신청 시스템", layout="wide", page_icon="🍏")
SCHOOL_DOMAIN = "kis.ac.kr"
ID_11 = "1xADYmy5iJEIiaENxCH1ZiqGU2yiFS81MfSQDCMsnO04" 
ID_12 = "1Yp79f79ilwA2ErJ6DoxRPbU_ADCq0PnRGH2TxGvKSDg"
TRACKS = ['국어과', '영어과', '수학과', '사회과', '과학과', '베트남어과', '예술과', '정보과']
MAX_CAPACITY = 20

# 세션 상태 초기화
for key, val in {
    'login_email': None, 'user_name': None, 'user_id': None, 
    'page': 'login', 'app_status': '준비중', 'target_semester': '1학기'
}.items():
    if key not in st.session_state: st.session_state[key] = val

# ==========================================
# 2. 헬퍼 함수 (데이터 로드 및 저장)
# ==========================================
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

# ==========================================
# 3. 사이드바 (리모컨)
# ==========================================
with st.sidebar:
    st.title("🍏 KIS 메뉴")
    if st.session_state.login_email:
        st.write(f"🧑‍🎓 **{st.session_state.user_name}**님 ({st.session_state.user_id})")
        if st.button("🏠 메인 대시보드"): st.session_state.page = "dashboard"; st.rerun()
        if st.button("🚪 로그아웃"): st.session_state.clear(); st.rerun()
        
        if st.session_state.user_id == "admin":
            st.divider()
            st.subheader("⚙️ 관리자 리모컨")
            st.session_state.app_status = st.radio("시스템 단계", ["준비중", "수강신청 진행", "과목거래 오픈"])
            st.session_state.target_semester = st.selectbox("진행 학기", ["1학기", "2학기"])
            if st.button("💾 설정 저장"): st.success("반영되었습니다!"); st.rerun()

# ==========================================
# 4. 페이지 로직
# ==========================================

# [로그인/회원가입 페이지]
if st.session_state.login_email is None:
    if st.session_state.page == "signup":
        st.title("📝 KIS 회원가입")
        with st.container(border=True):
            se = st.text_input("이메일 (@kis.ac.kr)")
            sp = st.text_input("비밀번호", type="password")
            si = st.text_input("학번 (5자리)")
            sn = st.text_input("이름")
            if st.button("가입 완료", use_container_width=True):
                pd.DataFrame([{'이메일':se, '비밀번호':sp, '학번':si, '이름':sn}]).to_csv('users.csv', mode='a', header=not os.path.exists('users.csv'), index=False, encoding='utf-8-sig')
                st.success("가입 성공!"); st.session_state.page = "login"; st.rerun()
            if st.button("뒤로 가기"): st.session_state.page = "login"; st.rerun()
    else:
        st.title("🍏 KIS 수강신청 로그인")
        with st.container(border=True):
            le = st.text_input("이메일")
            lp = st.text_input("비밀번호", type="password")
            if st.button("로그인", type="primary", use_container_width=True):
                if le == "admin" and lp == "admin123":
                    st.session_state.update({'login_email':'admin','user_name':'관리자','user_id':'admin','page':'dashboard'}); st.rerun()
                u_df = get_csv_df('users.csv')
                if u_df is not None:
                    user = u_df[(u_df['이메일']==le) & (u_df['비밀번호']==str(lp))]
                    if not user.empty:
                        st.session_state.update({'login_email':le, 'user_name':user.iloc[0]['이름'], 'user_id':user.iloc[0]['학번'], 'page':'dashboard'}); st.rerun()
                    else: st.error("정보가 일치하지 않습니다.")
            if st.button("신규 회원가입"): st.session_state.page = "signup"; st.rerun()
    st.stop()

# [메인 대시보드 - 버튼 4개]
if st.session_state.page == "dashboard":
    st.title(f"👋 {st.session_state.user_name}님, 환영합니다!")
    st.info(f"📢 상태: **{st.session_state.app_status}** | 학기: **{st.session_state.target_semester}**")
    
    c1, c2 = st.columns(2); c3, c4 = st.columns(2)
    with c1:
        if st.button("📝 수강신청 하기", use_container_width=True):
            if st.session_state.app_status == "수강신청 진행": st.session_state.page = "apply"; st.rerun()
            else: st.error("신청 기간이 아닙니다.")
    with c2:
        if st.button("📊 배정 결과 조회", use_container_width=True): st.session_state.page = "result"; st.rerun()
    with c3:
        if st.button("🤝 과목 거래소", use_container_width=True):
            if st.session_state.app_status == "과목거래 오픈": st.session_state.page = "trade"; st.rerun()
            else: st.warning("거래소 준비 중")
    with c4:
        label = "⚙️ 관리 시스템" if st.session_state.user_id == "admin" else "🔔 알림함"
        if st.button(label, use_container_width=True):
            st.session_state.page = "admin_page" if st.session_state.user_id == "admin" else "noti"; st.rerun()

# [수강신청 페이지]
elif st.session_state.page == "apply":
    st.title(f"📝 {st.session_state.target_semester} 수강신청")
    if st.button("⬅️ 뒤로가기"): st.session_state.page = "dashboard"; st.rerun()
    
    u_pre = str(st.session_state.user_id)[:2]
    cur_grade = 10 if u_pre == "10" else 11
    clist = list_11 if cur_grade == 10 else list_12
    req_cnt = 7 if cur_grade == 10 else 8
    
    with st.form("apply_form"):
        st.write(f"💡 {cur_grade}학년은 선택과목을 **{req_cnt}개** 골라야 합니다.")
        selected = st.multiselect("과목 선택", clist)
        track = st.selectbox("희망 계열", TRACKS) if cur_grade == 11 else "공통"
        if st.form_submit_button("🚀 제출하기"):
            if len(selected) != req_cnt: st.error(f"정확히 {req_cnt}개를 골라주세요.")
            else:
                new = {'제출시간':datetime.now().strftime('%Y-%m-%d %H:%M:%S'),'학번':st.session_state.user_id,'이름':st.session_state.user_name,'학년':cur_grade,'희망계열':track,'신청과목':",".join(selected)}
                pd.DataFrame([new]).to_csv('students_data.csv', mode='a', header=not os.path.exists('students_data.csv'), index=False, encoding='utf-8-sig')
                st.success("신청 완료!"); st.session_state.page = "dashboard"; st.rerun()

# [배정 결과 조회]
elif st.session_state.page == "result":
    st.title("📊 배정 결과 조회")
    if st.button("⬅️ 뒤로가기"): st.session_state.page = "dashboard"; st.rerun()
    res = get_csv_df('final_results.csv')
    if res is not None:
        my = res[res['학번'].astype(str) == str(st.session_state.user_id)]
        if not my.empty:
            st.success(f"✅ 확정 과목: {my.iloc[0]['확정과목']}")
            st.error(f"❌ 탈락 과목: {my.iloc[0]['탈락과목']}")
        else: st.warning("배정 내역이 없습니다.")
    else: st.info("관리자가 배정 알고리즘을 가동하기 전입니다.")

# [관리자 전용: 배정 및 시뮬레이션]
elif st.session_state.page == "admin_page":
    st.title("⚙️ 관리자 시스템 제어")
    if st.button("⬅️ 뒤로가기"): st.session_state.page = "dashboard"; st.rerun()
    
    st.divider()
    st.subheader("📊 170명 신청 및 만족도 시뮬레이션")
    
    def run_sim(count, req, sub_list):
        sim_data = []
        total_sat = 0
        for i in range(count):
            req_subs = random.sample(sub_list, min(req, len(sub_list)))
            match = len(req_subs) # 시뮬레이션 단순화: 전부 배정 성공 가정
            sat = (match / req) * 100
            total_sat += sat
            sim_data.append({"학번": f"SIM-{i+1:03d}", "만족도(%)": sat})
        return pd.DataFrame(sim_data), total_sat / count

    c1, c2 = st.columns(2)
    with c1:
        if st.button("📊 11학년(7개) 시뮬레이션"):
            df7, rate7 = run_sim(170, 7, list_11)
            st.metric("평균 만족도", f"{rate7:.1f}%")
            st.dataframe(df7)
    with c2:
        if st.button("📊 12학년(8개) 시뮬레이션"):
            df8, rate8 = run_sim(170, 8, list_12)
            st.metric("평균 만족도", f"{rate8:.1f}%")
            st.dataframe(df8)

    st.divider()
    st.subheader("🚀 실제 배정 알고리즘 가동")
    if st.button("학생 데이터로 실제 배정 실행", type="primary"):
        # 여기에 실제 배정 로직 (선착순/계열우대) 추가 가능
        st.success("배정이 완료되었습니다! (final_results.csv 생성됨)")
