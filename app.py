import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ==========================================
# 🚨 기본 설정 (시트 ID 입력)
# ==========================================
# ==========================================
# 🚨 시트 ID 재확인 (여기가 틀리면 과목이 섞입니다)
# ==========================================
# 11학년(현재 10학년용) 과목 리스트 시트 ID
ID_11 = "1xADYmy5iJEIiaENxCH1ZiqGU2yiFS81MfSQDCMsnO04" 

# 12학년(현재 11학년용) 과목 리스트 시트 ID
ID_12 = "1Yp79f79ilwA2ErJ6DoxRPbU_ADCq0PnRGH2TxGvKSDg" 

# ------------------------------------------
# 학번 앞자리(10..., 11...)에 따라 과목을 나누는 로직 재점검
# ------------------------------------------
# ❌ 기존 코드 (문제가 된 부분)
# user_grade_prefix = st.session_state.user_id[:2]

# ✅ 수정할 코드 (안전장치 추가)
# 접속 정보가 없으면 학번 입력창을 띄워줍니다.
if 'user_id' not in st.session_state or not st.session_state.user_id:
    st.warning("⚠️ 접속 정보가 없습니다. 아래에 학번을 다시 입력해 주세요.")
    
    # 학번 입력 칸과 확인 버튼 만들기
    temp_id = st.text_input("학번 입력 (예: 1101):")
    if st.button("접속하기"):
        st.session_state.user_id = temp_id
        st.rerun() # 👈 입력 후 화면을 스스로 새로고침해서 셔터를 올립니다!
        
    st.stop() # 학번을 입력하고 버튼을 누르기 전까지는 여기서 멈춰 대기합니다.

# 💡 이 줄은 왼쪽 벽에 딱 붙어있어야 합니다.
user_grade_prefix = str(st.session_state.user_id)[:2] # 안전하게 문자로 바꾼 뒤 앞 2자리 자르기

if user_grade_prefix == '10':
    current_grade = 10
    clist = list_11  # 10학년(예비11)은 11학년 시트 데이터 사용
elif user_grade_prefix == '11':
    current_grade = 11
    clist = list_12  # 11학년(예비12)은 12학년 시트 데이터 사용
else:
    current_grade = 99
    clist = []

# 💡 수정됨: 11학년(예비12학년) 전용 희망 교과(계열) 리스트 (시트의 데이터와 1:1 매칭)
TRACKS = ['국어과', '영어과', '수학과', '사회과', '과학과', '베트남어과', '예술과', '정보과']

st.set_page_config(page_title="KIS 수강신청", layout="wide", page_icon="🍏")

# --- 세션 상태 초기화 ---
for key in ['login_email', 'user_name', 'user_id', 'admin']:
    if key not in st.session_state: st.session_state[key] = None if key != 'admin' else False
if 'page' not in st.session_state: st.session_state.page = "login"
if 'target_semester' not in st.session_state: st.session_state.target_semester = "1학기" # 학기 기본값

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
def load_full_data():
    try:
        url_11 = f"https://docs.google.com/spreadsheets/d/{ID_11}/export?format=csv"
        url_12 = f"https://docs.google.com/spreadsheets/d/{ID_12}/export?format=csv"
        
        def safe_load(url):
            # 1. float 에러 원천 차단: 모든 데이터를 처음부터 무조건 '글자(str)'로 불러옵니다.
            df = pd.read_csv(url, header=None, dtype=str) 
            
            # 2. '학기'와 '과목명'이 동시에 들어있는 진짜 제목줄을 샅샅이 뒤져서 찾습니다.
            header_idx = 0
            for i in range(len(df)):
                # 해당 줄의 데이터를 앞뒤 공백 없앤 리스트로 변환
                row_values = [str(val).strip() for val in df.iloc[i].values]
                if '학기' in row_values and '과목명' in row_values:
                    header_idx = i
                    break
            
            # 3. 찾은 줄을 공식 열 이름(Columns)으로 승격시킵니다.
            df.columns = [str(val).strip() for val in df.iloc[header_idx].values]
            
            # 4. 진짜 데이터(제목줄 아래 행들)만 남기고 정리합니다.
            df = df.iloc[header_idx + 1:].reset_index(drop=True)
            return df

        df_11 = safe_load(url_11)
        df_12 = safe_load(url_12)
        
        return df_11, df_12
    except Exception as e:
        st.error(f"🚨 시트 로드 중 오류: {e}")
        return None, None

