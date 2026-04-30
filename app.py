import streamlit as st
import pandas as pd
import os
import time
import uuid
from datetime import datetime

# ==========================================
# 1. 기본 설정 및 데이터 (Constants)
# ==========================================
st.set_page_config(page_title="KIS 수강신청 시스템", layout="wide", page_icon="🍏")

MAX_CAPACITY = 35  # 최대 정원 35명
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

# 마스터 시간표 (공간 매핑)
MASTER_TIMETABLE = {
    "물리학": [("화", "3교시"), ("수", "3교시"), ("목", "5교시"), ("금", "6교시")],
    "미적분 II": [("화", "3교시"), ("수", "3교시"), ("목", "5교시"), ("금", "6교시")],
    "생명과학": [("월", "6교시"), ("화", "5교시"), ("수", "4교시"), ("금", "3교시")],
    "경제": [("월", "6교시"), ("화", "5교시"), ("수", "4교시"), ("금", "3교시")],
    "토론과 글쓰기": [("화", "1교시"), ("금", "2교시"), ("월", "7교시"), ("목", "7교시")],
    "세계 지리": [("화", "1교시"), ("금", "2교시"), ("월", "7교시"), ("목", "7교시")],
    "미적분 I": [("수", "1교시"), ("화", "6교시"), ("목", "4교시"), ("금", "4교시")],
    "화학 II": [("수", "1교시"), ("화", "6교시"), ("목", "4교시"), ("금", "4교시")],
    "대수": [("월", "5교시"), ("화", "4교시"), ("목", "1교시"), ("금", "5교시")],
    "화학": [("월", "4교시"), ("화", "2교시"), ("수", "5교시"), ("금", "1교시")],
    "정보": [("월", "4교시"), ("화", "2교시"), ("수", "5교시"), ("금", "1교시")]
}

# 구글 시트 ID (임시)
ID_11 = "1xADYmy5iJEIiaENxCH1ZiqGU2yiFS81MfSQDCMsnO04" 
ID_12 = "1Yp79f79ilwA2ErJ6DoxRPbU_ADCq0PnRGH2TxGvKSDg"

# ==========================================
# 2. 세션 상태 초기화
# ==========================================
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'user_id' not in st.session_state: st.session_state.user_id = None
if 'app_status' not in st.session_state: st.session_state.app_status = '준비중'
if 'selected_semester' not in st.session_state: st.session_state.selected_semester = '1학기'

# ==========================================
# 3. 유틸리티 & 핵심 로직
# ==========================================
def mask_name(name):
    if not isinstance(name, str) or len(name) <= 1: return str(name)
    if len(name) == 2: return name[0] + "*"
    return name[0] + "*" + name[2:]

def get_files():
    sem = st.session_state.selected_semester
    return f"apply_data_{sem}.csv", f"results_{sem}.csv", f"trade_{sem}.csv"

@st.cache_data(ttl=60)
def load_and_filter_data(semester):
    try:
        def process(url, sem):
            df = pd.read_csv(url, dtype=str)
            if '학기' in df.columns:
                df = df[df['학기'].str.contains(sem.replace("학기", ""), na=False)]
            return df.reset_index(drop=True)
        return process(f"https://docs.google.com/spreadsheets/d/{ID_11}/export?format=csv", semester), \
               process(f"https://docs.google.com/spreadsheets/d/{ID_12}/export?format=csv", semester)
    except:
        dummy_data = {
            "학기": ["1", "1", "1", "1", "1", "1", "1", "1", "2", "2", "2", "2"],
            "과목명": ["물리학", "생명과학", "토론과 글쓰기", "미적분 I", "대수", "화학", "심화 국어", "경제", 
                    "미적분 II", "화학 II", "세계 지리", "정보"]
        }
        df = pd.DataFrame(dummy_data)
        res = df[df['학기'] == semester.replace("학기", "")]
        return res, res

def highlight_timetable(val):
    if not val: return ''
    if val in ['영어 I', '스포츠 문화', '창의적 사고 설계', '창체', '심화 영어', '진로 활동']: 
        return 'background-color: #f0f2f6; color: black;' 
    for g_name, subjects in GROUP_MAP.items():
        if val in subjects:
            colors = {"A그룹":"#fff2cc", "B그룹":"#d9ead3", "C그룹":"#c9daf8", "D그룹":"#fce5cd", "E그룹":"#ead1dc", "F그룹":"#b6d7a8"}
            return f'background-color: {colors[g_name]}; color: black;'
    return 'background-color: #ffffff; color: black;'

