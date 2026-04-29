import streamlit as st
import pandas as pd
import os

# ==========================================
# 🚨 1. 본인의 사본 시트 ID를 넣으세요
# ==========================================
ID_11 = "1Nfzop5JjziphJON7BGofEMJDM8TV31uY" 
ID_12 = "1NwYlD2X396Ux4NkRT_Dru3zsuolYeJrz" 

st.set_page_config(page_title="KIS 수강신청 시스템", page_icon="🍏", layout="centered")

# 메뉴 숨기기 CSS
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# --- 세션 상태 초기화 ---
if 'page' not in st.session_state:
    st.session_state.page = "input"  # input, success, check 세 가지 상태

# 학번 유효성 검사 함수
def is_valid_student_id(sid, selected_grade):
    if not sid.isdigit() or len(sid) != 5: return False
    st_list = [int(d) for d in sid]
    if st_list[0] != 1: return False
    if selected_grade == 10 and st_list[1] != 0: return False
    if selected_grade == 11 and st_list[1] != 1: return False
    if st_list[2] not in [1, 2, 3, 4, 5]: return False
    last_two = int(sid[3:])
    if st_list[3] < 3: return last_two > 0
    elif st_list[3] == 3: return st_list[4] <= 5
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

# ==========================================
# 📱 화면 로직 제어
# ==========================================

# 1️⃣ 제출 완료 페이지
if st.session_state.page == "success":
    st.balloons()
    st.success("🎉 신청서 제출이 완료되었습니다!")
    st.info("관리자가 확인 후 배정할 예정입니다.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 내 결과 확인하러 가기", use_container_width=True):
            st.session_state.page = "check"
            st.rerun()
    with col2:
        if st.button("🏠 처음으로 돌아가기", use_container_width=True):
            st.session_state.page = "input"
            st.rerun()

# 2️⃣ 결과 확인 페이지 (개별 이동 가능하게 분리)
elif st.session_state.page == "check":
    st.title("🔍 수강 배정 결과 조회")
    check_id = st.text_input("학번 5자리를 입력하세요")
    
    if st.button("조회하기", type="primary", use_container_width=True):
        if os.path.exists('final_results.csv'):
            res_df = pd.read_csv('final_results.csv')
            user_res = res_df[res_df['학번'].astype(str) == str(check_id)]
            if not user_res.empty:
                st.success(f"🎊 {user_res.iloc[0]['이름']} 학생의 배정 과목은 **[{user_res.iloc[0]['배정과목']}]** 입니다.")
            else:
                st.error("해당 학번의 배정 결과를 찾을 수 없습니다.")
        else:
            # 관리자가 아직 파일을 생성하지 않았을 때 출력되는 문구
            st.warning("👨‍🏫 아직 관리자가 수강 배정을 진행 중입니다. 확인 후 배정 예정이니 잠시만 기다려주세요.")
    
    if st.button("돌아가기"):
        st.session_state.page = "input"
        st.rerun()

# 3️⃣ 메인 입력 페이지
else:
    st.title("🍏 KIS 수강신청 시스템")
    tab1, tab2 = st.tabs(["📝 수강신청", "⚙️ 관리자"])

    with tab1:
        st.subheader("정보를 입력하세요")
        c1, c2 = st.columns(2)
        with c1:
            s_id = st.text_input("학번", placeholder="10101")
            s_name = st.text_input("이름")
        with c2:
            grade = st.radio("학년", [10, 11], horizontal=True)

        clist = list_11 if grade == 11 else list_11
        st.divider()
        sel1 = st.selectbox("1지망", clist, key="s1")
        sel2 = st.selectbox("2지망", clist, key="s2")
        sel3 = st.selectbox("3지망", clist, key="s3")

        if st.button("신청서 최종 제출", use_container_width=True):
            if not is_valid_student_id(s_id, grade):
                st.error("❌ 올바르지않은학번입니다")
            elif not s_name:
                st.warning("이름을 입력해주세요.")
            else:
                if os.path.exists('students_data.csv'):
                    existing = pd.read_csv('students_data.csv')
                    if str(s_id) in existing['학번'].astype(str).values:
                        st.error("🚨 이미 신청된 학번입니다.")
                        st.stop()
                
                new_row = pd.DataFrame([{'학번': s_id, '이름': s_name, '학년': grade, '1지망': sel1, '2지망': sel2, '3지망': sel3}])
                new_row.to_csv('students_data.csv', mode='a', header=not os.path.exists('students_data.csv'), index=False)
                
                st.session_state.page = "success"
                st.rerun()

    with tab2:
        st.subheader("관리자 로그인")
        if 'admin' not in st.session_state: st.session_state.admin = False
        if not st.session_state.admin:
            pw = st.text_input("Password", type="password")
            if st.button("Login"):
                if pw == "kis2026": 
                    st.session_state.admin = True
                    st.rerun()
                else: st.error("비밀번호 틀림")
        else:
            if st.button("Logout"): 
                st.session_state.admin = False
                st.rerun()
            if os.path.exists('students_data.csv'):
                s_data = pd.read_csv('students_data.csv')
                if st.button("✨ 수강 배정 실행 (결과 생성)", type="primary"):
                    # 배정 로직 (생략 - 이전과 동일)
                    # final_df.to_csv('final_results.csv', index=False) 가 반드시 포함되어야 함
                    st.success("배정 완료! 이제 학생들이 조회할 수 있습니다.")
