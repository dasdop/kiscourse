import streamlit as st
import pandas as pd
import os
import time
import uuid
from datetime import datetime

# ==========================================
# 1. 기본 설정 및 데이터 (오타 방지용 별칭 추가)
# ==========================================
st.set_page_config(page_title="KIS 수강신청 시스템", layout="wide", page_icon="🍏")

MAX_CAPACITY = 35
TRACKS = ['국어과', '영어과', '수학과', '사회과', '과학과', '베트남어과', '예술과', '정보과']

GROUP_MAP = {
    "A그룹": ["물리학", "미적분 II", "심화 국어", "프레젠테이션 화법", "프리젠테이션 화법"],
    "B그룹": ["생명과학", "미디어와 비판적사고", "경제", "글로벌 이슈 글쓰기"],
    "C그룹": ["토론과 글쓰기", "Introduction to Biology", "세계 지리", "영어 발표와 토론"],
    "D그룹": ["미적분 I", "물리학 실험", "화학 II", "Contemporary Literature"],
    "E그룹": ["대수", "영미 문학 읽기", "예술", "Adventures in Writing"],
    "F그룹": ["화학", "베트남어 회화", "정보", "Comprehensive English", "AP 컴퓨터 과학"]
}

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
    "정보": [("월", "4교시"), ("화", "2교시"), ("수", "5교시"), ("금", "1교시")],
    
    "프레젠테이션 화법": [("화", "3교시"), ("수", "3교시"), ("목", "5교시"), ("금", "6교시")],
    "프리젠테이션 화법": [("화", "3교시"), ("수", "3교시"), ("목", "5교시"), ("금", "6교시")], # 오타 대비
    "글로벌 이슈 글쓰기": [("월", "6교시"), ("화", "5교시"), ("수", "4교시"), ("금", "3교시")],
    "영어 발표와 토론": [("화", "1교시"), ("금", "2교시"), ("월", "7교시"), ("목", "7교시")],
    "Contemporary Literature": [("수", "1교시"), ("화", "6교시"), ("목", "4교시"), ("금", "4교시")],
    "Adventures in Writing": [("월", "5교시"), ("화", "4교시"), ("목", "1교시"), ("금", "5교시")],
    "Comprehensive English": [("월", "4교시"), ("화", "2교시"), ("수", "5교시"), ("금", "1교시")],
    "문학과 여행(국어)": [("월", "1교시"), ("화", "1교시"), ("수", "1교시"), ("목", "1교시")],
    
    "영어 I": [("월", "2교시"), ("목", "2교시")],
    "스포츠 문화": [("월", "3교시"), ("목", "3교시")],
    "창의적 사고 설계": [("수", "2교시")],
    "심화 영어": [("월", "2교시"), ("목", "2교시")],
    "진로 활동": [("월", "3교시"), ("목", "3교시")]
}

ID_11 = "1xADYmy5iJEIiaENxCH1ZiqGU2yiFS81MfSQDCMsnO04" 
ID_12 = "1Yp79f79ilwA2ErJ6DoxRPbU_ADCq0PnRGH2TxGvKSDg"

# ==========================================
# 2. 세션 상태 초기화 및 보호 (오류 1 방어)
# ==========================================
if 'page' not in st.session_state: st.session_state.page = 'login'
if 'user_id' not in st.session_state: st.session_state.user_id = None
if 'app_status' not in st.session_state: st.session_state.app_status = '준비중'
if 'selected_semester' not in st.session_state: st.session_state.selected_semester = '1학기'

# 로그인 풀림 방지 로직 (강제 로그인 창 이동)
if st.session_state.page != 'login' and st.session_state.user_id is None:
    st.session_state.page = 'login'
    st.rerun()

# 학생인데 grade가 날아간 경우 방어
if st.session_state.user_id and st.session_state.user_id != "admin" and 'grade' not in st.session_state:
    st.session_state.page = 'login'
    st.session_state.user_id = None
    st.rerun()

# ==========================================
# 3. 유틸리티 로직
# ==========================================
def mask_name(name):
    name = str(name)
    if len(name) <= 1: return name
    if len(name) == 2: return name[0] + "*"
    return name[0] + "*" + name[2:]

def get_files():
    sem = st.session_state.selected_semester
    return f"apply_data_{sem}.csv", f"results_{sem}.csv", f"trade_{sem}.csv"