def run_assignment(semester):
    apply_file, result_file, _ = get_files()
    if not os.path.exists(apply_file): return False, f"{semester} 신청 데이터가 없습니다."

    df = pd.read_csv(apply_file)
    df['제출시간'] = pd.to_datetime(df['제출시간'])
    df = df.sort_values(by=['제출시간'], ascending=[True]) # 선착순 정렬
    
    final_results = []
    course_counts = {}

    for _, student in df.iterrows():
        requested = str(student.get('신청과목', '')).split(',')
        confirmed, rejected = [], []
        
        for course in requested:
            course = course.strip()
            if not course: continue
            if course not in course_counts: course_counts[course] = 0
            
            if course_counts[course] < MAX_CAPACITY:
                confirmed.append(course)
                course_counts[course] += 1
            else:
                rejected.append(course)
        
        final_results.append({
            '학번': student.get('학번', ''), 
            '이름': student.get('이름', ''), 
            '학년': student.get('학년', '미상'),
            '확정과목': ",".join(confirmed), 
            '탈락과목': ",".join(rejected)
        })

    pd.DataFrame(final_results).to_csv(result_file, index=False, encoding='utf-8-sig')
    return True, f"배정 완료 (35명 정원, {semester} 기준)"

# ==========================================
# 4. 사이드바 (관리자 컨트롤)
# ==========================================
with st.sidebar:
    st.title("🍏 KIS PRO")
    if st.session_state.user_id:
        st.write(f"👤 **{st.session_state.user_name}**님")
        
        if st.session_state.user_id == "admin":
            st.divider()
            st.subheader("⚙️ 관리자 제어판")
            st.session_state.selected_semester = st.selectbox("📅 진행 학기 선택", ["1학기", "2학기"])
            st.session_state.app_status = st.radio("🚦 시스템 상태", ["준비중", "수강신청 진행", "과목거래 오픈"])
            st.success(f"현재 설정: {st.session_state.selected_semester} / {st.session_state.app_status}")
            
        st.divider()
        if st.button("🏠 홈으로"): st.session_state.page = "dashboard"; st.rerun()
        if st.button("🚪 로그아웃"): st.session_state.clear(); st.rerun()

# ==========================================
# 5. 페이지 라우팅
# ==========================================

# [A] 로그인
if st.session_state.page == 'login':
    st.title("🏢 KIS 수강신청 로그인")
    uid = st.text_input("학번 (10...: 11학년 / 11...: 12학년 / 관리자: admin)")
    upw = st.text_input("비밀번호", type="password")
    
    if st.button("로그인"):
        if uid == "admin" and upw == "admin123":
            st.session_state.update({'user_id':'admin', 'user_name':'관리자', 'page':'dashboard'})
            st.rerun()
        elif uid.startswith("10") or uid.startswith("11"):
            gr = "11학년" if uid.startswith("10") else "12학년"
            st.session_state.update({'user_id':uid, 'user_name':f"학생_{uid}", 'grade':gr, 'page':'dashboard'})
            st.rerun()
        else:
            st.error("올바른 학번을 입력하세요 (10... 또는 11...)")

# [B] 대시보드
elif st.session_state.page == 'dashboard':
    st.title(f"👋 반갑습니다, {st.session_state.user_name}님")
    st.info(f"📍 현재 모드: **{st.session_state.selected_semester}** ({st.session_state.app_status})")
    
    if st.session_state.user_id != "admin" and st.session_state.app_status == "준비중":
        st.error("🔒 관리자가 수강신청을 오픈할 때까지 기다려주세요.")
        
    c1, c2, c3 = st.columns(3)
    with c1:
        is_open = st.session_state.app_status == "수강신청 진행"
        if st.button("📝 수강신청", use_container_width=True, disabled=not is_open, type="primary" if is_open else "secondary"):
            st.session_state.page = "apply"; st.rerun()
    with c2:
        if st.button("📊 결과/시간표", use_container_width=True): st.session_state.page = "result"; st.rerun()
    with c3:
        if st.button("🤝 과목 거래소", use_container_width=True): st.session_state.page = "trade"; st.rerun()
        
    if st.session_state.user_id == "admin":
        st.divider()
        if st.button("⚙️ 관리자 데이터 관리", type="primary"): st.session_state.page = "admin"; st.rerun()

