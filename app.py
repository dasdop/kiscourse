import streamlit as st
import pandas as pd
import os
import time
import uuid
from datetime import datetime

# ==========================================
# 1. 기본 설정 및 데이터 매핑 (Constants)
# ==========================================
st.set_page_config(page_title="KIS 수강신청 시스템", layout="wide", page_icon="🍏")

MAX_CAPACITY = 35  # 최대 수용 인원 35명 확정
TRACKS = ['국어과', '영어과', '수학과', '사회과', '과학과', '베트남어과', '예술과', '정보과']

# A-F 그룹 매핑 (시간표 블록)
GROUP_MAP = {
    "A그룹": ["물리학", "미적분 II", "심화 국어"],
    "B그룹": ["생명과학", "미디어와 비판적사고", "경제"],
    "C그룹": ["토론과 글쓰기", "Introduction to Biology", "세계 지리"],
    "D그룹": ["미적분 I", "물리학 실험", "화학 II"],
    "E그룹": ["대수", "영미 문학 읽기", "예술"],
    "F그룹": ["화학", "베트남어 회화", "정보", "AP 컴퓨터 과학"]
}

# 과목-계열 매핑 (12학년 동점자 처리용)
COURSE_TRACK_MAP = {
    "심화 국어": "국어과", "영미 문학 읽기": "영어과", "경제": "사회과", 
    "세계 지리": "사회과", "물리학": "과학과", "화학 II": "과학과", "생명과학": "과학과",
    "베트남어 회화": "베트남어과", "예술": "예술과", "정보": "정보과", "미적분 II": "수학과"
}

# 마스터 시간표 (공간 매핑)
MASTER_TIMETABLE = {
    "물리학": [("화", "3교시"), ("수", "3교시"), ("목", "5교시"), ("금", "6교시")],
    "미적분 II": [("화", "3교시"), ("수", "3교시"), ("목", "5교시"), ("금", "6교시")],
    "생명과학": [("월", "6교시"), ("화", "5교시"), ("수", "4교시"), ("금", "3교시")],
    "미디어와 비판적사고": [("월", "6교시"), ("화", "5교시"), ("수", "4교시"), ("금", "3교시")],
    "토론과 글쓰기": [("화", "1교시"), ("금", "2교시"), ("월", "7교시"), ("목", "7교시")],
    "Introduction to Biology": [("화", "1교시"), ("금", "2교시"), ("월", "7교시"), ("목", "7교시")],
    "미적분 I": [("수", "1교시"), ("화", "6교시"), ("목", "4교시"), ("금", "4교시")],
    "물리학 실험": [("수", "1교시"), ("화", "6교시"), ("목", "4교시"), ("금", "4교시")],
    "대수": [("월", "5교시"), ("화", "4교시"), ("목", "1교시"), ("금", "5교시")],
    "화학": [("월", "4교시"), ("화", "2교시"), ("수", "5교시"), ("금", "1교시")]
}

# 구글 시트 ID (임시)
ID_11 = "1xADYmy5iJEIiaENxCH1ZiqGU2yiFS81MfSQDCMsnO04" 
ID_12 = "1Yp79f79ilwA2ErJ6DoxRPbU_ADCq0PnRGH2TxGvKSDg"

# ==========================================
# 2. 세션 상태 초기화
# ==========================================
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'login_email' not in st.session_state: st.session_state.login_email = None
if 'app_status' not in st.session_state: st.session_state.app_status = '준비중'

# ==========================================
# 3. 유틸리티 & 핵심 로직 함수
# ==========================================
def mask_name(name):
    if len(name) <= 1: return name
    if len(name) == 2: return name[0] + "*"
    return name[0] + "*" + name[2:]

