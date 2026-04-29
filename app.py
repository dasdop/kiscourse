import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ==========================================
# 🚨 기본 설정 (시트 ID 입력)
# ==========================================
ID_11 = "1xADYmy5iJEIiaENxCH1ZiqGU2yiFS81MfSQDCMsnO04"  # <- 여기에 11학년 시트 ID를 넣으세요
ID_12 = "11Yp79f79ilwA2ErJ6DoxRPbU_ADCq0PnRGH2TxGvKSDgD"  # <- 여기에 12학년 시트 ID를 넣으세요
SCHOOL_DOMAIN = "kshcm.net"  
MAX_CAPACITY = 35  

# 11학년(예비12학년) 전용 희망계열
TRACKS = ['인문사회계열', '자연공학계열', '예체능계열', '자유전공']

st.set_page_config(page_title="KIS 수강신청", layout="wide", page_icon="🍏")

# --- 세션 상태 초기화 ---
for key in ['login_email', 'user_name', 'user_id', 'admin']:
    if key not in st.session_state: st.session_state[key] = None if key != 'admin' else False
if 'page' not in st.session_state: st.session_state.page = "login"

# ==========================================
# 🛠️ 헬퍼 함수 
# ==========================================
def is_valid_sid_format(sid):
    if not sid.isdigit() or len(sid) != 5: return False
    if sid[0] != '1' or sid[1] not in ['0', '1']: return False 
    class_num = int(sid[2]) 
    if class_num not in [1, 2, 3, 4, 5]: return False
    student_num = int(sid[3:])
    return 1 <= student_num <= 35

@st.cache_data(ttl=60)
def load_course_data():
    try:
        url_11 = f"https://docs.google.com/spreadsheets/d/{ID_11}/export?format=csv"
        url_12 = f"https://docs.google.com/spreadsheets/d/{ID_12}/export?format=csv"
        
        # 💡 핵심 1: 11학년 시트는 2번째 줄(index 1)이 진짜 헤더입니다 (header=1 옵션)
        df_11 = pd.read_csv(url_11, header=1)
        # 💡 핵심 2: 12학년 시트는 1번째 줄이 헤더입니다.
        df_12 = pd.read_csv(url_12)
        
        # '과목명' 열 데이터만 추출
        l_11 = df_11['과목명'].dropna().astype(str).tolist()
        l_12 = df_12['과목명'].dropna().astype(str).tolist()
        
        # 12학년의 '계열(교과)' 정보를 딕셔너리로 저장 (우선순위 배정용)
        # 예: {'21세기 문학 탐구': '국어과', '수학 과제 탐구': '수학과'}
        course_to_dept = dict(zip(df_12['과목명'].astype(str), df_12['계열(교과)'].astype(str)))
        
        return l_11, l_12, course_to_dept
    except Exception as e:
        st.error(f"🚨 시트 데이터를 불러오지 못했습니다. (ID 오류 또는 권한 문제)\n에러 상세: {e}")
        return [], [], {}

list_11, list_12, course_to_dept_dict = load_course_data()

# 시트의 '국어과', '수학과' 등을 학생이 선택한 '희망계열'과 연결해주는 함수
def get_course_track(course_name, dept_dict):
    dept = dept_dict.get(course_name, "")
    if "국어" in dept or "영어" in dept or "사회" in dept or "역사" in dept: return '인문사회계열'
    if "수학" in dept or "과학" in dept or "정보" in dept: return '자연공학계열'
    if "체육" in dept or "음악" in dept or "미술" in dept or "예술" in dept: return '예체능계열'
    return '자유전공'

def get_csv_df(filename):
    if os.path.exists(filename): return pd.read_csv(filename)
    return None

def save_csv(df, filename):
    df.to_csv(filename, index=False, encoding='utf-8-sig')

