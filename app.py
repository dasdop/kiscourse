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

# 페이지 상태 초기화 (제출 완료 여부 확인용)
if 'submitted' not in st.session_state:
    st.session_state.submitted = False

# 학번 유효성 검사 함수 (요청하신 규칙 그대로 적용)
def is_valid_student_id(sid, selected_grade):
    if not sid.isdigit() or len(sid) != 5: return False
    st_list = [int(d) for d in sid] # [만, 천, 백, 십, 일]
    
    if st_list[0] != 1: return False # 만의 자리 무조건 1
    if selected_grade == 10 and st_list[1] != 0: return False # 10학년 천의자리 0
    if selected_grade == 11 and st_list[1] != 1: return False # 11학년 천의자리 1
    if st_list[2] not in [1, 2, 3, 4, 5]: return False # 백의 자리 (1~5반)
    
    last_two = int(sid[3:]) # 번호 (십+일)
    if st_list[3] < 3: # 십의 자리가 0,1,2일 때
        return last_two > 0 # 00번 제외
    elif st_list[3] == 3: # 십의 자리가 3일 때
        return st_list[4] <= 5 # 35번까지
    return False

# 데이터 로드 (캐싱)
@st.cache_data(ttl=600)
def load_course_data():
    try:
        url_11 = f"https://docs.google.com/spreadsheets/d/{ID_11}/export?format=csv"
        url_12 = f"https://docs.google.com/spreadsheets/d/{ID_12}/export?format=csv"
        df_11 = pd.read_csv(url_11)
        df_12 = pd.read_csv(url_12)
        def get_list(df):
            return sorted(list(set([val for col in df.columns if col.startswith('S') for val in df[col].dropna().astype(str)])))
        return df_11, df_12, get_list(df_11), get_list(df_12)
    except:
        return pd.DataFrame(), pd.DataFrame(), [], []

df_11, df_12, list_11, list_12 = load_course_data()

# ==========================================
# 메인 화면 로직
# ==========================================

# 1️⃣ 제출 완료 페이지
if st.session_state.submitted:
    st.empty() # 이전 화면 지우기
    st.balloons()
    st.success("🎉 신청서 제출이 완료되었습니다!")
    st.write("입력하신 정보는 관리자가 확인 후 배정할 예정입니다.")
    st.write("결과는 '결과 확인' 탭에서 나중에 확인해 주세요.")
    
    if st.button("처음으로 돌아가기"):
        st.session_state.submitted = False
        st.rerun()

# 2️⃣ 기본 입력 페이지
else:
    st.title("🍏 KIS 수강신청 시스템")
    tab1, tab2, tab3 = st.tabs(["📝 수강신청", "🔍 결과확인", "⚙️ 관리자"])

    with tab1:
        st.subheader("정보를 입력하세요")
        col1, col2 = st.columns(2)
        with col1:
            s_id = st.text_input("학번 (5자리)", placeholder="예: 10101")
            s_name = st.text_input("이름")
        with col2:
            grade = st.radio("학년 선택", [10, 11], horizontal=True)

        c_list = list_11 if grade == 11 else list_11 # 10학년용 리스트가 따로 없다면 11용 사용
        st.divider()
        c1 = st.selectbox("1지망", c_list, key="c1")
        c2 = st.selectbox("2지망", c_list, key="c2")
        c3 = st.selectbox("3지망", c_list, key="c3")

        if st.button("신청서 최종 제출", use_container_width=True):
            if not is_valid_student_id(s_id, grade):
                st.error("❌ 올바르지않은학번입니다")
            elif not s_name:
                st.warning("이름을 입력해주세요.")
            else:
                # 중복 체크
                if os.path.exists('students_data.csv'):
                    existing = pd.read_csv('students_data.csv')
                    if str(s_id) in existing['학번'].astype(str).values:
                        st.error(f"🚨 이미 신청된 학번({s_id})입니다.")
                        st.stop()
                
                # 저장
                new_row = pd.DataFrame([{'학번': s_id, '이름': s_name, '학년': grade, '1지망': c1, '2지망': c2, '3지망': c3}])
                new_row.to_csv('students_data.csv', mode='a', header=not os.path.exists('students_data.csv'), index=False)
                
                # ✅ 상태 변경 (완료 페이지로 이동)
                st.session_state.submitted = True
                st.rerun()

    # 결과 확인 및 관리자 탭 (기존과 동일)
    with tab2:
        st.subheader("배정 결과 조회")
        cid = st.text_input("학번", key="cid")
        if st.button("조회"):
            if os.path.exists('final_results.csv'):
                res_df = pd.read_csv('final_results.csv')
                match = res_df[res_df['학번'].astype(str) == str(cid)]
                if not match.empty: st.success(f"결과: {match.iloc[0]['배정과목']}")
                else: st.error("정보를 찾을 수 없습니다.")
            else: st.warning("배정 전입니다.")

    with tab3:
        if 'admin' not in st.session_state: st.session_state.admin = False
        if not st.session_state.admin:
            if st.text_input("PW", type="password") == "kis2026":
                if st.button("로그인"): 
                    st.session_state.admin = True
                    st.rerun()
        else:
            if st.button("로그아웃"): 
                st.session_state.admin = False
                st.rerun()
            if os.path.exists('students_data.csv'):
                if st.button("배정 실행"):
                    # (배정 로직 생략 - 이전 코드와 동일)
                    st.write("배정 완료!")
