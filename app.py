import streamlit as st
import pandas as pd
import os

# ==========================================
# 🚨 1. 여기에 본인의 사본 시트 ID를 넣으세요
# ==========================================
ID_11 = "1Nfzop5JjziphJON7BGofEMJDM8TV31uY" 
ID_12 = "1NwYlD2X396Ux4NkRT_Dru3zsuolYeJrz" 

st.set_page_config(page_title="KIS 수강신청 시스템", page_icon="🍏", layout="centered")

# 메뉴 숨기기 CSS
hide_style = """
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
"""
st.markdown(hide_style, unsafe_allow_html=True)

# ==========================================
# [신규] 학번 유효성 검사 함수
# ==========================================
def is_valid_student_id(sid, selected_grade):
    if not sid.isdigit() or len(sid) != 5:
        return False
    
    # 각 자리수 추출 (문자열 인덱스 활용)
    ten_thousand = int(sid[0]) # 만의 자리
    thousand = int(sid[1])     # 천의 자리
    hundred = int(sid[2])      # 백의 자리
    ten = int(sid[3])          # 십의 자리
    one = int(sid[4])          # 일의 자리
    last_two = int(sid[3:])    # 마지막 두 자리 (번호)

    # 1. 만의 자리는 무조건 1
    if ten_thousand != 1: return False
    
    # 2. 천의 자리 (학년별 조건)
    if selected_grade == 10 and thousand != 0: return False
    if selected_grade == 11 and thousand != 1: return False
    
    # 3. 백의 자리 (반: 1~5반)
    if hundred not in [1, 2, 3, 4, 5]: return False
    
    # 4. 십의 자리 & 일의 자리 (번호 제한)
    if ten < 3: # 0, 1, 2일 때는 무상관 (단, 00번은 없으므로 01 이상 조건 추가 가능)
        if last_two == 0: return False 
        return True
    elif ten == 3: # 3일 때는 5까지만 (30~35)
        if one <= 5: return True
        else: return False
    else: # 십의 자리가 4 이상인 경우
        return False

# 데이터 로드 및 배정 알고리즘 (이전과 동일)
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
        return pd.DataFrame(), pd.DataFrame(), [], []

df_11, df_12, list_11, list_12 = load_course_data()

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
                results.append({'학번': str(student['학번']), '이름': student['이름'], '학년': int(student['학년']), '배정과목': choice})
                assigned = True
                break
        if not assigned:
            results.append({'학번': str(student['학번']), '이름': student['이름'], '학년': int(student['학년']), '배정과목': '미배정(정원초과)'})
    final_df = pd.DataFrame(results)
    final_df.to_csv('final_results.csv', index=False)
    return final_df

# ==========================================
# 메인 UI
# ==========================================
st.title("🍏 KIS 수강신청 시스템")
tab1, tab2, tab3 = st.tabs(["📝 수강신청", "🔍 결과확인", "⚙️ 관리자"])

with tab1:
    st.subheader("정보를 입력하세요")
    col1, col2 = st.columns(2)
    with col1:
        s_id = st.text_input("학번 (5자리 숫자)", placeholder="예: 10101")
        s_name = st.text_input("이름")
    with col2:
        # 질문에는 10학년, 11학년 조건이 있어서 선택지를 10, 11로 수정했습니다.
        grade = st.radio("학년 선택", [10, 11], horizontal=True)

    c_list = list_11 if grade == 11 else (list_11 if grade == 10 else []) # 10학년 데이터가 따로 없다면 일단 11용 리스트 활용
    st.divider()
    c1 = st.selectbox("1지망", c_list, key="sel1")
    c2 = st.selectbox("2지망", c_list, key="sel2")
    c3 = st.selectbox("3지망", c_list, key="sel3")

    if st.button("신청서 최종 제출", use_container_width=True):
        if s_id and s_name:
            # 🚨 학번 유효성 검사 실행
            if not is_valid_student_id(s_id, grade):
                st.error("❌ 올바르지않은학번입니다")
            else:
                if os.path.exists('students_data.csv'):
                    existing = pd.read_csv('students_data.csv')
                    if str(s_id) in existing['학번'].astype(str).values:
                        st.error(f"🚨 학번 {s_id}는 이미 신청되었습니다.")
                        st.stop()
                
                new_row = pd.DataFrame([{'학번': s_id, '이름': s_name, '학년': grade, '1지망': c1, '2지망': c2, '3지망': c3}])
                new_row.to_csv('students_data.csv', mode='a', header=not os.path.exists('students_data.csv'), index=False)
                st.success("✅ 신청 완료!")
                st.balloons()
        else:
            st.warning("정보를 모두 입력해주세요.")

# 관리자 및 결과확인 탭은 이전과 동일하게 유지...
with tab3:
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
        if os.path.exists('students_data.csv'):
            s_data = pd.read_csv('students_data.csv')
            if st.button("✨ 배정 알고리즘 실행", type="primary", use_container_width=True):
                res = run_assignment(s_data, list_11, list_12)
                st.success("배정 완료!")
                st.dataframe(res)
        else: st.info("신청 데이터가 없습니다.")

with tab2:
    st.subheader("개인별 결과 조회")
    check_id = st.text_input("학번 입력", key="check_id")
    check_grade = st.selectbox("학년 선택", [10, 11], key="check_grade")
    if st.button("조회하기"):
        if os.path.exists('final_results.csv'):
            results_df = pd.read_csv('final_results.csv')
            user_res = results_df[(results_df['학번'].astype(str) == str(check_id)) & (results_df['학년'] == check_grade)]
            if not user_res.empty:
                st.success(f"🎊 배정 결과: **[{user_res.iloc[0]['배정과목']}]**")
            else: st.error("일치하는 결과가 없습니다.")
        else: st.warning("배정 전입니다.")