# ==========================================
# 🔑 1부: 로그인 / 회원가입
# ==========================================
if st.session_state.login_email is None:
    if st.session_state.page == "login":
        st.title("🍏 KIS 수강신청 로그인")
        with st.container(border=True):
            email_input = st.text_input("학교 이메일 (@kshcm.net)")
            pw_input = st.text_input("비밀번호", type="password")
            if st.button("로그인", type="primary", use_container_width=True):
                if email_input == "admin@kshcm.net" and pw_input == "admin":
                    st.session_state.update({'login_email': email_input, 'user_name': '관리자', 'user_id': '99999', 'admin': True, 'page': 'input'}); st.rerun()
                
                users_df = get_csv_df('users.csv')
                if users_df is not None:
                    user = users_df[(users_df['이메일'] == email_input) & (users_df['비밀번호'] == str(pw_input))]
                    if not user.empty:
                        st.session_state.update({'login_email': user.iloc[0]['이메일'], 'user_name': user.iloc[0]['이름'], 'user_id': str(user.iloc[0]['학번']), 'page': 'input'}); st.rerun()
                    else: st.error("이메일 또는 비밀번호 오류")
                else: st.error("등록된 회원이 없습니다.")
            st.divider()
            if st.button("회원가입 하기", use_container_width=True): st.session_state.page = "signup"; st.rerun()

    elif st.session_state.page == "signup":
        st.title("📝 KIS 수강신청 회원가입")
        with st.container(border=True):
            new_email = st.text_input("학교 이메일", placeholder=f"ID@{SCHOOL_DOMAIN}")
            new_pw = st.text_input("비밀번호 생성", type="password")
            new_id = st.text_input("학번 (5자리)", placeholder="예: 10101 (10학년)")
            new_name = st.text_input("본인 이름")
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button("가입 완료하기", type="primary", use_container_width=True):
                    if not is_valid_sid_format(new_id): st.error("❌ 올바른 학번 형식이 아닙니다.")
                    else:
                        pd.DataFrame([{'이메일': new_email, '비밀번호': new_pw, '학번': new_id, '이름': new_name}]).to_csv('users.csv', mode='a', header=not os.path.exists('users.csv'), index=False, encoding='utf-8-sig')
                        st.success("🎉 회원가입 완료!"); st.session_state.page = "login"; st.rerun()
            with c2:
                if st.button("뒤로 가기"): st.session_state.page = "login"; st.rerun()
    st.stop()

# ==========================================
# 📱 2부: 사이드바 및 메인
# ==========================================
user_grade_prefix = st.session_state.user_id[:2]
current_grade = 10 if user_grade_prefix == '10' else (11 if user_grade_prefix == '11' else 99)
target_grade = 11 if current_grade == 10 else 12

req_courses_count = 7 if current_grade == 10 else 8

with st.sidebar:
    st.write(f"🧑‍🎓 **{st.session_state.user_name}**님 ({st.session_state.user_id})")
    st.divider()
    if st.button("📝 수강신청 / 보충신청"): st.session_state.page = "input"; st.rerun()
    if st.button("📊 결과조회"): st.session_state.page = "check"; st.rerun()
    if st.session_state.admin and st.button("⚙️ 관리자 대시보드"): st.session_state.page = "admin"; st.rerun()
    if st.button("로그아웃"): st.session_state.clear(); st.rerun()