# [C] 정규 수강신청 폼 (🔥 max_selections 적용)
elif st.session_state.page == 'apply':
    st.title(f"📝 {st.session_state.selected_semester} 수강신청")
    if st.session_state.app_status != "수강신청 진행":
        st.warning("기간이 아닙니다."); st.stop()
        
    req_count = 7 if st.session_state.grade == "11학년" else 8
    df_11, df_12 = load_and_filter_data(st.session_state.selected_semester)
    target_list = df_11 if st.session_state.grade == "11학년" else df_12
    
    if target_list.empty:
        st.error(f"{st.session_state.selected_semester} 개설 과목이 없습니다."); st.stop()
        
    available = target_list['과목명'].unique().tolist()
    st.info(f"💡 {st.session_state.grade}은 반드시 **{req_count}개**를 선택해야 합니다. ({req_count}개를 초과하여 누를 수 없습니다!)")
    
    with st.form("apply_form"):
        # 🔥 max_selections 파라미터 추가: 물리적으로 학년에 맞는 개수까지만 클릭 가능!
        selected = st.multiselect(
            f"수강 희망 과목 (최대 {req_count}개 선택)", 
            available, 
            max_selections=req_count
        )
        track = st.selectbox("희망 계열 (12학년 동점자 처리용)", TRACKS)
        
        if st.form_submit_button("신청서 제출"):
            if len(selected) != req_count:
                st.error(f"❌ 정확히 {req_count}개를 골라주세요! (현재 {len(selected)}개 선택됨)")
            else:
                apply_file, _, _ = get_files()
                new_data = {
                    '학기': st.session_state.selected_semester,
                    '제출시간': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                    '학번': st.session_state.user_id, 
                    '이름': st.session_state.user_name,
                    '학년': st.session_state.grade, 
                    '희망계열': track,
                    '신청과목': ",".join(selected)
                }
                pd.DataFrame([new_data]).to_csv(apply_file, mode='a', header=not os.path.exists(apply_file), index=False, encoding='utf-8-sig')
                st.success(f"✅ {st.session_state.selected_semester} 제출 완료!"); time.sleep(1); st.session_state.page = "dashboard"; st.rerun()

# [D] 결과 확인 및 시간표 (🔥 KeyError 방어 로직 추가)
elif st.session_state.page == 'result':
    st.title(f"📊 {st.session_state.selected_semester} 시간표")
    _, result_file, _ = get_files()
    
    if os.path.exists(result_file):
        res_df = pd.read_csv(result_file)
        my_res = res_df[res_df['학번'].astype(str) == str(st.session_state.user_id)]
        
        if not my_res.empty:
            # .get()을 사용하여 예전 파일에 해당 컬럼이 없어도 에러가 나지 않음
            my_confirmed = str(my_res.iloc[0].get('확정과목', ''))
            my_grade = my_res.iloc[0].get('학년', st.session_state.get('grade', '11학년'))
            
            st.success(f"✅ 배정 과목: {my_confirmed}")
            
            days = ["월", "화", "수", "목", "금"]
            periods = [f"{i}교시" for i in range(1, 9)]
            timetable = pd.DataFrame("", index=periods, columns=days)
            
            timetable.at["7교시", "금"] = "창체"
            timetable.at["8교시", "금"] = "창체"
            
            common = ["영어 I", "스포츠 문화", "창의적 사고 설계"] if my_grade == "11학년" else ["심화 영어", "진로 활동"]
            my_courses = [c.strip() for c in my_confirmed.split(',') if c.strip()] + common
            
            for c in my_courses:
                if c in MASTER_TIMETABLE:
                    for day, p in MASTER_TIMETABLE[c]:
                        if not (day == "금" and p in ["7교시", "8교시"]): 
                            timetable.at[p, day] = c
                            
            st.dataframe(timetable.style.applymap(highlight_timetable), use_container_width=True)
            
            rejected = str(my_res.iloc[0].get('탈락과목', ''))
            if rejected and rejected != 'nan':
                st.error(f"❌ 탈락(대기): {rejected}")
        else: st.warning("배정 내역이 없습니다.")
    else: st.info("아직 배정이 진행되지 않았습니다.")