@st.cache_data(ttl=60)
def load_and_filter_data(semester):
    # 구글 시트 에러(오류 4) 방어용 기본 데이터
    dummy_df = pd.DataFrame({
        "학기": ["1"]*12 + ["2"]*12,
        "과목명": ["물리학", "생명과학", "토론과 글쓰기", "미적분 I", "대수", "화학", "심화 국어", "경제", "미적분 II", "화학 II", "세계 지리", "정보"] * 2
    })
    try:
        def process(url, sem):
            df = pd.read_csv(url, dtype=str)
            df.columns = df.columns.str.strip()
            if '과목명' not in df.columns: return None # 열 이름이 틀린 경우
            if '학기' in df.columns: 
                df = df[df['학기'].str.contains(sem.replace("학기", ""), na=False)]
            return df.reset_index(drop=True)
            
        df_11 = process(f"https://docs.google.com/spreadsheets/d/{ID_11}/export?format=csv", semester)
        df_12 = process(f"https://docs.google.com/spreadsheets/d/{ID_12}/export?format=csv", semester)
        
        if df_11 is None or '과목명' not in df_11.columns: df_11 = dummy_df[dummy_df['학기'] == semester.replace("학기", "")]
        if df_12 is None or '과목명' not in df_12.columns: df_12 = dummy_df[dummy_df['학기'] == semester.replace("학기", "")]
        return df_11, df_12
    except Exception:
        return dummy_df[dummy_df['학기'] == semester.replace("학기", "")], dummy_df[dummy_df['학기'] == semester.replace("학기", "")]

def highlight_timetable(val):
    if not val: return ''
    if val in ['영어 I', '스포츠 문화', '창의적 사고 설계', '창체', '심화 영어', '진로 활동']: 
        return 'background-color: #f0f2f6; color: black;' 
    for g_name, subjects in GROUP_MAP.items():
        if val in subjects:
            colors = {"A그룹":"#fff2cc", "B그룹":"#d9ead3", "C그룹":"#c9daf8", "D그룹":"#fce5cd", "E그룹":"#ead1dc", "F그룹":"#b6d7a8"}
            return f'background-color: {colors[g_name]}; color: black;'
    if "💥충돌" in val: return 'background-color: #ffcccc; color: red; font-weight: bold;'
    return 'background-color: #ffffff; color: black;'

# Pandas 버전 업데이트 에러(오류 2) 완전 해결 함수
def draw_styled_dataframe(df):
    styler = df.style
    if hasattr(styler, "map"):
        styled_df = styler.map(highlight_timetable)
    else:
        # 구버전 파이썬을 위한 예비책 (최근 Streamlit에서는 map 사용)
        styled_df = styler.applymap(highlight_timetable)
    st.dataframe(styled_df, use_container_width=True)

def run_assignment(semester):
    apply_file, result_file, _ = get_files()
    if not os.path.exists(apply_file): return False, f"{semester} 신청 데이터가 없습니다."

    df = pd.read_csv(apply_file)
    df['제출시간'] = pd.to_datetime(df['제출시간'])
    df = df.sort_values(by=['제출시간'], ascending=[True])
    
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
            '학번': student.get('학번', ''), '이름': student.get('이름', ''), '학년': student.get('학년', '미상'),
            '확정과목': ",".join(confirmed), '탈락과목': ",".join(rejected)
        })

    pd.DataFrame(final_results).to_csv(result_file, index=False, encoding='utf-8-sig')
    return True, f"배정 완료 (35명 정원, {semester} 기준)"

# ==========================================
# 4. 사이드바 
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
            st.session_state.update({'user_id':'admin', 'user_name':'관리자', 'page':'dashboard'}); st.rerun()
        elif uid.startswith("10") or uid.startswith("11"):
            gr = "11학년" if uid.startswith("10") else "12학년"
            st.session_state.update({'user_id':uid, 'user_name':f"학생_{uid}", 'grade':gr, 'page':'dashboard'}); st.rerun()
        else: st.error("올바른 학번을 입력하세요")