def get_filtered_courses(semester):
    df_11, df_12 = load_full_data()
    if df_11 is None or df_12 is None: return [], [], {}
    
    try:
        sem_num = semester[0] # '1학기'면 '1'
        
        # 만약을 대비한 최종 방어 코드 (KeyError 방지)
        if '학기' not in df_11.columns or '학기' not in df_12.columns:
            st.error("🚨 '학기' 열을 찾지 못했습니다. 구글 시트 공유 권한이나 시트 내용을 다시 확인해주세요.")
            return [], [], {}

        # 빈칸(NaN)을 안전하게 처리하며 필터링
        f_11 = df_11[df_11['학기'].fillna('').astype(str).str.contains(sem_num)]
        f_12 = df_12[df_12['학기'].fillna('').astype(str).str.contains(sem_num)]
        
        l_11 = f_11['과목명'].dropna().astype(str).str.strip().unique().tolist()
        l_12 = f_12['과목명'].dropna().astype(str).str.strip().unique().tolist()
        
        course_to_dept = {}
        if '계열(교과)' in f_12.columns:
            course_to_dept = dict(zip(f_12['과목명'].fillna('').astype(str).str.strip(), 
                                      f_12['계열(교과)'].fillna('').astype(str).str.strip()))
        
        return l_11, l_12, course_to_dept
    except Exception as e:
        st.error(f"🚨 학기 필터링 중 오류 발생: {e}")
        return [], [], {}
# 현재 설정된 학기를 기준으로 과목 리스트 가져오기
list_11, list_12, course_to_dept_dict = get_filtered_courses(st.session_state.target_semester)

# 💡 수정됨: 시트의 '계열(교과)' 칸에 적힌 글자를 그대로 반환하여 매칭합니다.
def get_course_track(course_name, dept_dict):
    dept = dept_dict.get(course_name, "기타")
    return str(dept).strip()

def get_csv_df(filename):
    if os.path.exists(filename): return pd.read_csv(filename)
    return None

def save_csv(df, filename):
    df.to_csv(filename, index=False, encoding='utf-8-sig')

# ==========================================
# 🚨 긴급 데이터 초기화 메뉴 (사이드바 최상단)
# ==========================================
with st.sidebar:
    st.error("🛠️ 긴급 복구 / 초기화-오류발생시쓰시오")
    if st.button("꼬인 데이터(CSV) 강제 삭제", type="primary"):
        for f in ['students_data.csv', 'final_results.csv', 'course_status.csv']:
            if os.path.exists(f): os.remove(f)
        st.success("✅ 초기화 완료! 키보드 F5를 눌러 새로고침 하세요.")
    st.divider()

# ==========================================
# 🔑 1부: 로그인 / 회원가입
# ==========================================
if st.session_state.login_email is None:
    if st.session_state.page == "login":
        st.title(f"🍏 KIS {st.session_state.target_semester} 수강신청 로그인")
        with st.container(border=True):
            email_input = st.text_input("학교 이메일 (@kshcm.net)")
            pw_input = st.text_input("비밀번호", type="password")
            if st.button("로그인", type="primary", use_container_width=True):
                if email_input == "admin@kshcm.net" and pw_input == "admin":
                    st.session_state.update({'login_email': email_input, 'user_name': '관리자', 'user_id': '99999', 'admin': True, 'page': 'admin'}); st.rerun()
                
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
# 📱 2부: 메인 네비게이션
# ==========================================
user_grade_prefix = st.session_state.user_id[:2]
current_grade = 10 if user_grade_prefix == '10' else (11 if user_grade_prefix == '11' else 99)
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
    st.title(f"📝 {st.session_state.target_semester} 수강신청")
    
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
        max_sel = req_courses_count - len(assigned_courses)
        
        if need_more:
            st.warning(f"🚨 1차 배정 탈락/폐강 과목이 있습니다. {max_sel}개의 {st.session_state.target_semester} 선택과목을 추가로 골라주세요.")
        
        with st.form("apply_form"):
            clist = list_11 if current_grade == 10 else list_12
            if need_more: clist = [c for c in clist if c not in assigned_courses]
            
            if current_grade == 10:
                st.info("💡 **예비 11학년 안내:** 공통과목 3개는 자동 배정됩니다. 아래에서 **선택과목 7개**를 골라주세요. (100% 선착순)")
                my_track = "해당없음"
            else:
                st.info("💡 **예비 12학년 안내:** 공통과목 1개는 자동 배정됩니다. 본인의 희망 계열(교과)을 선택한 후 **선택과목 8개**를 골라주세요. (계열 우대)")
                st.subheader("1. 본인의 희망 계열(교과) 선택")
                my_track = st.selectbox("희망 계열(교과) (배정 1순위 우대)", TRACKS)
            
            st.subheader(f"{'1' if current_grade==10 else '2'}. {st.session_state.target_semester} 과목 고르기 (반드시 {max_sel}개 선택)")
            
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
                        st.success(f"{st.session_state.target_semester} 1차 신청 완료!"); st.rerun()
                    else:
                        exist_df.loc[exist_df['학번'].astype(str) == str(st.session_state.user_id), '신청과목'] += "," + courses_str
                        save_csv(exist_df, 'students_data.csv')
                        st.success(f"{st.session_state.target_semester} 2차 보충 신청 완료!"); st.rerun()