# [E] 과목 거래소
elif st.session_state.page == 'trade':
    st.title(f"🤝 {st.session_state.selected_semester} 과목 거래소")
    if st.session_state.app_status != "과목거래 오픈": st.warning("🔒 닫혀있습니다."); st.stop()

    _, result_file, trade_file = get_files()
    if not os.path.exists(result_file): st.stop()
    
    res_df = pd.read_csv(result_file)
    my_id = str(st.session_state.user_id)
    my_info = res_df[res_df['학번'].astype(str) == my_id]
    if my_info.empty: st.stop()
    
    my_courses = [c.strip() for c in str(my_info.iloc[0].get('확정과목', '')).split(',') if c.strip()]
    my_grade = my_info.iloc[0].get('학년', st.session_state.grade)
    
    if not os.path.exists(trade_file): 
        pd.DataFrame(columns=['요청ID','발신ID','발신자','수신ID','수신자','줄과목','받을과목','상태']).to_csv(trade_file, index=False)
    
    t1, t2 = st.tabs(["전체 현황판", "받은 제안"])
    with t1:
        # KeyError 방어를 위해 get() 활용
        if '학년' in res_df.columns:
            peer_df = res_df[(res_df['학년'] == my_grade) & (res_df['학번'].astype(str) != my_id)]
        else:
            peer_df = res_df[res_df['학번'].astype(str) != my_id] # 학년 컬럼이 없으면 본인 빼고 전부 표시
            
        for _, row in peer_df.iterrows():
            with st.container(border=True):
                c1, c2, c3 = st.columns([2,5,3])
                p_courses = [c.strip() for c in str(row.get('확정과목', '')).split(',') if c.strip()]
                with c1: st.write(f"👤 {mask_name(row.get('이름', '알수없음'))}")
                with c2: st.write(", ".join(p_courses))
                with c3:
                    with st.expander("교환 제안"):
                        give = st.selectbox("줄 과목", my_courses, key=f"g_{row['학번']}")
                        want = st.selectbox("받을 과목", p_courses, key=f"w_{row['학번']}")
                        if st.button("제안", key=f"b_{row['학번']}"):
                            req = {'요청ID': str(uuid.uuid4())[:8], '발신ID': my_id, '발신자': st.session_state.user_name,
                                   '수신ID': row['학번'], '수신자': row.get('이름', ''), '줄과목': give, '받을과목': want, '상태': '요청중'}
                            pd.DataFrame([req]).to_csv(trade_file, mode='a', header=False, index=False, encoding='utf-8-sig')
                            st.success("전송 완료!"); time.sleep(1); st.rerun()

    with t2:
        trade_df = pd.read_csv(trade_file)
        my_inbox = trade_df[(trade_df['수신ID'].astype(str) == my_id) & (trade_df['상태'] == '요청중')]
        if my_inbox.empty: st.info("제안이 없습니다.")
        for _, req in my_inbox.iterrows():
            with st.container(border=True):
                st.write(f"🔔 **{mask_name(req['발신자'])}**님: 내 **[{req['받을과목']}]** ↔ 상대 **[{req['줄과목']}]**")
                if st.button("✅ 수락(즉시반영)", key=f"a_{req['요청ID']}"):
                    my_courses.remove(req['받을과목']); my_courses.append(req['줄과목'])
                    res_df.at[my_info.index[0], '확정과목'] = ",".join(my_courses)
                    s_idx = res_df.index[res_df['학번'].astype(str) == str(req['발신ID'])][0]
                    s_courses = [c.strip() for c in str(res_df.at[s_idx, '확정과목']).split(',')]
                    s_courses.remove(req['줄과목']); s_courses.append(req['받을과목'])
                    res_df.at[s_idx, '확정과목'] = ",".join(s_courses)
                    
                    res_df.to_csv(result_file, index=False, encoding='utf-8-sig')
                    trade_df.loc[trade_df['요청ID'] == req['요청ID'], '상태'] = '완료'
                    trade_df.to_csv(trade_file, index=False, encoding='utf-8-sig')
                    st.success("교환 성사!"); time.sleep(1); st.rerun()

# [F] 관리자 데이터 관리 (🔥 KeyError 방어 로직 추가)
elif st.session_state.page == 'admin' and st.session_state.user_id == "admin":
    st.title("⚙️ 관리자 전용 제어")
    sem = st.session_state.selected_semester
    
    if st.button(f"🔥 {sem} 선착순 정규 배정 실행", type="primary"):
        suc, msg = run_assignment(sem)
        if suc: st.success(msg) 
        else: st.error(msg)
        
    st.divider()
    st.subheader(f"📂 {sem} 그룹별(A-F) 최종 명단 추출")
    _, result_file, _ = get_files()
    if os.path.exists(result_file):
        res_df = pd.read_csv(result_file)
        all_data = []
        
        for g_name, subjects in GROUP_MAP.items():
            for sub in subjects:
                if '확정과목' in res_df.columns:
                    matched = res_df[res_df['확정과목'].str.contains(sub, na=False)]
                    for _, r in matched.iterrows():
                        # .get('학년', '미상') 처리로 에러를 완벽 차단!
                        all_data.append([g_name, sub, r.get('학번', ''), r.get('이름', ''), r.get('학년', '미상')])
                        
        sum_df = pd.DataFrame(all_data, columns=["그룹", "과목명", "학번", "이름", "학년"])
        st.dataframe(sum_df)
        csv = sum_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button(f"📥 {sem} 전체 명단 다운로드(CSV)", csv, f"KIS_Group_{sem}.csv", "text/csv")
