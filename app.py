import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# 1. 페이지 기본 설정
st.set_page_config(
    page_title="제천시(중부권) 대학생 e스포츠 리그전",
    page_icon="🎮",
    layout="wide"
)

# 2. SQLite 데이터베이스 초기화
DB_FILE = "esports_league.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS registrations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT,
            game_category TEXT,
            team_name TEXT,
            university TEXT,
            leader_name TEXT,
            leader_phone TEXT,
            leader_major TEXT,
            leader_game_id TEXT,
            member1_info TEXT,
            member2_info TEXT,
            member3_info TEXT,
            member4_info TEXT
        )
    ''')
    conn.commit()
    conn.close()

def insert_registration(data):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('''
        INSERT INTO registrations (
            created_at, game_category, team_name, university,
            leader_name, leader_phone, leader_major, leader_game_id,
            member1_info, member2_info, member3_info, member4_info
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', data)
    conn.commit()
    conn.close()

def get_registrations():
    conn = sqlite3.connect(DB_FILE)
    df = pd.read_sql_query("SELECT * FROM registrations ORDER BY id DESC", conn)
    conn.close()
    return df

# DB 초기화 실행
init_db()

# 3. 헤더 영역
st.title("🏆 제천시(중부권) 대학생 e스포츠 리그전")
st.caption("주최/주관: 제천시 e스포츠협회 | 문의: 010-5820-7145 (anjinmo@hanmail.net)")
st.markdown("---")

# 4. 대회 개요 요약 카드
col_info1, col_info2, col_info3, col_info4 = st.columns(4)
with col_info1:
    st.metric(label="📅 모집 기간", value="2026.09. ~ 09.30")
with col_info2:
    st.metric(label="🎮 종목 (5인 1팀)", value="발로란트 / LoL")
with col_info3:
    st.metric(label="🥇 종목별 1위 상금", value="1,000,000원")
with col_info4:
    st.metric(label="🎓 참가 대상", value="세명대/대원대/중부권 대학생")

st.markdown("<br>", unsafe_allow_html=True)

# 5. 탭 구성
tab1, tab2 = st.tabs(["📝 참가 신청서 작성", "📊 신청 현황 대시보드 (관리자)"])

# ==================== TAB 1: 참가 신청서 ====================
with tab1:
    st.subheader("대회 참가 신청서")
    st.info("💡 팀 대표자(팀장)가 팀원 5명의 정보를 모두 확인 후 작성해 주세요.")

    with st.form(key="apply_form", clear_on_submit=True):
        st.markdown("### 1. 기본 정보")
        c1, c2, c3 = st.columns(3)
        with c1:
            game_category = st.selectbox("참가 종목 *", ["발로란트 (5인 1팀)", "리그 오브 레전드 (5인 1팀)"])
        with c2:
            team_name = st.text_input("팀명 *", placeholder="팀명을 입력하세요")
        with c3:
            university = st.selectbox("소속 대학교 *", ["세명대학교", "대원대학교", "기타 제천인근 대학교"])

        st.markdown("---")
        st.markdown("### 2. 팀장(대표자) 정보")
        l1, l2 = st.columns(2)
        with l1:
            leader_name = st.text_input("팀장 이름 *")
            leader_phone = st.text_input("팀장 연락처 *", placeholder="010-0000-0000")
        with l2:
            leader_major = st.text_input("팀장 학과/학번 *", placeholder="예: 컴퓨터공학과 / 20230001")
            leader_game_id = st.text_input("팀장 게임 ID (#태그 포함) *", placeholder="예: Hide on bush#KR1")

        st.markdown("---")
        st.markdown("### 3. 팀원 정보 (4명)")
        
        members_data = []
        for i in range(1, 5):
            st.markdown(f"**팀원 {i}**")
            m1, m2, m3 = st.columns(3)
            with m1:
                m_name = st.text_input(f"팀원 {i} 이름 *", key=f"m_name_{i}")
            with m2:
                m_major = st.text_input(f"팀원 {i} 학과/학번 *", key=f"m_major_{i}")
            with m3:
                m_gid = st.text_input(f"팀원 {i} 게임 ID (#태그 포함) *", key=f"m_gid_{i}")
            
            members_data.append(f"{m_name} | {m_major} | {m_gid}")

        submit_button = st.form_submit_button(label="🚀 참가 신청서 제출하기", use_container_width=True)

        if submit_button:
            # 필수값 검증
            if not team_name or not leader_name or not leader_phone or not leader_game_id:
                st.error("⚠️ 필수 항목(*표시)을 모두 입력해 주세요.")
            else:
                created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                record = (
                    created_at, game_category, team_name, university,
                    leader_name, leader_phone, leader_major, leader_game_id,
                    members_data[0], members_data[1], members_data[2], members_data[3]
                )
                insert_registration(record)
                st.balloons()
                st.success(f"🎉 **[{team_name}]** 팀의 참가 신청이 성공적으로 완료되었습니다!")

# ==================== TAB 2: 대시보드 ====================
with tab2:
    st.subheader("실시간 참가 신청 현황")

    df = get_registrations()

    # 현황 요약 지표
    total_count = len(df)
    val_count = len(df[df['game_category'].str.contains('발로란트', na=False)]) if total_count > 0 else 0
    lol_count = len(df[df['game_category'].str.contains('리그 오브 레전드', na=False)]) if total_count > 0 else 0

    m1, m2, m3 = st.columns(3)
    m1.metric(label="총 접수 팀", value=f"{total_count} 팀")
    m2.metric(label="발로란트", value=f"{val_count} 팀")
    m3.metric(label="리그 오브 레전드", value=f"{lol_count} 팀")

    st.markdown("---")

    if total_count > 0:
        # 데이터 검색 및 필터
        search_term = st.text_input("🔍 팀명 또는 팀장명 검색", "")
        if search_term:
            df_filtered = df[df['team_name'].str.contains(search_term, na=False) | df['leader_name'].str.contains(search_term, na=False)]
        else:
            df_filtered = df

        # 테이블 표시
        st.dataframe(
            df_filtered,
            column_config={
                "id": "ID",
                "created_at": "신청일시",
                "game_category": "종목",
                "team_name": "팀명",
                "university": "대학교",
                "leader_name": "팀장명",
                "leader_phone": "연락처",
                "leader_major": "학과/학번",
                "leader_game_id": "팀장 게임 ID",
                "member1_info": "팀원 1",
                "member2_info": "팀원 2",
                "member3_info": "팀원 3",
                "member4_info": "팀원 4",
            },
            use_container_width=True,
            hide_index=True
        )

        # CSV 내보내기 버튼
        csv = df.to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            label="📥 엑셀(CSV) 데이터 다운로드",
            data=csv,
            file_name=f"제천시_e스포츠리그전_참가자명단_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv",
        )
    else:
        st.info("현재 접수된 참가 팀이 없습니다.")