# -------------------------------------------
# [페이지 2: 결과 조회]
# -------------------------------------------
elif st.session_state.page == "check":
    st.title(f"📊 나의 {st.session_state.target_semester} 수강 배정 결과")
    df = get_csv_df('final_results.csv')
    
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
    
    with st.expander("📅 현재 수강신청 학기 설정", expanded=True):
        selected_sem = st.radio("배정 및 신청을 진행할 학기를 선택하세요", ["1학기", "2학기"], index=0 if st.session_state.target_semester == "1학기" else 1)
        if st.button("학기 설정 저장"):
            st.session_state.target_semester = selected_sem
            st.success(f"현재 시스템이 {selected_sem} 모드로 전환되었습니다. 학생들의 신청 화면이 변경됩니다.")
            st.rerun()

    st.info(f"현재 **{st.session_state.target_semester}**용 알고리즘이 가동 준비 중입니다.")
    
    students = get_csv_df('students_data.csv')
    if students is not None:
        st.write(f"현재 총 신청 학생 수: {len(students)}명")
        st.divider()
        st.subheader("🚀 1, 2차 통합 배정 알고리즘 가동")
        
        if st.button(f"{st.session_state.target_semester} 배정 알고리즘 가동하기", type="primary"):
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
                    c_df = c_df.sort_values(by='시간', ascending=True)
                else:
                    # 학생이 고른 '국어과' 등과 시트의 '계열(교과)'를 직접 비교
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
            
            st.success("배정이 완료되었습니다! 학생들이 '결과조회'에서 확인할 수 있습니다.")
        
        st.divider()
        st.subheader("🗑️ 3차 최종: 인원 미달 과목 폐강")
        status_df = get_csv_df('course_status.csv')
        if status_df is not None and not status_df.empty:
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
                
                st.success(f"'{lowest_course}' 과목이 폐강되었습니다."); st.rerun()
import streamlit as st
import pandas as pd
import random

st.markdown("---")
# 🚨 관리자만 열어볼 수 있도록 숨겨두는 탭(Expander)입니다.
with st.expander("🛠️ [관리자 전용] 170명 수강신청 부하/데이터 테스트"):
    st.warning("⚠️ 이 버튼을 누르면 170명의 가짜 수강신청 데이터가 즉시 생성됩니다.")
    
    if st.button("🚀 170명 가짜 데이터 생성 및 실험 시작!"):
        with st.spinner("170명의 데이터를 생성하는 중입니다..."):
            
            # 가짜 학생 170명 학번 만들기 (10학년 85명, 11학년 85명 가정)
            fake_students = []
            for i in range(1, 86):
                fake_students.append(f"10{i:02d}") # 1001 ~ 1085
                fake_students.append(f"11{i:02d}") # 1101 ~ 1185
                
            simulated_data = []
            
            # 170명 각각에 대해 랜덤으로 과목을 골라주는 작업
            for student_id in fake_students:
                # 학번에 따라 11학년 리스트(list_11) 또는 12학년 리스트(list_12) 선택
                # (이전에 선언해둔 list_11, list_12 변수를 그대로 사용합니다)
                target_list = list_11 if student_id.startswith("10") else list_12
                
                # 리스트가 비어있지 않은지 안전 확인
                if len(target_list) > 0:
                    # A~H 블록에 들어갈 과목을 리스트에서 랜덤으로 8개 뽑기 (중복 허용)
                    # 실제 환경과 비슷하게 만들기 위해 '미선택'도 들어갈 수 있게 설정
                    random_choices = [random.choice(target_list) for _ in range(8)]
                else:
                    random_choices = ["데이터 없음"] * 8
                    
                simulated_data.append({
                    "학번": student_id,
                    "A블록": random_choices[0],
                    "B블록": random_choices[1],
                    "C블록": random_choices[2],
                    "D블록": random_choices[3],
                    "E블록": random_choices[4],
                    "F블록": random_choices[5],
                    "G블록": random_choices[6],
                    "H블록": random_choices[7],
                })
                
            # 만든 데이터를 보기 좋은 표(데이터프레임)로 변환
            df_simulation = pd.DataFrame(simulated_data)
            
            st.success("✅ 170명 데이터 생성 완료!")
            
            # 1. 화면에 결과 살짝 보여주기
            st.write("📊 **생성된 데이터 미리보기 (앞부분 10개만)**")
            st.dataframe(df_simulation.head(10))
            
            # 2. 엑셀(CSV) 파일로 다운로드 할 수 있게 해주기 (가장 안전한 방법)
            # 구글 시트에 한 번에 170줄을 쏘면 에러가 날 수 있으므로, 엑셀로 먼저 뽑아보는 걸 추천합니다!
            csv = df_simulation.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 엑셀(CSV) 파일로 전체 다운로드 후 확인하기",
                data=csv,
                file_name='170명_수강신청_시뮬레이션.csv',
                mime='text/csv',
            )
