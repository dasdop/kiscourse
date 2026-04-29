import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ==========================================
# 🚨 기본 설정 (시트 ID 변경 필수)
# ==========================================
ID_11 = "11학년_시트_ID" 
ID_12 = "12학년_시트_ID" 
SCHOOL_DOMAIN = "kshcm.net"  
MAX_CAPACITY = 35  

st.set_page_config(page_title="KIS 수강신청", layout="wide", page_icon="🍏")

# --- 세션 상태 초기화 ---
if 'login_email' not in st.session_state: st.session_state.login_email = None
if 'user_name' not in st.session_state: st.session_state.user_name = None
if 'user_id' not in st.session_state: st.session_state.user_id = None
if 'page' not in st.session_state: st.session_state.page = "login"
if 'admin' not in st.session_state: st.session_state.admin = False

# ==========================================
# 🛠️ 헬퍼 함수 모음
# ==========================================
def mask_name(name):
    name = str(name)
    if len(name) <= 2: return name[0] + "O"
    else: return name[0] + "O" * (len(name) - 2) + name[-1]

# 💡 수정됨: 10학년(10XXX) / 11학년(11XXX) 판별 로직 적용
def is_valid_sid_format(sid):
    if not sid.isdigit() or len(sid) != 5: return False
    if sid[0] != '1': return False # 만의 자리 1 고정
    if sid[1] not in ['0', '1']: return False # 천의 자리 0(10학년) 또는 1(11학년)
    
    class_num = int(sid[2]) # 백의 자리 (반)
    if class_num not in [1, 2, 3, 4, 5]: return False
    
    student_num = int(sid[3:]) # 십, 일의 자리 (번호)
    if not (1 <= student_num <= 35): return False
    return True

# 💡 수정됨: 반(과목) 개수 전체 7개로 제한 [:7]
@st.cache_data(ttl=60)
def load_course_data():
    try:
        url_11 = f"https://docs.google.com/spreadsheets/d/{ID_11}/export?format=csv"
        url_12 = f"https://docs.google.com/spreadsheets/d/{ID_12}/export?format=csv"
        df_11 = pd.read_csv(url_11); df_12 = pd.read_csv(url_12)
        return df_11.iloc[:, 0].dropna().tolist()[:7], df_12.iloc[:, 0].dropna().tolist()[:7]
    except: return ["11_과목A", "11_과목B", "11_과목C"], ["12_과목X", "12_과목Y", "12_과목Z"]

list_11, list_12 = load_course_data()

def get_csv_df(filename):
    if os.path.exists(filename): return pd.read_csv(filename)
    return None

def send_trade_request(sender_id, sender_name, target_id, target_course, my_course):
    req_df = pd.DataFrame([{
        '시간': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        '보낸사람ID': sender_id, '보낸사람이름': sender_name,
        '받는사람ID': target_id, '상대과목': target_course, '내과목': my_course, '상태': '대기중'
    }])
    req_df.to_csv('trade_requests.csv', mode='a', header=not os.path.exists('trade_requests.csv'), index=False, encoding='utf-8-sig')

