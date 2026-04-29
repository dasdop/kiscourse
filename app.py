import os

# [추가할 코드] 에러 방지를 위해 기존 파일 강제 삭제 (한 번 실행 후 지워도 됨)
#if os.path.exists('final_results.csv'): os.remove('final_results.csv')
#if os.path.exists('students_data.csv'): os.remove('students_data.csv')
#if os.path.exists('trade_requests.csv'): os.remove('trade_requests.csv')
import streamlit as st
import pandas as pd
import os
from datetime import datetime

# ==========================================
# 🚨 설정 및 ID (본인의 시트 ID로 교체)
# ==========================================
ID_11 = "1Nfzop5JjziphJON7BGofEMJDM8TV31uY" 
ID_12 = "1NwYlD2X396Ux4NkRT_Dru3zsuolYeJrz" 
SCHOOL_DOMAIN = "kshcm.net"  # HCM 학교 도메인
MAX_CAPACITY = 35  
MIN_CAPACITY = 20  

st.set_page_config(page_title="KIS 수강신청 시스템", layout="wide", page_icon="🍏")

# --- 세션 상태 초기화 ---
if 'login_email' not in st.session_state: st.session_state.login_email = None
if 'page' not in st.session_state: st.session_state.page = "input"
if 'admin' not in st.session_state: st.session_state.admin = False

# 이름 마스킹 함수 (예: 홍길동 -> 홍O동)
def mask_name(name):
    name = str(name)
    if len(name) <= 2: return name[0] + "O"
    else: return name[0] + "O" * (len(name) - 2) + name[-1]

# 데이터 로드
@st.cache_data(ttl=60)
def load_course_data():
    try:
        url_11 = f"https://docs.google.com/spreadsheets/d/{ID_11}/export?format=csv"
        url_12 = f"https://docs.google.com/spreadsheets/d/{ID_12}/export?format=csv"
        df_11 = pd.read_csv(url_11); df_12 = pd.read_csv(url_12)
        return df_11.iloc[:, 0].dropna().tolist(), df_12.iloc[:, 0].dropna().tolist()
    except: return ["과목A", "과목B"], ["과목X", "과목Y"]

list_11, list_12 = load_course_data()

# ==========================================
# 🔑 1단계: 학교 계정 로그인 화면
# ==========================================
if st.session_state.login_email is None:
    st.title("🍏 KIS 수강신청 로그인")
    with st.container(border=True):
        st.subheader("학교 계정으로 로그인하세요")
        st.caption(f"이 시스템은 @{SCHOOL_DOMAIN} 계정 전용입니다.")
        email_input = st.text_input("이메일 주소 입력", placeholder=f"yourname@{SCHOOL_DOMAIN}")
        
        if st.button("로그인", type="primary"):
            if email_input.endswith(f"@{SCHOOL_DOMAIN}"):
                st.session_state.login_email = email_input
                st.success("로그인 성공!")
                st.rerun()
            else:
                st.error(f"❌ 학교 공식 이메일(@{SCHOOL_DOMAIN})만 사용 가능합니다.")
    st.stop()

# ==========================================
# ⚙️ 데이터베이스 처리 (배정 및 로그)
# ==========================================
# 배정 결과 파일 로드 함수
def get_final_df():
    if os.path.exists('final_results.csv'):
        return pd.read_csv('final_results.csv')
    return None

# 교환 요청(알림) 저장 함수
def send_trade_request(sender_id, sender_name, target_id, target_course, my_course):
    req_df = pd.DataFrame([{
        '시간': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        '보낸사람ID': sender_id,
        '보낸사람이름': sender_name,
        '받는사람ID': target_id,
        '상대과목': target_course,
        '내과목': my_course,
        '상태': '대기중'
    }])
    req_df.to_csv('trade_requests.csv', mode='a', header=not os.path.exists('trade_requests.csv'), index=False, encoding='utf-8-sig')

# ==========================================
# 📱 메인 화면 로직
# ==========================================

