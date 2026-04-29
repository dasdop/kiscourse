import streamlit as st
import pandas as pd
import os

# ==========================================
# 🚨 1. 여기에 본인의 사본 시트 ID를 넣으세요
# ==========================================
ID_11 = "1Nfzop5JjziphJON7BGofEMJDM8TV31uY" 
ID_12 = "1NwYlD2X396Ux4NkRT_Dru3zsuolYeJrz" 

# 페이지 설정 (가장 처음에 와야 함)
st.set_page_config(page_title="KIS 수강신청 시스템", page_icon="🍏", layout="centered")

# 메뉴 숨기기 및 배경 설정
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 세션 상태 초기화 (오류 방지) ---
if 'page' not in st.session_state:
    st.session_state['page'] = "input"
if 'admin' not in st.session_state:
    st.session_state['admin'] = False

# 학번 유효성 검사 (만의자리 1 / 11학년 천자리 1, 12학년 천자리 2)
def is_valid_student_id(sid, selected_grade):
    if not sid.isdigit() or len(sid) != 5: return False
    st_list = [int(d) for d in sid]
    if st_list[0] != 1: return False
    if selected_grade == 11 and st_list[1] != 1: return False
    if selected_grade == 12 and st_list[1] != 2: return False
    if st_list[2] not in [1, 2, 3, 4, 5]: return False
    last_two = int(sid[3:])
    if st_list[3] < 3: return last_two > 0
    elif st_list[3] == 3: return st_list[4] <= 5
    return False

# 구글 시트 데이터 로드
@st.cache_data(ttl=60)
def load_course_data():
    try:
        url_11 = f"https://docs.google.com/spreadsheets/d/{ID_11}/export?format=csv"
        url_12 = f"https://docs.google.com/spreadsheets/d/{ID_12}/export?format=csv"
        df_11 = pd.read_csv(url_11)
        df_12 = pd.read_csv(url_12)
        def get_list(df):
            # 시트 이미지에 맞춰 S1~S7 컬럼 추출
            s_cols = [c for c in df.columns if c.startswith('S')]
            return sorted(list(set(df[s_cols].stack().dropna().astype(str).unique())))
        return df_11, df_12, get_list(df_11), get_list(df_12)
    except Exception as e:
        st.error(f"시트 연결 오류: {e}")
        return pd.DataFrame(), pd.DataFrame(), ["과목 로드 실패"], ["과목 로드 실패"]

df_11, df_12, list_11, list_12 = load_course_data()

# 배정 알고리즘
def run_assignment(students_df, l11, l12):
    capacities = {course: 20 for course in (l11 + l12)}
    results = []
    # 12학년(고학년) 우선 배정
    students_df = students_df.sort_values(by=['학년', '학번'], ascending=[False, True])
    for _, student in students_df.iterrows():
        assigned = False
        choices = [student['1지망'], student['2지망'], student['3지망']]
        for choice in choices:
            if pd.notna(choice) and choice in capacities and capacities[choice] > 0:
                capacities[choice] -= 1
                results.append({'학번': str(student['학번']), '이름': student['이름'], '학년': int(student['학년']), '배정과목': choice})
                assigned = True; break
        if not assigned:
            results.append({'학번': str(student['학번']), '이름': student['이름'], '학년': int(student['학년']), '배정과목': '미배정(정원초과)'})
    final_df = pd.DataFrame(results)
    final_df.to_csv('final_results.csv', index=False, encoding='utf-8-sig')
    return final_df

# ==========================================
# 📱 화면 출력 로직
# ==========================================

# 1. 제출 성공 화면
if st.session_state['page'] == "success":
    st.title("🍏 신청 완료")
    st.balloons()
    st.success("신청서 제출이 성공적으로 완료되었습니다!")
    st.info("관리자가 확인 후 배정을 진행할 예정입니다.")
    if st.button("🔍 내 결과 확인"):
        st.session_state['page'] = "check"; st.rerun()
    if st.button("🏠 처음으로 돌아가기"):
        st.session_state['page'] = "input"; st.rerun()

# 2. 결과 확인 화면
elif st.session_state['page'] == "check":
    st.title("🔍 수강 배정 결과 조회")
    check_id = st.text_input("학번 5자리를 입력하세요")
    if st.button("결과 조회하기", type="primary"):
        if os.path.exists('final_results.csv'):
            res_df = pd.read_csv('final_results.csv')
            match = res_df[res_df['학번'].astype(str) == str(check_id)]
            if not match.empty:
                st.success(f"🎊 {match.iloc[0]['이름']} 학생: **[{match.iloc[0]['배정과목']}]**")
            else: st.error("해당 학번의 결과를 찾을 수 없습니다.")
        else:
            st.warning("👨‍🏫 아직 관리자가 수강 배정을 진행 중입니다. 잠시만 기다려주세요.")
    if st.button("뒤로 가기"):
        st.session_state['page'] = "input"; st.rerun()

# 3. 메인 수강신청 화면
else:
    st.title("🍏 KIS 수강신청 시스템")
    tab1, tab2 = st.tabs(["📝 수강신청", "⚙️ 관리자"])

    with tab1:
        st.subheader("정보 입력")
        c1, c2 = st.columns(2)
        with c1:
            s_id = st.text_input("학번 (5자리)", placeholder="11101")
            s_name = st.text_input("이름")
        with c2:
            grade = st.radio("학년", [11, 12], horizontal=True)

        clist = list_11 if grade == 11 else list_12
        st.divider()
        sel1 = st.selectbox("1지망", clist, key="z1")
        sel2 = st.selectbox("2지망", clist, key="z2")
        sel3 = st.selectbox("3지망", clist, key="z3")

        if st.button("신청서 제출", use_container_width=True):
            if not is_valid_student_id(s_id, grade):
                st.error("❌ 올바르지 않은 학번 형식입니다.")
            elif not s_name:
                st.warning("이름을 입력하세요.")
            else:
                if os.path.exists('students_data.csv'):
                    existing = pd.read_csv('students_data.csv')
                    if str(s_id) in existing['학번'].astype(str).values:
                        st.error("🚨 이미 신청된 학번입니다.")
                        st.stop()
                
                new_data = pd.DataFrame([{'학번': s_id, '이름': s_name, '학년': grade, '1지망': sel1, '2지망': sel2, '3지망': sel3}])
                new_data.to_csv('students_data.csv', mode='a', header=not os.path.exists('students_data.csv'), index=False, encoding='utf-8-sig')
                st.session_state['page'] = "success"
                st.rerun()

    with tab2:
        if not st.session_state['admin']:
            pw = st.text_input("Admin Password", type="password")
            if st.button("로그인"):
                if pw == "kis2026": 
                    st.session_state['admin'] = True; st.rerun()
                else: st.error("비번 틀림")
        else:
            if st.button("로그아웃"): 
                st.session_state['admin'] = False; st.rerun()
            if os.path.exists('students_data.csv'):
                s_data = pd.read_csv('students_data.csv')
                if st.button("✨ 배정 알고리즘 실행", type="primary"):
                    run_assignment(s_data, list_11, list_12)
                    st.success("배정 완료! 이제 학생들이 조회 가능합니다.")