# [B] 대시보드
elif st.session_state.page == 'dashboard':
    st.title(f"👋 반갑습니다, {st.session_state.user_name}님")
    st.info(f"📍 현재 모드: **{st.session_state.selected_semester}** ({st.session_state.app_status})")
    
    if st.session_state.user_id != "admin" and st.session_state.app_status == "준비중":
        st.error("🔒 관리자가 수강신청을 오픈할 때까지 대기해주세요.")
        
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        is_open = st.session_state.app_status == "수강신청 진행"
        if st.button("📝 실전 수강신청", use_container_width=True, disabled=not is_open, type="primary" if is_open else "secondary"):
            st.session_state.page = "apply"; st.rerun()
    with c2:
        if st.button("📊 결과/시간표", use_container_width=True): st.session_state.page = "result"; st.rerun()
    with c3:
        if st.button("🤝 과목 거래소", use_container_width=True): st.session_state.page = "trade"; st.rerun()
    with c4:
        if st.button("🎮 시뮬레이션", use_container_width=True): st.session_state.page = "simulation"; st.rerun()
        
    if st.session_state.user_id == "admin":
        st.divider()
        if st.button("⚙️ 관리자 전용 데이터 관리", type="primary"): st.session_state.page = "admin"; st.rerun()

# [C] 정규 수강신청 폼
elif st.session_state.page == 'apply':
    st.title(f"📝 {st.session_state.selected_semester} 실전 수강신청")
    if st.session_state.app_status != "수강신청 진행": st.warning("기간이 아닙니다."); st.stop()
        
    req_count = 7 if st.session_state.get('grade', '11학년') == "11학년" else 8
    df_11, df_12 = load_and_filter_data(st.session_state.selected_semester)
    target_list = df_11 if st.session_state.get('grade', '11학년') == "11학년" else df_12
    available = target_list['과목명'].dropna().unique().tolist() if '과목명' in target_list.columns else []
    
    with st.form("apply_form"):
        selected = st.multiselect(f"수강 희망 과목 (최대 {req_count}개 선택)", available, max_selections=req_count)
        track = st.selectbox("희망 계열", TRACKS)
        
        if st.form_submit_button("신청서 제출"):
            if len(selected) != req_count: st.error(f"❌ 정확히 {req_count}개를 골라주세요!")
            else:
                apply_file, _, _ = get_files()
                new_data = {
                    '학기': st.session_state.selected_semester,
                    '제출시간': datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],
                    '학번': st.session_state.user_id, '이름': st.session_state.user_name,
                    '학년': st.session_state.get('grade', '미상'), '희망계열': track, '신청과목': ",".join(selected)
                }
                pd.DataFrame([new_data]).to_csv(apply_file, mode='a', header=not os.path.exists(apply_file), index=False, encoding='utf-8-sig')
                st.success("✅ 제출 완료!"); time.sleep(1); st.session_state.page = "dashboard"; st.rerun()

# [D] 시뮬레이션
elif st.session_state.page == 'simulation':
    st.title("🎮 수강신청 시뮬레이션")
    gr = st.radio("테스트할 학년", ["11학년", "12학년"]) if st.session_state.user_id == "admin" else st.session_state.get('grade', '11학년')
    req_count = 7 if gr == "11학년" else 8
    
    df_11, df_12 = load_and_filter_data(st.session_state.selected_semester)
    target_list = df_11 if gr == "11학년" else df_12
    available = target_list['과목명'].dropna().unique().tolist() if '과목명' in target_list.columns else []
    
    sim_selected = st.multiselect(f"과목을 담아보세요 (최대 {req_count}개)", available, max_selections=req_count)
    
    if st.button("시간표 그리기"):
        days = ["월", "화", "수", "목", "금"]
        periods = [f"{i}교시" for i in range(1, 9)]
        timetable = pd.DataFrame("", index=periods, columns=days)
        
        timetable.at["7교시", "금"] = "창체"
        timetable.at["8교시", "금"] = "창체"
        
        common = ["영어 I", "스포츠 문화", "창의적 사고 설계"] if gr == "11학년" else ["심화 영어", "진로 활동"]
        all_sim_courses = sim_selected + common
        
        not_found = []
        for c in all_sim_courses:
            match_found = False
            for master_key in MASTER_TIMETABLE.keys():
                # 부분 일치로 인식 강화 (Comprehensive English III -> Comprehensive English 매칭)
                if master_key in c or c in master_key:
                    for day, p in MASTER_TIMETABLE[master_key]:
                        if not (day == "금" and p in ["7교시", "8교시"]): 
                            current_val = timetable.at[p, day]
                            if current_val == "": timetable.at[p, day] = master_key
                            else: timetable.at[p, day] = f"💥충돌 ({current_val} / {master_key})"
                    match_found = True
                    break
            if not match_found and c not in common:
                not_found.append(c)
        
        if not_found:
            st.warning(f"⚠️ 다음 과목은 시간표 데이터에 없어 표시되지 않습니다: {', '.join(not_found)}")
            
        draw_styled_dataframe(timetable)