# -------------------------------------------
# [페이지 1: 수강신청]
# -------------------------------------------
if st.session_state.page == "input":
    st.title("📝 KIS 수강신청")
    
    exist_df = get_csv_df('students_data.csv')
    has_applied = exist_df is not None and str(st.session_state.user_id) in exist_df['학번'].astype(str).values
    
    results_df = get_csv_df('final_results.csv')
    assigned_courses = []
    need_more = False
    
    if results_df is not None and str(st.session_state.user_id) in results_df['학번'].astype(str).values:
        my_res = results_df[results_df['학번'].astype(str) == str(st.session_state.user_id)].iloc[0]
        assigned_courses = str(my_res['확정과목']).split(',') if pd.notna(my_res['확정과목']) and my_res['확정과목'] != "" else []
        if len(assigned_courses) < req_courses_count:
            need_more = True

    if has_applied and not need_more:
        st.success("✅ 수강신청이 완료되어 심사 중이거나 최종 확정되었습니다.")
        st.info("결과조회 탭을 확인하세요.")
    else:
        max_sel = req_courses_count - len(assigned_courses) # 고를 수 있는 최대 개수
        
        if need_more:
            st.warning(f"🚨 1차 배정 결과 탈락/폐강된 과목이 있습니다. {max_sel}개의 선택과목을 추가로 골라주세요.")
        
        with st.form("apply_form"):
            clist = list_11 if current_grade == 10 else list_12
            if need_more: clist = [c for c in clist if c not in assigned_courses]
            
            if current_grade == 10:
                st.info("💡 **예비 11학년 안내:** 공통과목 3개는 자동 배정됩니다. 아래에서 **선택과목 7개**를 골라주세요. (100% 선착순)")
                my_track = "해당없음"
            else:
                st.info("💡 **예비 12학년 안내:** 공통과목 1개는 자동 배정됩니다. 본인의 희망 계열을 선택한 후 **선택과목 8개**를 골라주세요. (계열 우대)")
                st.subheader("1. 본인의 희망 계열 선택")
                my_track = st.selectbox("희망 계열 (배정 1순위 우대)", TRACKS)
            
            st.subheader(f"{'1' if current_grade==10 else '2'}. 선택과목 고르기 (반드시 {max_sel}개 선택)")
            
            # 💡 핵심 3: max_selections를 설정해 초과 선택을 시스템적으로 차단!
            selected_courses = st.multiselect(
                "과목 리스트", 
                clist, 
                max_selections=max_sel, 
                placeholder=f"최대 {max_sel}개까지 고를 수 있습니다."
            )
            
            if st.form_submit_button("🚀 제출하기", type="primary"):
                if len(selected_courses) != max_sel:
                    st.error(f"❌ 정확히 {max_sel}개의 과목을 골라주세요. (현재 {len(selected_courses)}개 선택)")
                else:
                    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    courses_str = ",".join(selected_courses)
                    
                    new_data = {'제출시간': ts, '학번': st.session_state.user_id, '이름': st.session_state.user_name, '학년': current_grade, '희망계열': my_track, '신청과목': courses_str}
                    
                    if not need_more:
                        pd.DataFrame([new_data]).to_csv('students_data.csv', mode='a', header=not os.path.exists('students_data.csv'), index=False, encoding='utf-8-sig')
                        st.success("1차 신청 완료!"); st.rerun()
                    else:
                        exist_df.loc[exist_df['학번'].astype(str) == str(st.session_state.user_id), '신청과목'] += "," + courses_str
                        save_csv(exist_df, 'students_data.csv')
                        st.success("2차 보충 신청 완료!"); st.rerun()

# -------------------------------------------
# [페이지 2: 결과 조회]
# -------------------------------------------
elif st.session_state.page == "check":
    st.title("📊 나의 수강 배정 결과")
    df = get_csv_df('final_results.csv')
    
    # 에러 방지: 학번 기준으로 필터링 (이메일 기준 삭제)
    if df is not None and str(st.session_state.user_id) in df['학번'].astype(str).values:
        my_data = df[df['학번'].astype(str) == str(st.session_state.user_id)].iloc[0]
        confirmed = str(my_data.get('확정과목', '')).split(',')
        rejected = str(my_data.get('탈락과목', '')).split(',')
        
        st.info(f"📌 공통과목 **{'3' if current_grade == 10 else '1'}개**는 학교 일괄 배정으로 별도 표기되지 않습니다.")
        
        st.subheader(f"✅ 확정된 선택과목 (현재 {len([c for c in confirmed if c])}개)")
        if confirmed and confirmed[0] != "":
            for c in confirmed: st.success(c)
        else: st.write("아직 확정된 과목이 없습니다.")
            
        st.subheader("❌ 초과 탈락된 과목 (2차 보충 신청 필요)")
        if rejected and rejected[0] != "" and rejected[0] != "nan":
            for r in rejected: st.error(r)
        else: st.write("탈락한 과목이 없습니다.")
    else:
        st.info("관리자가 배정 알고리즘을 가동하기 전입니다.")