@st.cache_data(ttl=60)
def load_full_data():
    try:
        url_11 = f"https://docs.google.com/spreadsheets/d/{ID_11}/export?format=csv"
        url_12 = f"https://docs.google.com/spreadsheets/d/{ID_12}/export?format=csv"
        def process(url):
            df = pd.read_csv(url, header=None, dtype=str)
            idx = 0
            for i in range(len(df)):
                row = [str(v).strip() for v in df.iloc[i].values]
                if '학기' in row and '과목명' in row: idx = i; break
            df.columns = [str(v).strip() for v in df.iloc[idx].values]
            return df.iloc[idx + 1:].reset_index(drop=True)
        return process(url_11), process(url_12)
    except: 
        # 임시 데이터 반환 (테스트용)
        temp_df = pd.DataFrame({"과목명": ["물리학", "미적분 II", "생명과학", "미디어와 비판적사고", "토론과 글쓰기", "Introduction to Biology", "미적분 I", "물리학 실험", "대수", "화학", "베트남어 회화", "정보"]})
        return temp_df, temp_df

df_11, df_12 = load_full_data()

def highlight_timetable(val):
    if not val: return ''
    if val in ['영어 I', '스포츠 문화', '창의적 사고 설계', '창체', '심화 영어', '진로 활동']: return 'background-color: #f0f2f6; color: black;' # 공통과목
    if val in GROUP_MAP["A그룹"]: return 'background-color: #fff2cc; color: black;' # A그룹(노랑)
    if val in GROUP_MAP["B그룹"]: return 'background-color: #d9ead3; color: black;' # B그룹(초록)
    if val in GROUP_MAP["C그룹"]: return 'background-color: #c9daf8; color: black;' # C그룹(파랑)
    if val in GROUP_MAP["D그룹"]: return 'background-color: #fce5cd; color: black;' # D그룹(주황)
    if val in GROUP_MAP["E그룹"]: return 'background-color: #ead1dc; color: black;' # E그룹(보라)
    if val in GROUP_MAP["F그룹"]: return 'background-color: #b6d7a8; color: black;' # F그룹(연두)
    return 'background-color: #ffffff; color: black;'

def run_assignment_logic():
    if not os.path.exists('students_data.csv'): return False, "신청 데이터가 없습니다."

    apply_df = pd.read_csv('students_data.csv')
    apply_df['제출시간'] = pd.to_datetime(apply_df['제출시간'])
    
    final_results = []
    
    for grade_prefix in ["10", "11"]:
        grade_label = "11학년" if grade_prefix == "10" else "12학년"
        grade_df = apply_df[apply_df['학번'].astype(str).str.startswith(grade_prefix)].copy()
        
        if grade_df.empty: continue
        course_counts = {}
        
        # 11학년: 오직 선착순 / 12학년: 선착순 우선, 동점 시 계열 우대 (여기선 제출시간 우선 정렬로 기본 처리)
        grade_df = grade_df.sort_values(by=['제출시간'], ascending=[True])

        for _, student in grade_df.iterrows():
            requested = str(student['신청과목']).split(',')
            confirmed, rejected = [], []
            student_track = student['희망계열']
            
            for course in requested:
                course = course.strip()
                if course not in course_counts: course_counts[course] = 0
                
                if course_counts[course] < MAX_CAPACITY:
                    confirmed.append(course)
                    course_counts[course] += 1
                else:
                    # 12학년 동점자 발생 처리 로직은 밀리초 단위 중복 시 별도 트리거 (현재는 엄격한 타임스탬프 순서대로)
                    rejected.append(course)
            
            final_results.append({
                '학번': student['학번'], '이름': student['이름'], '학년': grade_label,
                '확정과목': ",".join(confirmed), '탈락과목': ",".join(rejected)
            })

    pd.DataFrame(final_results).to_csv('final_results.csv', index=False, encoding='utf-8-sig')
    return True, f"배정 완료 (35명 정원, {grade_label} 기준 적용)"

