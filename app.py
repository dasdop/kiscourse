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
MIN_CAPACITY = 20  

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

def is_valid_sid_format(sid):
    if not sid.isdigit() or len(sid) != 5: return False
    st_list = [int(d) for d in sid]
    if st_list[0] != 1: return False
    if st_list[1] not in [1, 2]: return False 
    if st_list[2] not in [1,2,3,4,5]: return False
    last_two = int(sid[3:])
    if st_list[3] < 3: return last_two > 0
    elif st_list[3] == 3: return st_list[4] <= 5
    return False

@st.cache_data(ttl=60)
def load_course_data():
    try:
        url_11 = f"https://docs.google.com/spreadsheets/d/{ID_11}/export?format=csv"
        url_12 = f"https://docs.google.com/spreadsheets/d/{ID_12}/export?format=csv"
        df_11 = pd.read_csv(url_11); df_12 = pd.read_csv(url_12)
        return df_11.iloc[:, 0].dropna().tolist(), df_12.iloc[:, 0].dropna().tolist()
    except: return ["과목A", "과목B", "과목C"], ["과목X", "과목Y", "과목Z"]

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
                # 🛑 하드코딩된 관리자 테스트 계정 (대시보드 미노출)
                if email_input == "admin@kshcm.net" and pw_input == "admin":
                    st.session_state.login_email = "admin@kshcm.net"
                    st.session_state.user_name = "테스트관리자"
                    st.session_state.user_id = "99999"  
                    st.session_state.admin = True
                    st.session_state.page = "input"
                    st.rerun()
                
                # 일반 회원 로그인
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
                st.session_state.page = "signup"
                st.rerun()

    elif st.session_state.page == "signup":
        st.title("📝 KIS 수강신청 회원가입")
        with st.container(border=True):
            new_email = st.text_input("학교 이메일", placeholder=f"ID@{SCHOOL_DOMAIN}")
            new_pw = st.text_input("비밀번호 생성", type="password")
            new_pw2 = st.text_input("비밀번호 확인", type="password")
            new_id = st.text_input("학번 (5자리)", placeholder="예: 11101")
            new_name = st.text_input("본인 이름 (실명)")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("가입 완료하기", type="primary", use_container_width=True):
                    if not new_email.endswith(f"@{SCHOOL_DOMAIN}"):
                        st.error(f"❌ 이메일은 반드시 @{SCHOOL_DOMAIN} 형식이어야 합니다.")
                    elif new_pw != new_pw2: st.error("❌ 비밀번호가 서로 일치하지 않습니다.")
                    elif len(new_pw) < 4: st.error("❌ 비밀번호는 4자리 이상이어야 합니다.")
                    elif not is_valid_sid_format(new_id): st.error("❌ 올바른 학번 형식이 아닙니다.")
                    elif not new_name: st.error("❌ 이름을 입력해주세요.")
                    else:
                        users_df = get_csv_df('users.csv')
                        if users_df is not None and new_email in users_df['이메일'].values:
                            st.error("🚨 이미 가입된 이메일입니다.")
                        elif users_df is not None and str(new_id) in users_df['학번'].astype(str).values:
                            st.error("🚨 이미 가입된 학번입니다.")
                        else:
                            pd.DataFrame([{'이메일': new_email, '비밀번호': new_pw, '학번': new_id, '이름': new_name}]).to_csv('users.csv', mode='a', header=not os.path.exists('users.csv'), index=False, encoding='utf-8-sig')
                            st.success("🎉 회원가입 완료! 로그인 해주세요.")
                            st.session_state.page = "login"
                            st.rerun()
            with col2:
                if st.button("뒤로 가기", use_container_width=True):
                    st.session_state.page = "login"
                    st.rerun()
    st.stop()

