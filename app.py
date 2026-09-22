from datetime import datetime
from google.oauth2.service_account import Credentials
import gspread
import pandas as pd
import streamlit as st

# 페이지 기본 설정
st.set_page_config(
    page_title="제천시(중부권) 대학생 e스포츠 리그전",
    page_icon="🎮",
    layout="wide",
)


# -------------------------------------------------------------------
# 1. 구글 시트 연동 설정
# -------------------------------------------------------------------
@st.cache_resource
def get_gsheet_client():
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]

    service_account_info = dict(st.secrets["gcp_service_account"])
    if "private_key" in service_account_info:
        service_account_info["private_key"] = service_account_info[
            "private_key"
        ].replace("\\n", "\n")

    credentials = Credentials.from_service_account_info(
        service_account_info, scopes=scopes
    )
    return gspread.authorize(credentials)


def get_spreadsheet():
    client = get_gsheet_client()
    return client.open_by_url(st.secrets["private_gsheet_url"])


def get_worksheet():
    sheet = get_spreadsheet()
    return sheet, sheet.sheet1


def add_registration_to_sheet(row_data):
    """구글 시트에 새로운 행 추가"""
    spreadsheet, worksheet = get_worksheet()
    worksheet.append_row(row_data, value_input_option="USER_ENTERED")
    return spreadsheet.title, worksheet.title


@st.cache_data(ttl=60)
def load_data_from_sheet():
    """구글 시트의 전체 데이터 읽어오기"""
    _, worksheet = get_worksheet()
    records = worksheet.get_all_records()
    return pd.DataFrame(records)


# -------------------------------------------------------------------
# 2. UI 레이아웃
# -------------------------------------------------------------------
st.title("🏆 제천시(중부권) 대학생 e스포츠 리그전")
st.markdown(
    "**주최/주관:** 제천시 e스포츠협회 | **문의:** 010-5820-7145"
)

tab1, tab2 = st.tabs(["📝 참가 신청하기", "📊 신청 현황 대시보드"])

# [TAB 1] 참가 신청서
with tab1:
    st.subheader("대회 참가 신청서 (5인 1팀)")
    st.info(
        "팀장(대표자)이 팀원 5명의 정보를 모두 작성하여 제출해주세요."
    )

    with st.form("registration_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            game_category = st.selectbox(
                "참가 종목 *", ["발로란트", "리그 오브 레전드"]
            )
        with col2:
            team_name = st.text_input("팀명 *")
        with col3:
            university = st.selectbox(
                "소속 대학교 *",
                ["세명대학교", "대원대학교", "기타 제천인근 대학교"],
            )

        st.markdown("---")
        st.markdown("##### 👑 팀장(대표자) 정보")
        c1, c2, c3, c4 = st.columns(4)
        leader_name = c1.text_input("팀장 이름 *")
        leader_phone = c2.text_input(
            "팀장 연락처 *", placeholder="010-0000-0000"
        )
        leader_major = c3.text_input(
            "학과 / 학번 *", placeholder="컴퓨터공학과 / 20230001"
        )
        leader_game_id = c4.text_input(
            "게임 라이엇 ID (#태그 포함) *",
            placeholder="Hide on bush#KR1",
        )

        st.markdown("---")
        st.markdown("##### 👥 팀원 정보 (4명)")
        members = []
        for i in range(1, 5):
            mc1, mc2, mc3 = st.columns(3)
            m_name = mc1.text_input(f"팀원 {i} 이름 *", key=f"m_name_{i}")
            m_major = mc2.text_input(
                f"팀원 {i} 학과/학번 *", key=f"m_major_{i}"
            )
            m_id = mc3.text_input(
                f"팀원 {i} 게임 ID (#태그) *", key=f"m_id_{i}"
            )
            
            # 이름, 학과/학번, 게임ID 3가지를 보기 좋게 합쳐서 저장
            if m_name or m_major or m_id:
                members.append(f"{m_name} ({m_major}, {m_id})")
            else:
                members.append("")

        submitted = st.form_submit_button(
            "참가 신청서 제출하기", use_container_width=True
        )

        if submitted:
            if not (
                team_name
                and leader_name
                and leader_phone
                and leader_game_id
            ):
                st.error("필수 항목(*)을 모두 입력해주세요.")
            else:
                try:
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    row_to_insert = [
                        now_str,
                        game_category,
                        team_name,
                        university,
                        leader_name,
                        leader_phone,
                        leader_major,
                        leader_game_id,
                        members[0],
                        members[1],
                        members[2],
                        members[3],
                    ]

                    # 구글 시트에 데이터 전송
                    doc_title, sheet_title = add_registration_to_sheet(
                        row_to_insert
                    )

                    # 대시보드 즉시 갱신용 캐시 비우기
                    st.cache_data.clear()

                    st.balloons()
                    st.success(
                        f"🎉 '{team_name}' 팀의 참가 신청이 성공적으로 완료되었습니다!"
                    )
                except Exception as e:
                    st.error(f"저장 중 오류가 발생했습니다: {e}")

# [TAB 2] 대시보드 (관리자 전용)
with tab2:
    # 관리자 인증 세션 상태 초기화
    if "admin_authenticated" not in st.session_state:
        st.session_state.admin_authenticated = False

    # 1. 미인증 상태: 비밀번호 입력폼 표시
    if not st.session_state.admin_authenticated:
        st.subheader("🔒 관리자 전용 페이지")
        st.info("신청 현황 대시보드는 관리자만 접근 가능합니다. 비밀번호를 입력해주세요.")
        
        with st.form("admin_login_form"):
            password_input = st.text_input("관리자 비밀번호", type="password")
            login_submitted = st.form_submit_button("로그인", use_container_width=True)
            
            if login_submitted:
                # secrets.toml의 admin_password 항목 확인 (없을 경우 기본값 지정 가능)
                correct_password = st.secrets.get("admin_password", "2021")
                
                if password_input == correct_password:
                    st.session_state.admin_authenticated = True
                    st.success("로그인에 성공했습니다.")
                    st.rerun()  # 화면 즉시 갱신
                else:
                    st.error("비밀번호가 올바르지 않습니다.")

    # 2. 인증 완료 상태: 대시보드 출력
    else:
        top_col1, top_col2 = st.columns([8, 2])
        with top_col1:
            st.subheader("📊 실시간 참가 신청 현황 (관리자)")
        with top_col2:
            if st.button("🚪 로그아웃", use_container_width=True):
                st.session_state.admin_authenticated = False
                st.rerun()

        st.markdown("---")

        if st.button("🔄 데이터 새로고침"):
            st.cache_data.clear()

        try:
            df = load_data_from_sheet()

            if df.empty:
                st.warning("현재 접수된 참가 팀이 없습니다.")
            else:
                m1, m2, m3 = st.columns(3)
                m1.metric("총 참가 팀", f"{len(df)} 팀")

                if "종목" in df.columns:
                    m2.metric(
                        "발로란트",
                        f"{len(df[df['종목'] == '발로란트'])} 팀",
                    )
                    m3.metric(
                        "리그 오브 레전드",
                        f"{len(df[df['종목'] == '리그 오브 레전드'])} 팀",
                    )

                st.markdown("---")
                st.dataframe(df, use_container_width=True)

                csv_data = df.to_csv(index=False).encode("utf-8-sig")
                st.download_button(
                    label="📥 엑셀(CSV) 명단 다운로드",
                    data=csv_data,
                    file_name=f"제천시_e스포츠리그전_참가명단_{datetime.now().strftime('%Y%m%d')}.csv",
                    mime="text/csv",
                )
        except Exception as e:
            st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