# ==========================================
# 🔑 1부: 회원가입 및 로그인 시스템
# ==========================================
if st.session_state.login_email is None:
    if st.session_state.page == "login":
        st.title("🍏 KIS 수강신청 로그인")
        with st.container(border=True):
            st.subheader("로그인")
            email_input = st.text_input("학교 이메일 (@kshcm.net)")
            pw_input = st.text_input("비밀번호", type="password")
            
            if st.button("로그인", type="primary", use_container_width=True):
                if email_input == "admin@kshcm.net" and pw_input == "admin":
                    st.session_state.login_email = "admin@kshcm.net"
                    st.session_state.user_name = "테스트관리자"
                    st.session_state.user_id = "99999"  
                    st.session_state.admin = True
                    st.session_state.page = "input"
                    st.rerun()
                
                users_df = get_csv_df('users.csv')
                if users_df is not None:
                    user = users_df[(users_df['이메일'] == email_input) & (users_df['비밀번호'] == str(pw_input))]
                    if not user.empty:
                        st.session_state.login_email = user.iloc[0]['이메일']
                        st.session_state.user_name = user.iloc[0]['이름']
                        st.session_state.user_id = str(user.iloc[0]['학번'])
                        st.session_state.page = "input"
                        st.rerun()
                    else: st.error("이메일 또는 비밀번호가 틀렸습니다.")
                else: st.error("등록된 회원이 없습니다. 회원가입을 먼저 진행해주세요.")
            
            st.divider()
            if st.button("회원가입 하기", use_container_width=True):
                st.session_state.page = "signup"; st.rerun()

    elif st.session_state.page == "signup":
        st.title("📝 KIS 수강신청 회원가입")
        with st.container(border=True):
            st.info("💡 10학년은 **10XXX**, 11학년은 **11XXX** 형식의 학번을 입력해야 합니다.")
            new_email = st.text_input("학교 이메일", placeholder=f"ID@{SCHOOL_DOMAIN}")
            new_pw = st.text_input("비밀번호 생성", type="password")
            new_pw2 = st.text_input("비밀번호 확인", type="password")
            new_id = st.text_input("학번 (5자리)", placeholder="예: 10101 (10학년), 11215 (11학년)")
            new_name = st.text_input("본인 이름 (실명)")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("가입 완료하기", type="primary", use_container_width=True):
                    if not new_email.endswith(f"@{SCHOOL_DOMAIN}"): st.error(f"❌ 이메일은 반드시 @{SCHOOL_DOMAIN} 형식이어야 합니다.")
                    elif new_pw != new_pw2: st.error("❌ 비밀번호가 서로 일치하지 않습니다.")
                    elif len(new_pw) < 4: st.error("❌ 비밀번호는 4자리 이상이어야 합니다.")
                    elif not is_valid_sid_format(new_id): st.error("❌ 올바른 학번 형식이 아닙니다.")
                    elif not new_name: st.error("❌ 이름을 입력해주세요.")
                    else:
                        users_df = get_csv_df('users.csv')
                        if users_df is not None and new_email in users_df['이메일'].values: st.error("🚨 이미 가입된 이메일입니다.")
                        elif users_df is not None and str(new_id) in users_df['학번'].astype(str).values: st.error("🚨 이미 가입된 학번입니다.")
                        else:
                            pd.DataFrame([{'이메일': new_email, '비밀번호': new_pw, '학번': new_id, '이름': new_name}]).to_csv('users.csv', mode='a', header=not os.path.exists('users.csv'), index=False, encoding='utf-8-sig')
                            st.success("🎉 회원가입 완료! 로그인 해주세요.")
                            st.session_state.page = "login"
                            st.rerun()
            with col2:
                if st.button("뒤로 가기", use_container_width=True):
                    st.session_state.page = "login"; st.rerun()
    st.stop()

# ==========================================
# 📱 2부: 로그인 성공 후 메인 화면
# ==========================================
with st.sidebar:
    # 10학년인지 11학년인지 학번 앞 2자리로 판단
    user_grade_prefix = st.session_state.user_id[:2]
    current_grade = 10 if user_grade_prefix == '10' else (11 if user_grade_prefix == '11' else 99)
    target_grade = 11 if current_grade == 10 else 12
    
    st.write(f"🧑‍🎓 **{st.session_state.user_name}**님 ({st.session_state.user_id})")
    if current_grade != 99:
        st.write(f"🎓 현재 **{current_grade}학년**")
    st.divider()
    if st.button("📝 1. 수강신청 하기"): st.session_state.page = "input"; st.rerun()
    if st.button("📊 2. 결과조회 및 교환"): st.session_state.page = "check"; st.rerun()
    if st.button("🔔 3. 알림함 (교환요청)"): st.session_state.page = "inbox"; st.rerun()
    st.divider()
    
    if not st.session_state.admin:
        pw = st.text_input("Admin PW", type="password")
        if st.button("Admin 모드"):
            if pw == "kis2026": st.session_state.admin = True; st.rerun()
    else:
        if st.button("Admin 모드 끄기"): st.session_state.admin = False; st.rerun()
        
    if st.button("로그아웃"):
        st.session_state.clear(); st.rerun()

