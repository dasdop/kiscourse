import streamlit as st
import pandas as pd
import os

# ==========================================
# 🚨 1. 여기에 본인의 사본 시트 ID를 넣으세요
# ==========================================
ID_11 = "1Nfzop5JjziphJON7BGofEMJDM8TV31uY" 
ID_12 = "1NwYlD2X396Ux4NkRT_Dru3zsuolYeJrz" 

# 페이지 설정 및 코드 숨기기 CSS
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
# 데이터 로드 함수 (S1~S7 컬럼 대응)
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
    capacities = {course: 20 for course in (list_11 + list_12)}
    results = []
    students_df = students_df.sort_values(by=['학년', '학번'], ascending=[False, True])

    for _, student in students_df.iterrows():
        assigned = False
        choices = [student['1지망'], student['2지망'], student['3지망']]
        for choice in choices:
            if pd.notna(choice) and choice in capacities and capacities[choice] > 0:
                capacities[choice] -= 1
                results.append({'학번': student['학번'], '이름': student['이름'], '학년': student['학년'], '배정과목': choice})
                assigned = True
                break
        if not assigned:
            results.append({'학번': student['학번'], '이름': student['이름'], '학년': student['학년'], '배정과목': '미배정(정원초과)'})
    return pd.DataFrame(results)

# ==========================================
# 웹 UI 및 로그인 로직
# ==========================================
st.title("🍏 KIS 수강신청 및 배정 시스템")

tab1, tab2 = st.tabs(["📝 학생 수강신청", "⚙️ 관리자 모드"])

# --- 탭 1: 학생 수강신청 ---
with tab1:
    st.subheader("학생 정보 입력")
    col1, col2 = st.columns(2)
    with col1:
        s_id = st.text_input("학번")
        s_name = st.text_input("이름")
    with col2:
        grade = st.radio("학년", [11, 12], horizontal=True)

    c_list = list_11 if grade == 11 else list_12
    st.divider()
    c1 = st.selectbox("1지망 과목", c_list)
    c2 = st.selectbox("2지망 과목", c_list)
    c3 = st.selectbox("3지망 과목", c_list)

    if st.button("신청서 제출", use_container_width=True):
        if s_id and s_name:
            is_duplicate = False
            
            # 이미 제출된 데이터가 있는지 확인하고 중복 검사
            if os.path.exists('students_data.csv'):
                existing_data = pd.read_csv('students_data.csv')
                # 입력한 학번(문자열 처리)이 기존 학번 목록에 있는지 검사
                if str(s_id) in existing_data['학번'].astype(str).values:
                    is_duplicate = True
            
            if is_duplicate:
                st.error(f"🚨 이미 수강신청이 완료된 학번({s_id})입니다. 중복 제출은 불가능합니다!")
            else:
                new_row = pd.DataFrame([{'학번': s_id, '이름': s_name, '학년': grade, '1지망': c1, '2지망': c2, '3지망': c3}])
                new_row.to_csv('students_data.csv', mode='a', header=not os.path.exists('students_data.csv'), index=False)
                st.success("✅ 신청이 완료되었습니다!")
                st.balloons() # 축하 풍선 효과! 🎈
        else:
            st.warning("학번과 이름을 입력해주세요.")

# --- 탭 2: 관리자 모드 (로그인 기능) ---
with tab2:
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

    if not st.session_state.logged_in:
        st.subheader("🔒 관리자 로그인")
        pw = st.text_input("비밀번호를 입력하세요", type="password")
        if st.button("로그인"):
            if pw == "kis2026": 
                st.session_state.logged_in = True
                st.rerun()
            else:
                st.error("비밀번호가 틀렸습니다.")
    else:
        st.subheader("⚙️ 관리자 제어판")
        if st.button("로그아웃"):
            st.session_state.logged_in = False
            st.rerun()
            
        st.divider()
        
        if os.path.exists('students_data.csv'):
            s_data = pd.read_csv('students_data.csv')
            st.write(f"현재 신청 인원: **{len(s_data)}명**")
            
            with st.expander("전체 신청 명단 보기"):
                st.dataframe(s_data)
            
            if st.button("✨ 수강 배정 실행", type="primary", use_container_width=True):
                final_df = run_assignment(s_data, list_11, list_12)
                st.subheader("📋 배정 결과")
                st.dataframe(final_df, use_container_width=True)
                
                csv = final_df.to_csv(index=False).encode('utf-8-sig')
                st.download_button("엑셀 파일로 결과 다운로드", data=csv, file_name="assignment_results.csv", mime="text/csv")
        else:
            st.info("아직 신청한 학생이 없습니다.")