# -------------------------------------------
# [페이지 3: 관리자 대시보드]
# -------------------------------------------
elif st.session_state.page == "admin" and st.session_state.admin:
    st.title("⚙️ 관리자 종합 배정 시스템")
    
    students = get_csv_df('students_data.csv')
    
    if students is not None:
        st.write(f"현재 총 신청 학생 수: {len(students)}명")
        st.divider()
        st.subheader("🚀 1, 2차 통합 배정 알고리즘 가동")
        st.write("- **10학년(예비11):** 100% 제출시간(선착순) 배정")
        st.write("- **11학년(예비12):** 1순위 계열 일치(스프레드시트 연동), 2순위 제출시간 배정")
        
        if st.button("알고리즘 가동하기", type="primary"):
            requests = []
            for _, row in students.iterrows():
                sid = str(row['학번'])
                student_grade = int(row['학년'])
                track = row['희망계열']
                time = row['제출시간']
                courses = str(row['신청과목']).split(',')
                for c in courses:
                    if c: requests.append({'학번': sid, '학년': student_grade, '과목': c.strip(), '학생계열': track, '시간': time})
            
            req_df = pd.DataFrame(requests)
            final_assignments = {str(row['학번']): {'확정': [], '탈락': []} for _, row in students.iterrows()}
            course_counts = {}
            
            for course in req_df['과목'].unique():
                c_df = req_df[req_df['과목'] == course].copy()
                target_grade_of_course = c_df['학년'].iloc[0] 
                
                if target_grade_of_course == 10:
                    # 10학년 신청 -> 100% 선착순
                    c_df = c_df.sort_values(by='시간', ascending=True)
                else:
                    # 11학년 신청 -> 스프레드시트의 '계열(교과)'를 읽어와 일치 여부 확인
                    course_track = get_course_track(course, course_to_dept_dict)
                    c_df['계열일치'] = c_df['학생계열'] == course_track
                    c_df = c_df.sort_values(by=['계열일치', '시간'], ascending=[False, True])
                
                accepted = c_df.head(MAX_CAPACITY)
                rejected = c_df.iloc[MAX_CAPACITY:]
                
                course_counts[course] = len(accepted)
                
                for sid in accepted['학번']: final_assignments[sid]['확정'].append(course)
                for sid in rejected['학번']: final_assignments[sid]['탈락'].append(course)
                
            res_list = []
            for sid, data in final_assignments.items():
                res_list.append({
                    '학번': sid,
                    '확정과목': ",".join(data['확정']),
                    '탈락과목': ",".join(data['탈락'])
                })
            save_csv(pd.DataFrame(res_list), 'final_results.csv')
            save_csv(pd.DataFrame(list(course_counts.items()), columns=['과목명', '배정인원']), 'course_status.csv')
            
            st.success("배정이 완료되었습니다! 학생들이 '결과조회'에서 결과를 확인할 수 있습니다.")
        
        st.divider()
        st.subheader("🗑️ 3차 최종: 인원 미달 과목 폐강 및 조정")
        
        status_df = get_csv_df('course_status.csv')
        if status_df is not None:
            st.dataframe(status_df.sort_values(by='배정인원', ascending=False))
            
            lowest_course = status_df.sort_values(by='배정인원').iloc[0]['과목명']
            lowest_count = status_df.sort_values(by='배정인원').iloc[0]['배정인원']
            
            if st.button(f"🚨 인원 최하위 '{lowest_course}' ({lowest_count}명) 폐강 처리하기"):
                res_df = get_csv_df('final_results.csv')
                for idx, row in res_df.iterrows():
                    confirmed = str(row['확정과목']).split(',')
                    if lowest_course in confirmed:
                        confirmed.remove(lowest_course)
                        res_df.at[idx, '확정과목'] = ",".join(confirmed)
                        
                        rejected = str(row['탈락과목']).split(',') if pd.notna(row['탈락과목']) else []
                        if lowest_course not in rejected: rejected.append(lowest_course)
                        res_df.at[idx, '탈락과목'] = ",".join([r for r in rejected if r])
                
                save_csv(res_df, 'final_results.csv')
                
                status_df = status_df[status_df['과목명'] != lowest_course]
                save_csv(status_df, 'course_status.csv')
                
                st.success(f"'{lowest_course}' 과목이 폐강되었습니다. 해당 과목 신청 학생들은 2차 보충 신청을 해야 합니다."); st.rerun()