# -------------------------------------------
# [페이지 1: 수강신청] - 학년 자동 매칭
# -------------------------------------------
if st.session_state.page == "input":
    st.title("📝 KIS 수강신청")
    
    exist_df = get_csv_df('students_data.csv')
    has_applied = exist_df is not None and str(st.session_state.user_id) in exist_df['학번'].astype(str).values

    if has_applied:
        st.success("✅ 이미 수강신청이 완료되었습니다.")
        st.info("배정 결과는 사이드바의 '2. 결과조회 및 교환' 탭에서 확인하실 수 있습니다.")
    else:
        with st.form("apply_form"):
            st.info(f"✅ 회원 정보 자동 연동됨. 현재 **{current_grade}학년**이므로 **{target_grade}학년 과목**을 신청합니다.")
            
            # 학년에 맞게 과목 리스트 7개 자동 할당
            clist = list_11 if current_grade == 10 else list_12
            
            st.divider()
            sel1 = st.selectbox("1지망", clist)
            sel2 = st.selectbox("2지망", clist)
            sel3 = st.selectbox("3지망", clist)
            
            if st.form_submit_button("🚀 수강신청 제출하기", type="primary"):
                ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                new_row = pd.DataFrame([{
                    '제출시간': ts, '이메일': st.session_state.login_email, 
                    '학번': st.session_state.user_id, '이름': st.session_state.user_name, 
                    '신청대상학년': target_grade, '1지망': sel1, '2지망': sel2, '3지망': sel3
                }])
                new_row.to_csv('students_data.csv', mode='a', header=not os.path.exists('students_data.csv'), index=False, encoding='utf-8-sig')
                st.success("수강신청이 성공적으로 접수되었습니다!"); st.rerun()

# -------------------------------------------
# [페이지 2: 결과 조회 및 트레이드] - 학년 격리
# -------------------------------------------
elif st.session_state.page == "check":
    st.title("📊 수강 배정 결과 및 마켓")
    df = get_csv_df('final_results.csv')
    
    if df is not None:
        my_id = st.session_state.user_id
        my_data = df[df['학번'].astype(str) == str(my_id)]
        
        if not my_data.empty:
            my_course = my_data.iloc[0]['배정과목']
            st.success(f"✅ 현재 배정된 과목: **[{my_course}]**")
            st.divider()
            st.subheader(f"🤝 수강 교환 마켓 ({current_grade}학년 전용)")
            
            search = st.text_input("찾고 싶은 과목명 검색")
            # 💡 수정됨: 나랑 학번 앞 두 자리(학년)가 같은 학생들만 필터링
            my_grade_prefix = str(my_id)[:2]
            grade_df = df[df['학번'].astype(str).str.startswith(my_grade_prefix)]
            
            display_df = grade_df[grade_df['배정과목'].str.contains(search)] if search else grade_df
            
            for idx, row in display_df.iterrows():
                if str(row['학번']) == str(my_id): continue 
                if str(row['학번']) == '99999': continue 
                
                c1, c2, c3, c4 = st.columns([1, 1, 2, 1])
                with c1: st.write(f"학번: {row['학번']}")
                with c2: st.write(f"이름: {mask_name(row['이름'])}")
                with c3: st.write(f"배정과목: {row['배정과목']}")
                with c4:
                    if st.button("교환 요청", key=f"req_{row['학번']}"):
                        send_trade_request(my_id, st.session_state.user_name, row['학번'], row['배정과목'], my_course)
                        st.toast("요청이 전송되었습니다!")
        else: st.warning("아직 수강신청을 안 하셨거나, 관리자가 배정 전입니다.")
    else: st.info("관리자가 배정을 실행하지 않았습니다.")

# -------------------------------------------
# [페이지 3: 알림함]
# -------------------------------------------
elif st.session_state.page == "inbox":
    st.title("🔔 나의 알림함")
    df = get_csv_df('final_results.csv')
    reqs = get_csv_df('trade_requests.csv')
    
    if reqs is not None and df is not None:
        my_id = st.session_state.user_id
        my_reqs = reqs[(reqs['받는사람ID'].astype(str) == str(my_id)) & (reqs['상태'] == '대기중')]
        
        if not my_reqs.empty:
            for idx, row in my_reqs.iterrows():
                with st.expander(f"📩 {mask_name(row['보낸사람이름'])} 학생의 요청"):
                    st.write(f"- 상대방이 내놓은 과목: **{row['내과목']}**")
                    st.write(f"- 나와 바꾸길 원하는 과목: **{row['상대과목']}**")
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("✅ 수락하기", key=f"acc_{idx}"):
                            df.loc[df['학번'].astype(str) == str(row['보낸사람ID']), '배정과목'] = row['상대과목']
                            df.loc[df['학번'].astype(str) == str(row['받는사람ID']), '배정과목'] = row['내과목']
                            df.to_csv('final_results.csv', index=False, encoding='utf-8-sig')
                            reqs.at[idx, '상태'] = '승인됨'
                            reqs.to_csv('trade_requests.csv', index=False, encoding='utf-8-sig')
                            st.success("교환 성공!"); st.rerun()
                    with c2:
                        if st.button("❌ 거절하기", key=f"rej_{idx}"):
                            reqs.at[idx, '상태'] = '거절됨'
                            reqs.to_csv('trade_requests.csv', index=False, encoding='utf-8-sig')
                            st.rerun()
        else: st.write("새로운 교환 요청이 없습니다.")
    else: st.write("시스템에 등록된 요청 내역이 없습니다.")

