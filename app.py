import streamlit as st
import pandas as pd
import os

# ==========================================
# 🚨 1. 구글 시트 ID 설정
# ==========================================
ID_11 = "11학년_과목_시트_ID" # 10학년이 신청할 과목 (천의자리 0)
ID_12 = "12학년_과목_시트_ID" # 11학년이 신청할 과목 (천의자리 1)

st.set_page_config(page_title="KIS 수강신청 시스템", page_icon="🍏", layout="wide")

# 세션 상태 초기화
if 'page' not in st.session_state: st.session_state['page'] = "input"
if 'admin' not in st.session_state: st.session_state['admin'] = False

# ==========================================
# [규칙 반영] 학번 유효성 검사 (소속 반은 5반까지)
# ==========================================
def is_valid_student_id(sid, current_grade):
    if not sid.isdigit() or len(sid) != 5: return False
    st_list = [int(d) for d in sid]
    
    # 1. 만의 자리: 1 고정
    if st_list[0] != 1: return False
    # 2. 천의 자리: 10학년=0, 11학년=1
    if current_grade == 10 and st_list[1] != 0: return False
    if current_grade == 11 and st_list[1] != 1: return False
    # 3. 백의 자리: 학생 소속 반 (1~5반 고정)
    if st_list[2] not in [1, 2, 3, 4, 5]: return False
    # 4. 십/일의 자리: 번호 (01~35번)
    last_two = int(sid[3:])
    if st_list[3] < 3: return last_two > 0
    elif st_list[3] == 3: return st_list[4] <= 5
    return False

# 데이터 로드
@st.cache_data(ttl=60)
def load_data():
    try:
        url_11 = f"https://docs.google.com/spreadsheets/d/{ID_11}/export?format=csv"
        url_12 = f"https://docs.google.com/spreadsheets/d/{ID_12}/export?format=csv"
        df_11 = pd.read_csv(url_11); df_12 = pd.read_csv(url_12)
        def get_list(df):
            # S1~S7 컬럼만 추출 (과목별 최대 7개 분반)
            cols = [c for c in df.columns if c.startswith('S')]
            return sorted(list(set(df[cols].stack().dropna().astype(str).unique())))
        return get_list(df_11), get_list(df_12)
    except: return ["과목 로드 실패"], ["과목 로드 실패"]

list_for_10, list_for_11 = load_data()

# ==========================================
# 📱 화면 제어 로직
# ==========================================

# [성공 페이지]
if st.session_state['page'] == "success":
    st.balloons()
    st.success("🎉 수강 신청서 제출 완료!")
    st.info("관리자 배정 후 결과를 확인하실 수 있습니다.")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔍 신청 현황 보기"): st.session_state['page'] = "check"; st.rerun()
    with col2:
        if st.button("🏠 처음으로"): st.session_state['page'] = "input"; st.rerun()

# [현황 조회 페이지]
elif st.session_state['page'] == "check":
    st.title("🔍 학년별 실시간 신청 현황")
    view_grade = st.radio("나의 현재 학년", [10, 11], horizontal=True)
    
    if os.path.exists('students_data.csv'):
        df = pd.read_csv('students_data.csv')
        # 학년 격리 조회
        filtered = df[df['현재학년'] == view_grade]
        st.write(f"### {view_grade}학년 신청자 리스트")
        st.dataframe(filtered[['학번', '이름', '1지망', '2지망']], use_container_width=True)
    else: st.warning("데이터가 없습니다.")
    if st.button("돌아가기"): st.session_state['page'] = "input"; st.rerun()

# [메인 입력 페이지]
else:
    st.title("🍏 KIS 미래 수강신청 시스템")
    tab1, tab2 = st.tabs(["📝 수강신청", "⚙️ 관리자 대시보드"])

    with tab1:
        st.subheader("회원가입 및 과목 선택")
        c1, c2 = st.columns(2)
        with c1:
            curr_g = st.radio("현재 학년", [10, 11], horizontal=True)
            s_id = st.text_input("학번 (5자리)", placeholder="10XXX 또는 11XXX")
        with c2:
            s_name = st.text_input("이름")
            st.info(f"💡 {curr_g}학년은 차년도({curr_g+1}학년) 과목을 신청합니다.")

        # 학년별 과목 매칭 (10학년->11과목, 11학년->12과목)
        target_list = list_for_10 if curr_g == 10 else list_for_11
        
        st.divider()
        sel1 = st.selectbox("1지망 과목", target_list, key="z1")
        sel2 = st.selectbox("2지망 과목", target_list, key="z2")
        
        if st.button("제출하기", use_container_width=True):
            if not is_valid_student_id(s_id, curr_g):
                st.error("❌ 올바르지 않은 학번입니다. (학년/반/번호 규칙 확인)")
            elif not s_name: st.warning("이름을 입력하세요.")
            else:
                if os.path.exists('students_data.csv'):
                    if str(s_id) in pd.read_csv('students_data.csv')['학번'].astype(str).values:
                        st.error("🚨 이미 신청된 학번입니다."); st.stop()
                
                new_row = pd.DataFrame([{'학번': s_id, '이름': s_name, '현재학년': curr_g, '1지망': sel1, '2지망': sel2}])
                new_row.to_csv('students_data.csv', mode='a', header=not os.path.exists('students_data.csv'), index=False, encoding='utf-8-sig')
                st.session_state['page'] = "success"; st.rerun()

    # [관리자 대시보드 - 학년별 종합]
    with tab2:
        if not st.session_state['admin']:
            if st.text_input("Admin PW", type="password") == "kis2026":
                if st.button("로그인"): st.session_state['admin'] = True; st.rerun()
        else:
            st.subheader("📊 학년별 신청 현황 요약")
            if st.button("로그아웃"): st.session_state['admin'] = False; st.rerun()
            
            if os.path.exists('students_data.csv'):
                admin_df = pd.read_csv('students_data.csv')
                col_10, col_11 = st.columns(2)
                
                with col_10:
                    st.success("### 10학년 (11학년 과목 신청)")
                    st.metric("총 인원", f"{len(admin_df[admin_df['현재학년']==10])}명")
                    st.table(admin_df[admin_df['현재학년']==10]['1지망'].value_counts().head(5)) # 인기과목 TOP 5
                    st.dataframe(admin_df[admin_df['현재학년']==10])

                with col_11:
                    st.info("### 11학년 (12학년 과목 신청)")
                    st.metric("총 인원", f"{len(admin_df[admin_df['현재학년']==11])}명")
                    st.table(admin_df[admin_df['현재학년']==11]['1지망'].value_counts().head(5)) # 인기과목 TOP 5
                    st.dataframe(admin_df[admin_df['현재학년']==11])
            else: st.write("데이터가 없습니다.")