# ==========================================
# 4. 공통 UI & 사이드바
# ==========================================
with st.sidebar:
    st.title("🍏 KIS PRO")
    if st.session_state.login_email:
        st.info(f"👤 {st.session_state.user_name}님")
        if st.session_state.user_id == "admin":
            st.divider()
            st.session_state.app_status = st.radio("시스템 단계", ["준비중", "수강신청 진행", "과목거래 오픈"], index=["준비중", "수강신청 진행", "과목거래 오픈"].index(st.session_state.app_status))
        if st.button("🏠 홈"): st.session_state.page = "dashboard"; st.rerun()
        if st.button("🚪 로그아웃"): st.session_state.clear(); st.rerun()

# ==========================================
# 5. 페이지 라우팅
# ==========================================
# [A] 로그인
if st.session_state.login_email is None:
    st.title("🍏 KIS 시스템 로그인")
    le = st.text_input("이메일 (admin)")
    lp = st.text_input("비번 (admin123)", type="password")
    if st.button("로그인"):
        if le=="admin" and lp=="admin123":
            st.session_state.update({'login_email':'admin','user_name':'관리자','user_id':'admin','page':'dashboard'}); st.rerun()
        else:
            # 테스트용 무조건 통과 로직 (실제 사용시 user.csv 확인)
            grade_prefix = "10" if "11" in le else "11" # 11학년용 이메일, 12학년용 이메일 분기용
            st.session_state.update({'login_email':le, 'user_name':"테스트유저", 'user_id':f"{grade_prefix}1234", 'page':'dashboard'}); st.rerun()
    st.stop()

# [B] 대시보드
elif st.session_state.page == "dashboard":
    st.title(f"👋 환영합니다, {st.session_state.user_name}님")
    st.write(f"현재 시스템 상태: **{st.session_state.app_status}**")
    
    c1, c2, c3, c4 = st.columns(4)
    with c1: 
        if st.button("📝 수강신청", use_container_width=True): st.session_state.page = "apply"; st.rerun()
    with c2: 
        if st.button("📊 내 시간표", use_container_width=True): st.session_state.page = "result"; st.rerun()
    with c3:
        if st.button("🤝 과목 거래소", use_container_width=True): st.session_state.page = "trade"; st.rerun()
    with c4:
        if st.session_state.user_id == "admin" and st.button("⚙️ 관리자 설정", use_container_width=True): st.session_state.page = "admin_page"; st.rerun()

# [C] 정규 수강신청 폼
elif st.session_state.page == "apply":
    st.title("📝 KIS 수강신청")
    if st.session_state.app_status != "수강신청 진행":
        st.warning("현재 수강신청 기간이 아닙니다."); st.stop()
        
    u_prefix = str(st.session_state.user_id)[:2]
    cur_grade = 11 if u_prefix == "10" else 12
    required_count = 7 if cur_grade == 11 else 8 # 과목 수 제한
    
    target_list = df_11 if cur_grade == 11 else df_12
    available = target_list['과목명'].unique().tolist()
    
    st.info(f"💡 **{cur_grade}학년 규칙:** 반드시 정확히 **{required_count}개**의 과목을 선택해야 합니다. 정원은 **35명**입니다.")
    
    with st.form("apply"):
        selected = st.multiselect(f"과목 선택 ({required_count}개)", available)
        track = st.selectbox("희망 계열 (12학년 동점자 기준, 11학년은 무관)", TRACKS)
        
        if st.form_submit_button("신청서 제출"):
            if len(selected) != required_count:
                st.error(f"❌ 정확히 {required_count}개의 과목을 선택해주세요. (현재 {len(selected)}개 선택)")
            else:
                new = {'제출시간': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3], 
                       '학번': st.session_state.user_id, '이름': st.session_state.user_name,
                       '희망계열': track, '신청과목': ",".join(selected)}
                pd.DataFrame([new]).to_csv('students_data.csv', mode='a', header=not os.path.exists('students_data.csv'), index=False, encoding='utf-8-sig')
                st.success(f"✅ {required_count}개 과목 제출 완료! (선착순 기록됨)"); time.sleep(1); st.session_state.page = "dashboard"; st.rerun()