# 사이드바: 내 정보 및 알림함 가기
with st.sidebar:
    st.write(f"📧 **{st.session_state.login_email}**")
    if st.button("🏠 수강신청/결과조회"): st.session_state.page = "check"; st.rerun()
    if st.button("🔔 알림함 (교환요청)"): st.session_state.page = "inbox"; st.rerun()
    if st.button("로그아웃"): st.session_state.login_email = None; st.rerun()

# [페이지: 알림함]
if st.session_state.page == "inbox":
    st.title("🔔 나의 알림함")
    st.info("다른 학생으로부터 온 과목 교환 요청을 확인하고 승인할 수 있습니다.")
    
    if os.path.exists('trade_requests.csv') and os.path.exists('final_results.csv'):
        df = pd.read_csv('final_results.csv')
        reqs = pd.read_csv('trade_requests.csv')
        my_id = df[df['이메일'] == st.session_state.login_email]['학번'].values[0]
        
        my_reqs = reqs[(reqs['받는사람ID'].astype(str) == str(my_id)) & (reqs['상태'] == '대기중')]
        
        if not my_reqs.empty:
            for idx, row in my_reqs.iterrows():
                with st.expander(f"📩 {mask_name(row['보낸사람이름'])} 학생의 교환 요청"):
                    st.write(f"**상대방의 과목:** {row['내과목']}")
                    st.write(f"**나의 과목:** {row['상대과목']} (교환 대상)")
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        if st.button("✅ 승인", key=f"acc_{idx}"):
                            # 실제 데이터 교체 로직
                            df.loc[df['학번'].astype(str) == str(row['보낸사람ID']), '배정과목'] = row['상대과목']
                            df.loc[df['학번'].astype(str) == str(row['받는사람ID']), '배정과목'] = row['내과목']
                            df.to_csv('final_results.csv', index=False, encoding='utf-8-sig')
                            # 요청 상태 변경
                            reqs.at[idx, '상태'] = '승인됨'
                            reqs.to_csv('trade_requests.csv', index=False, encoding='utf-8-sig')
                            st.success("교환이 완료되었습니다!"); st.rerun()
                    with c2:
                        if st.button("❌ 거절", key=f"rej_{idx}"):
                            reqs.at[idx, '상태'] = '거절됨'
                            reqs.to_csv('trade_requests.csv', index=False, encoding='utf-8-sig')
                            st.rerun()
        else: st.write("도착한 새 알림이 없습니다.")
    else: st.write("교환 요청 기록이 없습니다.")

# [페이지: 결과 조회 및 트레이드 리스트]
elif st.session_state.page in ["check", "input"]:
    st.title("📊 수강신청 현황 및 결과")
    
    df = get_final_df()
    if df is not None:
        my_data = df[df['이메일'] == st.session_state.login_email]
        if not my_data.empty:
            my_id = my_data.iloc[0]['학번']; my_name = my_data.iloc[0]['이름']; my_course = my_data.iloc[0]['배정과목']
            st.success(f"✅ **{my_name}**님은 현재 **[{my_course}]** 과목에 배정되어 있습니다.")
            
            st.divider()
            st.subheader("🤝 트레이드 리스트 (교환 신청)")
            
            # 검색 기능
            search = st.text_input("과목명으로 검색", placeholder="과목명을 입력하세요")
            display_df = df[df['배정과목'].str.contains(search)] if search else df
            
            # 리스트 출력
            for idx, row in display_df.iterrows():
                if str(row['학번']) == str(my_id): continue # 본인 제외
                
                c1, c2, c3, c4 = st.columns([1, 1, 2, 1])
                with c1: st.write(f"학번: {row['학번']}")
                with c2: st.write(f"이름: {mask_name(row['이름'])}")
                with c3: st.write(f"배정과목: {row['배정과목']}")
                with c4:
                    if st.button("교환 요청", key=f"req_{row['학번']}"):
                        send_trade_request(my_id, my_name, row['학번'], row['배정과목'], my_course)
                        st.toast(f"{mask_name(row['이름'])} 학생에게 교환 요청을 보냈습니다!")
        else:
            st.warning("아직 배정된 데이터가 없습니다. (수강신청 기간이 아닙니다)")
    else:
        st.info("관리자가 배정 알고리즘을 가동하기 전입니다.")