# ==========================================
# 📱 2부: 로그인 성공 후 메인 화면
# ==========================================
with st.sidebar:
    st.write(f"🧑‍🎓 **{st.session_state.user_name}**님 ({st.session_state.user_id})")
    st.write(f"📧 {st.session_state.login_email}")
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
# [페이지 1: 수강신청]
# -------------------------------------------
if st.session_state.page == "input":
    st.title("📝 KIS 수강신청")
    
    # 🛑 수강신청 중복 여부 확인
    exist_df = get_csv_df('students_data.csv')
    has_applied = False
    if exist_df is not None and str(st.session_state.user_id) in exist_df['학번'].astype(str).values:
        has_applied = True

    if has_applied:
        st.success("✅ 이미 수강신청이 완료되었습니다.")
        st.info("배정 결과는 사이드바의 '2. 결과조회 및 교환' 탭에서 확인하실 수 있습니다.")
    else:
        with st.form("apply_form"):
            st.info("✅ 회원 정보가 연동되었습니다. 수강할 학년과 지망 과목만 선택해주세요.")
            default_grade = 11 if st.session_state.user_id[1] == '1' else 12
            grade = st.radio("수강 학년", [11, 12], index=0 if default_grade == 11 else 1)
            
            st.divider()
            clist = list_11 if grade == 11 else list_12
            sel1 = st.selectbox("1지망", clist)
            sel2 = st.selectbox("2지망", clist)
            sel3 = st.selectbox("3지망", clist)
            
            if st.form_submit_button("🚀 수강신청 제출하기", type="primary"):
                ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                new_row = pd.DataFrame([{
                    '제출시간': ts, '이메일': st.session_state.login_email, 
                    '학번': st.session_state.user_id, '이름': st.session_state.user_name, 
                    '학년': grade, '1지망': sel1, '2지망': sel2, '3지망': sel3
                }])
                new_row.to_csv('students_data.csv', mode='a', header=not os.path.exists('students_data.csv'), index=False, encoding='utf-8-sig')
                st.success("수강신청이 성공적으로 접수되었습니다!"); st.rerun()

# -------------------------------------------
# [페이지 2: 결과 조회 및 트레이드]
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
            st.subheader("🤝 수강 교환 마켓 (트레이드)")
            
            search = st.text_input("찾고 싶은 과목명 검색")
            display_df = df[df['배정과목'].str.contains(search)] if search else df
            
            for idx, row in display_df.iterrows():
                if str(row['학번']) == str(my_id): continue 
                if str(row['학번']) == '99999': continue # 가계정 표시 제외
                
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
# ⚙️ 3부: 관리자 종합 대시보드
# ==========================================
if st.session_state.admin:
    st.divider()
    st.title("⚙️ 관리자 종합 대시보드")
    
    users = get_csv_df('users.csv')
    students = get_csv_df('students_data.csv')
    results = get_csv_df('final_results.csv')
    
    if users is not None:
        # 가계정(99999) 데이터 필터링하여 대시보드에서 숨김
        users = users[users['학번'].astype(str) != '99999']
        
        st.write("### 📋 전체 학생 등록 및 신청 현황")
        
        # 통합 데이터 생성
        dashboard_data = []
        for _, u in users.iterrows():
            sid = str(u['학번'])
            row_data = {
                '학번': int(sid) if sid.isdigit() else sid,  # 정렬을 위해 정수형 변환
                '이름': u['이름'],
                '이메일': u['이메일'],
                '비밀번호': u['비밀번호'],
                '신청여부': '❌ 미신청',
                '1지망': '-', '2지망': '-', '3지망': '-',
                '배정과목': '-'
            }
            
            # 수강신청 데이터 병합
            if students is not None and sid in students['학번'].astype(str).values:
                s_row = students[students['학번'].astype(str) == sid].iloc[0]
                row_data['신청여부'] = '✅ 신청완료'
                row_data['1지망'] = s_row.get('1지망', '-')
                row_data['2지망'] = s_row.get('2지망', '-')
                row_data['3지망'] = s_row.get('3지망', '-')
                
            # 최종 배정 데이터 병합
            if results is not None and sid in results['학번'].astype(str).values:
                r_row = results[results['학번'].astype(str) == sid].iloc[0]
                row_data['배정과목'] = r_row.get('배정과목', '-')
                
            dashboard_data.append(row_data)
        
        # 데이터프레임 변환 및 학번 기준 오름차순 정렬
        dash_df = pd.DataFrame(dashboard_data)
        if not dash_df.empty:
            dash_df = dash_df.sort_values(by='학번', ascending=True).reset_index(drop=True)
            st.dataframe(dash_df, use_container_width=True)
        else:
            st.info("가입된 일반 학생이 없습니다.")
            
        st.divider()
        st.write("### ⚡ 수강 배정 실행")
        if students is not None:
            if st.button("🚀 선착순 지망 배정 일괄 실행", type="primary"):
                s_data = students.copy()
                s_data['제출시간'] = pd.to_datetime(s_data['제출시간'])
                s_data = s_data.sort_values('제출시간')
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