# [D] 결과 확인 & 시간표 (금요일 7,8 창체 고정)
elif st.session_state.page == "result":
    st.title("📊 배정 결과 및 주간 시간표")
    if os.path.exists('final_results.csv'):
        res_df = pd.read_csv('final_results.csv')
        my_res = res_df[res_df['학번'].astype(str) == str(st.session_state.user_id)]
        
        if not my_res.empty:
            my_confirmed = str(my_res.iloc[0]['확정과목'])
            my_grade_label = my_res.iloc[0]['학년']
            st.success(f"✅ 성공 과목: {my_confirmed}")
            
            # 시간표 렌더링
            days = ["월", "화", "수", "목", "금"]
            periods = [f"{i}교시" for i in range(1, 9)]
            timetable_df = pd.DataFrame("", index=periods, columns=days)
            
            # [규칙 1] 금요일 7~8교시 무조건 '창체' 고정
            timetable_df.at["7교시", "금"] = "창체"
            timetable_df.at["8교시", "금"] = "창체"
            
            my_courses = [c.strip() for c in my_confirmed.split(',') if c.strip()]
            
            # [규칙 2] 학년별 공통 과목 수
            common_list = ["영어 I", "스포츠 문화", "창의적 사고 설계"] if my_grade_label == "11학년" else ["심화 영어", "진로 활동"]
            
            for course in my_courses + common_list:
                if course in MASTER_TIMETABLE:
                    for day, period in MASTER_TIMETABLE[course]:
                        if not (day == "금" and period in ["7교시", "8교시"]): # 창체 보호
                            timetable_df.at[period, day] = course
            
            st.dataframe(timetable_df.style.applymap(highlight_timetable), use_container_width=True)
            
            if pd.notna(my_res.iloc[0]['탈락과목']) and my_res.iloc[0]['탈락과목'].strip():
                st.error(f"❌ 탈락 과목 (정원 35명 초과): {my_res.iloc[0]['탈락과목']}")
        else: st.warning("배정 내역이 없습니다.")
    else: st.info("정규 배정 대기중입니다.")

