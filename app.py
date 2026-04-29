import streamlit as st
import pandas as pd
import os

# ==========================================
# 🚨 1. 본인의 사본 시트 ID를 넣으세요
# ==========================================
ID_11 = "1Nfzop5JjziphJON7BGofEMJDM8TV31uY" 
ID_12 = "1NwYlD2X396Ux4NkRT_Dru3zsuolYeJrz" 

st.set_page_config(page_title="KIS 수강신청 시스템", page_icon="🍏", layout="centered")

# 메뉴 및 헤더 숨기기
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

if 'page' not in st.session_state:
    st.session_state.page = "input"

# ==========================================
# [최종 수정] 학번 유효성 검사 함수
# ==========================================
def is_valid_student_id(sid, selected_grade):
    if not sid.isdigit() or len(sid) != 5: return False
    
    st_list = [int(d) for d in sid] # [만, 천, 백, 십, 일]
    
    # 1. 만의 자리는 무조건 1
    if st_list[0] != 1: return False
    
    # 2. 천의 자리 (11학년=1, 12학년=2)
    if selected_grade == 11 and st_list[1] != 1: return False
    if selected_grade == 12 and st_list[1] != 2: return False
    
    # 3. 백의 자리 (1~5반)
    if st_list[2] not in [1, 2, 3, 4, 5]: return False
    
    # 4. 번호 (01~35번 규칙)
    ten = st_list[3]
    one = st_list[4]
    last_two = int(sid[3:])
    
    if ten < 3: # 00~29번대
        return last_two > 0 # 00번은 제외
    elif ten == 3: # 30번대
        return one <= 5 # 35번까지만
    return False

# 데이터 로드
@st.cache_data(ttl=600)
def load_course_data():
    try:
        url_11 = f"https://docs.google.com/spreadsheets/d/{ID_11}/export?format=csv"
        url_12 = f"https://docs.google.com/spreadsheets/d/{ID_12}/export?format=csv"
        df_11 = pd.read_csv(url_11); df_12 = pd.read_csv(url_12)
        def get_list(df): return sorted(list(set([val for col in df.columns if col.startswith('S') for val in df[col].dropna().astype(str)])))
        return df_11, df_12, get_list(df_11), get_list(df_12)
    except: return pd.DataFrame(), pd.DataFrame(), [], []

df_11, df_12, list_11, list_12 = load_course_data()

# 배정 알고리즘
def run_assignment(students_df, list_11, list_12):
    capacities = {course: 20 for course in (list_11 + list_12)}
    results = []
    # 12학년 우선 배정
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
    final_df.to_csv('final_results.csv', index=False)
    return final_df

# ==========================================
# 화면 로직
# ==========================================

# 제출 완료 페이지
if st.session_state.page == "success":
    st.balloons()
    st.success("🎉 신청서 제출이 완료되었습니다!")
    st.info("관리자가 확인 후 배정할 예정입니다.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 내 결과 확인", use_container_width=True):
            st.session_state.page = "check"; st.rerun()
    with col2:
        if st.button("🏠 홈으로", use_container_width=True):
            st.session_state.page = "input"; st.rerun()

# 결과 확인 페이지
elif st.session_state.page == "check":
    st.title("🔍 배정 결과 조회")
    check_id = st.text_input("학번 5자리를 입력하세요")
    if st.button("조회하기", type="primary", use_container_width=True):
        if os.path.exists('final_results.csv'):
            res_df = pd.read_csv('final_results.csv')
            user_res = res_df[res_df['학번'].astype(str) == str(check_id)]
            if not user_res.empty:
                st.success(f"🎊 {user_res.iloc[0]['이름']} 학생: **[{user_res.iloc[0]['배정과목']}]**")
            else: st.error("해당 학번의 결과를 찾을 수 없습니다.")
        else: st.warning("👨‍🏫 관리자가 확인 후 배정 예정입니다.")
    if st.button("돌아가기"):
        st.session_state