# ==========================================
# ⚙️ 3부: 관리자 종합 대시보드 - 학년별 분리
# ==========================================
if st.session_state.admin:
    st.divider()
    st.title("⚙️ 관리자 종합 대시보드")
    
    users = get_csv_df('users.csv')
    students = get_csv_df('students_data.csv')
    results = get_csv_df('final_results.csv')
    
    if users is not None:
        users = users[users['학번'].astype(str) != '99999']
        
        dashboard_data = []
        for _, u in users.iterrows():
            sid = str(u['학번'])
            row_data = {
                '학번': int(sid) if sid.isdigit() else sid,  
                '이름': u['이름'], '이메일': u['이메일'], '비밀번호': u['비밀번호'],
                '신청여부': '❌ 미신청', '1지망': '-', '2지망': '-', '3지망': '-', '배정과목': '-'
            }
            if students is not None and sid in students['학번'].astype(str).values:
                s_row = students[students['학번'].astype(str) == sid].iloc[0]
                row_data['신청여부'] = '✅ 신청완료'
                row_data['1지망'] = s_row.get('1지망', '-')
                row_data['2지망'] = s_row.get('2지망', '-')
                row_data['3지망'] = s_row.get('3지망', '-')
                
            if results is not None and sid in results['학번'].astype(str).values:
                r_row = results[results['학번'].astype(str) == sid].iloc[0]
                row_data['배정과목'] = r_row.get('배정과목', '-')
                
            dashboard_data.append(row_data)
        
        dash_df = pd.DataFrame(dashboard_data)
        if not dash_df.empty:
            dash_df = dash_df.sort_values(by='학번', ascending=True).reset_index(drop=True)
            
            # 💡 수정됨: 10학년과 11학년 분리 출력
            dash_10 = dash_df[dash_df['학번'].astype(str).str.startswith('10')]
            dash_11 = dash_df[dash_df['학번'].astype(str).str.startswith('11')]
            
            col_a, col_b = st.columns(2)
            with col_a:
                st.subheader("🟢 10학년 (11학년 과목 신청)")
                st.dataframe(dash_10, use_container_width=True)
            with col_b:
                st.subheader("🔵 11학년 (12학년 과목 신청)")
                st.dataframe(dash_11, use_container_width=True)
        else:
            st.info("가입된 일반 학생이 없습니다.")
            
        st.divider()
        st.write("### ⚡ 수강 배정 실행 (전체 일괄)")
        if students is not None:
            if st.button("🚀 선착순 지망 배정 실행", type="primary"):
                s_data = students.copy()
                s_data['제출시간'] = pd.to_datetime(s_data['제출시간'])
                s_data = s_data.sort_values('제출시간')
                
                # 전체 수용 인원 설정
                capacities = {c: MAX_CAPACITY for c in list_11 + list_12}
                assignments = {}
                
                for p in ['1지망', '2지망', '3지망']:
                    for _, student in s_data.iterrows():
                        sid = str(student['학번'])
                        if sid in assignments: continue
                        choice = student[p]
                        if choice in capacities and capacities[choice] > 0:
                            capacities[choice] -= 1
                            assignments[sid] = choice
                
                results_list = []
                for _, student in s_data.iterrows():
                    sid = str(student['학번'])
                    results_list.append({**student.to_dict(), '배정과목': assignments.get(sid, "미배정")})
                pd.DataFrame(results_list).to_csv('final_results.csv', index=False, encoding='utf-8-sig')
                st.success("배정이 완료되었습니다. 새로고침 시 상단 표에 결과가 반영됩니다.")
