import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ==========================================
# 🚨 설정 및 ID (본인의 시트 ID로 교체 필수)
# ==========================================
ID_11 = "1Nfzop5JjziphJON7BGofEMJDM8TV31uY" 
ID_12 = "1NwYlD2X396Ux4NkRT_Dru3zsuolYeJrz" 
MAX_CAPACITY = 35  # 과목별 최대 정원
MIN_CAPACITY = 20  # 폐강 기준 최소 인원

st.set_page_config(page_title="KIS 수강신청 시스템", layout="wide", page_icon="🍏")

# --- 세션 상태 초기화 ---
if 'page' not in st.session_state: st.session_state.page = "input"
if 'admin' not in st.session_state: st.session_state.admin = False
if 'closed_list' not in st.session_state: st.session_state.closed_list = []

# CSS: 디자인 깔끔하게 정리
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .stButton>button {width: 100%; border-radius: 5px;}
    </style>
""", unsafe_allow_html=True)

# 데이터 로드 함수
@st.cache_data(ttl=60)
def load_course_data():
    try:
        url_11 = f"https://docs.google.com/spreadsheets/d/{ID_11}/export?format=csv"
        url_12 = f"https://docs.google.com/spreadsheets/d/{ID_12}/export?format=csv"
        df_11 = pd.read_csv(url_11); df_12 = pd.read_csv(url_12)
        return df_11.iloc[:, 0].dropna().tolist(), df_12.iloc[:, 0].dropna().tolist()
    except: return ["과목A", "과목B", "과목C"], ["과목X", "과목Y", "과목Z"]

list_11, list_12 = load_course_data()

# 학번 검증 함수 (11학년: 11XXX, 12학년: 12XXX)
def is_valid_sid(sid, grade):
    if not sid.isdigit() or len(sid) != 5: return False
    st_list = [int(d) for d in sid]
    if st_list[0] != 1: return False
    if grade == 11 and st_list[1] != 1: return False
    if grade == 12 and st_list[1] != 2: return False
    if st_list[2] not in [1,2,3,4,5]: return False
    last_two = int(sid[3:])
    if st_list[3] < 3: return last_two > 0
    elif st_list[3] == 3: return st_list[4] <= 5
    return False

# ==========================================
# ⚙️ 관리자 알고리즘 함수
# ==========================================
def run_initial_assignment(students_df, all_courses):
    students_df['제출시간'] = pd.to_datetime(students_df['제출시간'])
    students_df = students_df.sort_values('제출시간')
    capacities = {course: MAX_CAPACITY for course in all_courses}
    assignments = {}

    for p in ['1지망', '2지망', '3지망']:
        for _, student in students_df.iterrows():
            sid = str(student['학번'])
            if sid in assignments: continue
            choice = student[p]
            if choice in capacities and capacities[choice] > 0:
                capacities[choice] -= 1
                assignments[sid] = choice
    
    results = []
    for _, student in students_df.iterrows():
        sid = str(student['학번'])
        course = assignments.get(sid, "미배정")
        results.append({**student.to_dict(), '배정과목': course})
    
    pd.DataFrame(results).to_csv('final_results.csv', index=False, encoding='utf-8-sig')

# ==========================================
# 📱 메인 화면 로직
# ==========================================

# [1단계: 수강신청 입력]
if st.session_state.page == "input":
    st.title("🍏 KIS 수강신청 시스템")
    with st.container(border=True):
        st.subheader("📝 신청서 작성 (선착순)")
        c1, c2 = st.columns(2)
        with c1:
            s_id = st.text_input("학번 (5자리)", placeholder="예: 11101")
            s_name = st.text_input("이름")
        with c2:
            grade = st.radio("학년", [11, 12], horizontal=True)
        
        st.divider()
        clist = list_11 if grade == 11 else list_12
        sel1 = st.selectbox("1지망", clist, key="c1")
        sel2 = st.selectbox("2지망", clist, key="c2")
        sel3 = st.selectbox("3지망", clist, key="c3")
        
        if st.button("🚀 신청서 최종 제출", type="primary"):
            if not is_valid_sid(s_id, grade):
                st.error("❌ 학번 형식이 올바르지 않습니다.")
            elif not s_name:
                st.error("❌ 이름을 입력해주세요.")
            else:
                if os.path.exists('students_data.csv'):
                    exist = pd.read_csv('students_data.csv')
                    if str(s_id) in exist['학번'].astype(str).values:
                        st.error("🚨 이미 신청된 학번입니다.")
                        st.stop()
                
                ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                pd.DataFrame([{'제출시간': ts, '학번': s_id, '이름': s_name, '학년': grade, '1지망': sel1, '2지망': sel2, '3지망': sel3}]).to_csv('students_data.csv', mode='a', header=not os.path.exists('students_data.csv'), index=False, encoding='utf-8-sig')
                st.session_state.page = "success"; st.rerun()

# [2, 3, 4단계 통합: 결과 확인 / 재배정 / 교환]
elif st.session_state.page in ["success", "check"]:
    if st.session_state.page == "success": st.balloons()
    st.title("🔍 배정 결과 및 사후 관리")
    
    with st.sidebar:
        check_id = st.text_input("본인 학번 인증")
        st.button("새로고침")
        if st.button("🏠 홈으로"): st.session_state.page = "input"; st.rerun()

    if os.path.exists('final_results.csv'):
        df = pd.read_csv('final_results.csv')
        user = df[df['학번'].astype(str) == str(check_id)]
        
        if not user.empty:
            curr = user.iloc[0]['배정과목']
            st.success(f"### 현재 배정 상태: **[{curr}]**")
            
            # --- 미배정자 또는 폐강자 재선택 로직 ---
            if curr == "미배정" or "폐강" in str(curr):
                st.warning("⚠️ 과목 재선택이 필요합니다. 잔여석이 있는 과목을 고르세요.")
                counts = df['배정과목'].value_counts()
                g_list = list_11 if user.iloc[0]['학년'] == 11 else list_12
                remains = [c for c in g_list if counts.get(c, 0) < MAX_CAPACITY and "폐강" not in str(c)]
                
                selected_new = st.selectbox("선택 가능 과목", remains)
                if st.button("과목 확정하기"):
                    df.loc[df['학번'].astype(str) == str(check_id), '배정과목'] = selected_new
                    df.to_csv('final_results.csv', index=False, encoding='utf-8-sig')
                    st.success("배정이 완료되었습니다!"); st.rerun()
            
            # --- 1:1 교환 시스템 ---
            else:
                st.divider()
                st.subheader("🤝 1:1 과목 교환")
                st.info("교환을 원하는 상대방과 합의 후 상대방의 학번을 입력하세요.")
                target_id = st.text_input("상대방 학번 입력")
                if st.button("교환 승인"):
                    target_user = df[df['학번'].astype(str) == str(target_id)]
                    if not target_user.empty:
                        your_course = target_user.iloc[0]['배정과목']
                        # 교환 실행
                        df.loc[df['학번'].astype(str) == str(check_id), '배정과목'] = your_course
                        df.loc[df['학번'].astype(str) == str(target_id), '배정과목'] = curr
                        df.to_csv('final_results.csv', index=False, encoding='utf-8-sig')
                        st.success(f"✅ 교환 성공! [{your_course}] 과목으로 변경되었습니다."); st.rerun()
                    else: st.error("상대방 학번을 찾을 수 없습니다.")
        else:
            if check_id: st.error("신청 내역이 없거나 아직 배정 전입니다.")
    else:
        st.info("관리자가 배정을 진행 중입니다. 잠시 후 확인해주세요.")

# [관리자 모드]
elif st.session_state.admin:
    st.title("⚙️ 관리자 마스터 대시보드")
    if st.button("로그아웃"): st.session_state.admin = False; st.rerun()
    
    if os.path.exists('students_data.csv'):
        s_data = pd.read_csv('students_data.csv')
        st.metric("총 신청 인원", f"{len(s_data)}명")
        
        tab_a, tab_b = st.tabs(["📋 신청 명단", "⚡ 배정 및 폐강 제어"])
        
        with tab_a:
            st.dataframe(s_data, use_container_width=True)
            
        with tab_b:
            col1, col2 = st.columns(2)
            with col1:
                if st.button("1️⃣ 선착순 지망 배정 시작", type="primary"):
                    run_initial_assignment(s_data, list_11 + list_12)
                    st.success("1단계 배정 완료!")
            with col2:
                if st.button("2️⃣ 최종 폐강 확정 (20명 미만)", type="secondary"):
                    if os.path.exists('final_results.csv'):
                        res_df = pd.read_csv('final_results.csv')
                        cnt = res_df['배정과목'].value_counts()
                        closed = cnt[cnt < MIN_CAPACITY].index.tolist()
                        res_df.loc[res_df['배정과목'].isin(closed), '배정과목'] = "폐강(재선택 필요)"
                        res_df.to_csv('final_results.csv', index=False, encoding='utf-8-sig')
                        st.warning(f"폐강 처리 완료: {closed}")
                    else: st.error("배정 결과 파일이 없습니다.")
    else:
        st.info("아직 제출된 데이터가 없습니다.")

# 관리자 로그인 (비밀번호: kis2026)
if st.session_state.page == "input" and not st.session_state.admin:
    with st.expander("Admin Login"):
        pw = st.text_input("Password", type="password")
        if st.button("Login"):
            if pw == "kis2026": st.session_state.admin = True; st.rerun()