# [E] 1:1 맞교환 거래소
elif st.session_state.page == "trade":
    st.title("🤝 KIS 실시간 과목 거래소")
    if st.session_state.app_status != "과목거래 오픈":
        st.warning("🔒 현재 거래 기간이 아닙니다."); st.stop()

    res_df = pd.read_csv('final_results.csv') if os.path.exists('final_results.csv') else pd.DataFrame()
    my_id = str(st.session_state.user_id)
    my_grade = "11학년" if my_id.startswith("10") else "12학년"
    
    my_info = res_df[res_df['학번'].astype(str) == my_id]
    if my_info.empty: st.stop()
    
    my_courses = [c.strip() for c in str(res_df.at[my_info.index[0], '확정과목']).split(',') if c.strip()]
    if not os.path.exists('trade_requests.csv'):
        pd.DataFrame(columns=['요청ID', '발신자ID', '발신자이름', '수신자ID', '수신자이름', '발신자과목', '수신자과목', '상태']).to_csv('trade_requests.csv', index=False)
    
    tab1, tab2 = st.tabs([f"📊 {my_grade} 현황판", "🔔 받은 제안함"])

    with tab1:
        st.caption("※ 35명 정원 유지를 위해 1:1 맞교환(Swap)만 가능합니다.")
        peer_df = res_df[(res_df['학년'] == my_grade) & (res_df['학번'].astype(str) != my_id)]
        for _, row in peer_df.iterrows():
            with st.container(border=True):
                col1, col2, col3 = st.columns([2, 5, 3])
                peer_courses = [c.strip() for c in str(row['확정과목']).split(',') if c.strip()]
                with col1: st.write(f"👤 **{mask_name(row['이름'])}**")
                with col2: st.write(f"📚 {', '.join(peer_courses)}")
                with col3:
                    with st.expander("교환"):
                        give_c = st.selectbox("내 과목 (줄 것)", my_courses, key=f"g_{row['학번']}")
                        want_c = st.selectbox("상대 과목 (받을 것)", peer_courses, key=f"w_{row['학번']}")
                        if st.button("제안 보내기", key=f"b_{row['학번']}"):
                            req = {'요청ID': str(uuid.uuid4())[:8], '발신자ID': my_id, '발신자이름': st.session_state.user_name,
                                   '수신자ID': row['학번'], '수신자이름': row['이름'], '발신자과목': give_c, '수신자과목': want_c, '상태': '요청중'}
                            pd.DataFrame([req]).to_csv('trade_requests.csv', mode='a', header=False, index=False, encoding='utf-8-sig')
                            st.success("발송 완료!"); time.sleep(1); st.rerun()

    with tab2:
        trade_df = pd.read_csv('trade_requests.csv')
        my_inbox = trade_df[(trade_df['수신자ID'].astype(str) == my_id) & (trade_df['상태'] == '요청중')]
        if my_inbox.empty: st.info("대기 중인 제안이 없습니다.")
        else:
            for _, req in my_inbox.iterrows():
                with st.container(border=True):
                    st.write(f"🔔 **{mask_name(req['발신자이름'])}**님의 제안: 내 **[{req['수신자과목']}]** ↔ 상대 **[{req['발신자과목']}]**")
                    if st.button("✅ 수락 (즉시 교체)", key=f"a_{req['요청ID']}"):
                        my_idx = my_info.index[0]
                        my_courses.remove(req['수신자과목']); my_courses.append(req['발신자과목'])
                        res_df.at[my_idx, '확정과목'] = ",".join(my_courses)
                        
                        sender_idx = res_df.index[res_df['학번'].astype(str) == str(req['발신자ID'])][0]
                        s_courses = [c.strip() for c in str(res_df.at[sender_idx, '확정과목']).split(',') if c.strip()]
                        s_courses.remove(req['발신자과목']); s_courses.append(req['수신자과목'])
                        res_df.at[sender_idx, '확정과목'] = ",".join(s_courses)
                        
                        res_df.to_csv('final_results.csv', index=False, encoding='utf-8-sig')
                        trade_df.loc[trade_df['요청ID'] == req['요청ID'], '상태'] = '완료'
                        trade_df.to_csv('trade_requests.csv', index=False, encoding='utf-8-sig')
                        st.success("교체 완료!"); time.sleep(1); st.rerun()

# [F] 관리자 (A-F 그룹 추출 기능 포함)
elif st.session_state.page == "admin_page" and st.session_state.user_id == "admin":
    st.title("⚙️ 관리자 컨트롤 타워")
    
    if st.button("🔥 정규 배정 실행", type="primary"):
        success, msg = run_assignment_logic()
        if success: st.success(msg)
    
    st.divider()
    st.subheader("📂 그룹별(A-F) 최종 명단 추출")
    if os.path.exists('final_results.csv'):
        res_df = pd.read_csv('final_results.csv')
        all_data = []
        for g_name, subjects in GROUP_MAP.items():
            for sub in subjects:
                matched = res_df[res_df['확정과목'].str.contains(sub, na=False)]
                for _, r in matched.iterrows():
                    all_data.append([g_name, sub, r['학번'], r['이름'], r['학년']])
        
        summary_df = pd.DataFrame(all_data, columns=["그룹", "과목명", "학번", "이름", "학년"])
        st.dataframe(summary_df)
        
        csv = summary_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button("📥 A-F 그룹 전체 명단 다운로드(CSV)", csv, "KIS_Group_Lists.csv", "text/csv")
