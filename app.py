import streamlit as st
import pandas as pd
import os

# ==========================================
# 🚨 1. 여기에 본인의 사본 시트 ID를 넣으세요
# ==========================================
ID_11 = "1Nfzop5JjziphJON7BGofEMJDM8TV31uY" 
ID_12 = "1NwYlD2X396Ux4NkRT_Dru3zsuolYeJrz" 

# 페이지 설정 및 보안을 위한 CSS (메뉴 숨기기)
st.set_page_config(page_title="KIS 수강신청 시스템", page_icon="🍏", layout="centered")
hide_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

# ==========================================
# 데이터 로드 함수
# ==========================================
@st.cache_data(ttl=600)
def load_course_data():
    url_11 = f"https://docs.google.com/spreadsheets/d/{ID_11}/export?format=csv"
    url_12 = f"https://docs.google.com/spreadsheets/d/{ID_12}/export?format=csv"
    try:
        df_11 = pd.read_csv(url_11)
        df_12 = pd.read_csv(url_12)
        
        def extract_courses(df):
            courses = []
            for col in df.columns:
                if col.startswith('S'):
                    courses.extend(df[col].dropna().astype(str).tolist())
            return sorted(list(set(courses)))

        return df_11, df_12, extract_courses(df_11), extract_courses(df_12)
    except Exception as e:
        st.error(f"🚨 데이터 로드 에러: {e}")
        return pd.DataFrame(), pd.DataFrame(), [], []

df_11, df_12, list_11, list_12 = load_course_data()

# ==========================================
# 수강 배정 알고리즘
# ==========================================
def run_assignment(students_df, list_11, list_12):
    # 과목별 정원을 20명으로 가정
    capacities = {course: 20 for course in (list_11 + list_12)}
    results = []
    # 고학년 우선순위 배정
    students_df = students_df.sort_values(by=['학년', '학번'], ascending=[False, True])

    for _, student in students_df.iterrows():
        assigned = False
        choices = [student['1지망'], student['2지망'], student['3지망']]
        for choice in choices:
            if pd.notna(choice) and choice in capacities and capacities[choice] > 0:
                capacities[choice] -= 1
                results.append({'학번': str(student['학번']), '이름': student['이름'], '학년': int(student['학년']), '배정과목': choice})
                assigned = True
                break
        if not assigned:
            results.append({'학번': str(student['학번']), '이름': student['이름'], '학년': int(student['학년']), '배정과목': '미배정(정원초과)'})
    
    final_df = pd.DataFrame(results)
    # 🚨 결과를 서버에 저장 (학생들이 조회할 수 있도록)
    final_df.to_csv('final_results.csv', index=False)
    return final_df

# ==========================================
# 메인 UI 레이아웃
# ==========================================
st.title("🍏 KIS 수강신청 시스템")

tab1, tab2, tab3 = st.tabs(["📝 수강신청", "🔍 결과확인", "⚙️ 관리자"])

# --- 탭 1: 학생 수강신청 ---
with tab1:
    st.subheader("정보를 입력하여 신청을 완료하세요")
    col1, col2 = st.columns(2)
    with col1:
        s_id = st.text_input("학번", placeholder="예: 202601")
        s_name = st.text_input("이름")
    with col2:
        grade = st.radio("학년 선택", [11, 12], horizontal=True)

    c_list = list_11 if grade == 11 else list_12
    st.divider()
    c1 = st.selectbox("1지망", c_list, key="sel1")
    c2 = st.selectbox("2지망", c_list, key="sel2")
    c3 = st.selectbox("3지망", c_list, key="sel3")

    if st.button("신청서 최종 제출", use_container_width=True):
        if s_id and s_name:
            if os.path.exists('students_data.csv'):
                existing = pd.read_csv('students_data.csv')
                if str(s_id) in existing['학번'].astype(str).values:
                    st.error(f"🚨 학번 {s_id}는 이미 신청되었습니다.")
                    st.stop()
            
            new_row = pd.DataFrame([{'학번': s_id, '이름': s_name, '학년': grade, '1지망': c1, '2지망': c2, '3지망': c3}])
            new_row.to_csv('students_data.csv', mode='a', header=not os.path.exists('students_data.csv'), index=False)
            st.success("✅ 신청 완료! 결과 확인 탭에서 나중에 확인하세요.")
            st.balloons()
        else:
            st.warning("정보를 모두 입력해주세요.")

# --- 탭 2: 학생 결과 확인 (신규 추가!) ---
with tab3: # 순서상 관리자를 먼저 정의 (로그인 세션 때문)
    if 'logged_in' not in st.session_state: st.session_state.logged_in = False
    if not st.session_state.logged_in:
        pw = st.text_input("관리자 암호", type="password")
        if st.button("관리자 로그인"):
            if pw == "kis2026":
                st.session_state.logged_in = True
                st.rerun()
    else:
        if st.button("로그아웃"):
            st.session_state.logged_in = False
            st.rerun()
        
        st.divider()
        if os.path.exists('students_data.csv'):
            s_data = pd.read_csv('students_data.csv')
            st.write(f"접수 인원: {len(s_data)}명")
            if st.button("✨ 배정 알고리즘 실행", type="primary", use_container_width=True):
                res = run_assignment(s_data, list_11, list_12)
                st.success("배정이 완료되었습니다! 이제 학생들이 결과를 조회할 수 있습니다.")
                st.dataframe(res)
        else:
            st.info("신청 데이터가 없습니다.")

with tab2:
    st.subheader("개인별 배정 결과 조회")
    check_id = st.text_input("학번 입력", key="check_id")
    check_grade = st.selectbox("학년 선택", [11, 12], key="check_grade")
    
    if st.button("결과 조회하기", use_container_width=True):
        if os.path.exists('final_results.csv'):
            results_df = pd.read_csv('final_results.csv')
            # 학번과 학년이 일치하는 행 찾기
            user_res = results_df[(results_df['학번'].astype(str) == str(check_id)) & (results_df['학년'] == check_grade)]
            
            if not user_res.empty:
                assigned_subject = user_res.iloc[0]['배정과목']
                st.success(f"🎊 {user_res.iloc[0]['이름']} 학생의 배정 결과는 **[{assigned_subject}]** 입니다!")
            else:
                st.error("입력하신 정보와 일치하는 배정 결과가 없습니다. 학번을 확인하시거나 관리자 배정 전인지 문의하세요.")
        else:
            st.warning("아직 전체 배정이 완료되지 않았습니다. 관리자 배정 후 조회가 가능합니다.")