# [E] 결과 확인 및 시간표 (오류 3 방어)
elif st.session_state.page == 'result':
    st.title(f"📊 {st.session_state.selected_semester} 시간표")
    _, result_file, _ = get_files()
    
    if os.path.exists(result_file):
        res_df = pd.read_csv(result_file)
        my_res = res_df[res_df['학번'].astype(str) == str(st.session_state.user_id)]
        
        if not my_res.empty:
            my_confirmed = str(my_res.iloc[0].get('확정과목', ''))
            # get()을 사용하여 '학년' 열이 없어도 에러가 나지 않도록 처리
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
                for master_key in MASTER_TIMETABLE.keys():
                    if master_key in c or c in master_key:
                        for day, p in MASTER_TIMETABLE[master_key]:
                            if not (day == "금" and p in ["7교시", "8교시"]): 
                                timetable.at[p, day] = master_key
                        break
                            
            draw_styled_dataframe(timetable)
            
            rejected = str(my_res.iloc[0].get('탈락과목', ''))
            if rejected and rejected != 'nan': st.error(f"❌ 탈락(대기): {rejected}")
        else: st.warning("배정 내역이 없습니다.")
    else: st.info("아직 배정이 진행되지 않았습니다.")

# [F] 과목 거래소
elif st.session_state.page == 'trade':
    st.title("🤝 과목 거래소")
    if st.session_state.app_status != "과목거래 오픈": st.warning("🔒 닫혀있습니다."); st.stop()
    st.info("거래소 기능은 생략되었습니다. (이전 코드와 동일하므로 필요시 추가 복사)")

# [G] 관리자 전용 데이터 관리 (오류 1, 3 방어)
elif st.session_state.page == 'admin':
    if st.session_state.user_id != "admin": st.error("🚨 권한 없음"); st.stop()
        
    st.title("⚙️ 관리자 전용 제어")
    sem = st.session_state.selected_semester
    
    if st.button(f"🔥 {sem} 배정 실행", type="primary"):
        suc, msg = run_assignment(sem)
        if suc: st.success(msg) 
        else: st.error(msg)
        
    st.divider()
    st.subheader(f"📂 {sem} 그룹별 최종 명단 추출")
    _, result_file, _ = get_files()
    if os.path.exists(result_file):
        res_df = pd.read_csv(result_file)
        all_data = []
        
        for g_name, subjects in GROUP_MAP.items():
            for sub in subjects:
                if '확정과목' in res_df.columns:
                    matched = res_df[res_df['확정과목'].str.contains(sub, na=False)]
                    for _, r in matched.iterrows():
                        # get()을 사용하여 '학년' 열 누락으로 인한 에러 원천 차단
                        all_data.append([g_name, sub, r.get('학번', ''), r.get('이름', ''), r.get('학년', '미상')])
                        
        sum_df = pd.DataFrame(all_data, columns=["그룹", "과목명", "학번", "이름", "학년"])
        st.dataframe(sum_df)
        csv = sum_df.to_csv(index=False, encoding='utf-8-sig').encode('utf-8-sig')
        st.download_button(f"📥 다운로드", csv, f"KIS_Group_{sem}.csv", "text/csv")

# [F] 과목 거래소
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
    
    if not os.path.exists(trade_file): pd.DataFrame(columns=['요청ID','발신ID','발신자','수신ID','수신자','줄과목','받을과목','상태']).to_csv(trade_file, index=False)
    
    t1, t2 = st.tabs(["전체 현황판", "받은 제안"])
    with t1:
        peer_df = res_df[(res_df['학년'] == my_grade) & (res_df['학번'].astype(str) != my_id)] if '학년' in res_df.columns else res_df[res_df['학번'].astype(str) != my_id]
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
                            req = {'요청ID': str(uuid.uuid4())[:8], '발신ID': my_id, '발신자': st.session_state.user_name, '수신ID': row['학번'], '수신자': row.get('이름', ''), '줄과목': give, '받을과목': want, '상태': '요청중'}
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

