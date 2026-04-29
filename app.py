import streamlit as st
import pandas as pd
import os

# ==========================================
# 🚨 1. 여기에 사본 시트 ID 2개를 꼭 넣으세요!
# ==========================================
ID_11 = "1Nfzop5JjziphJON7BGofEMJDM8TV31uY" 
ID_12 = "1NwYlD2X396Ux4NkRT_Dru3zsuolYeJrz" 

@st.cache_data(ttl=600)
def load_course_data():
    url_11 = f"https://docs.google.com/spreadsheets/d/{ID_11}/export?format=csv"
    url_12 = f"https://docs.google.com/spreadsheets/d/{ID_12}/export?format=csv"
    try:
        df_11 = pd.read_csv(url_11)
        df_12 = pd.read_csv(url_12)
        
        # S1 ~ S7 컬럼에서 과목 이름들을 모두 긁어모아서 리스트로 만드는 마법의 코드!
        def extract_courses(df):
            courses = []
            for col in df.columns:
                if col.startswith('S'): # S1, S2 등 S로 시작하는 컬럼만 찾음
                    courses.extend(df[col].dropna().astype(str).tolist())
            # 중복된 과목명 제거하고 가나다순 정렬
            return sorted(list(set(courses)))

        list_11 = extract_courses(df_11)
        list_12 = extract_courses(df_12)
        
        return df_11, df_12, list_11, list_12
    except Exception as e:
        st.error(f"🚨 구글 시트 접근 에러: {e}")
        return pd.DataFrame(), pd.DataFrame(), [], []

df_11, df_12, list_11, list_12 = load_course_data()

# ==========================================
# 2. 수강 배정 알고리즘 (임시 정원 20명으로 설정)
# ==========================================
def run_assignment(students_df, list_11, list_12):
    # 정원 데이터가 시트에 없으므로, 모든 과목의 임시 정원을 20명으로 설정합니다.
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
# 3. 웹사이트 UI 화면
# ==========================================
st.set_page_config(page_title="KIS 수강신청 시스템", page_icon="🍏", layout="centered")
st.title("🍏 KIS 수강신청 및 배정 시스템")

tab1, tab2 = st.tabs(["📝 학생 수강신청", "⚙️ 관리자 대시보드"])

with tab1:
    st.subheader("1. 학생 정보 및 학년 선택")
    col1, col2 = st.columns(2)
    with col1:
        student_id = st.text_input("학번을 입력하세요 (예: 202601)")
        student_name = st.text_input("이름을 입력하세요")
    with col2:
        grade = st.radio("학년을 선택하세요", [11, 12], horizontal=True)

    # 학년에 맞는 과목 리스트 띄우기
    if grade == 11 and list_11: course_list = list_11
    elif grade == 12 and list_12: course_list = list_12
    else: course_list = ["데이터 대기중..."]

    st.divider()
    st.subheader(f"2. {grade}학년 희망 과목 선택")
    choice_1 = st.selectbox("1지망 과목", course_list, key="c1")
    choice_2 = st.selectbox("2지망 과목", course_list, key="c2")
    choice_3 = st.selectbox("3지망 과목", course_list, key="c3")

    if st.button("🚀 신청서 최종 제출", use_container_width=True):
        if not student_id or not student_name:
            st.error("학번과 이름을 모두 입력해주세요!")
        else:
            new_data = pd.DataFrame([{'학번': student_id, '이름': student_name, '학년': grade, '1지망': choice_1, '2지망': choice_2, '3지망': choice_3}])
            new_data.to_csv('students_data.csv', mode='a', header=not os.path.exists('students_data.csv'), index=False)
            st.success(f"✅ {student_name} 학생({grade}학년) 수강신청 접수 완료!")

with tab2:
    st.subheader("수강 신청 현황 및 배정")
    if os.path.exists('students_data.csv'):
        students_df = pd.read_csv('students_data.csv')
        st.write(f"현재 총 **{len(students_df)}명**의 학생이 신청을 완료했습니다.")
        with st.expander("신청 명단 전체 보기"): st.dataframe(students_df)
        
        if st.button("✨ 수강 배정 알고리즘 실행하기", type="primary"):
            final_results = run_assignment(students_df, list_11, list_12)
            st.success("배정 완료!")
            st.dataframe(final_results, use_container_width=True)
    else:
        st.info("아직 제출된 학생 데이터가 없습니다.")
