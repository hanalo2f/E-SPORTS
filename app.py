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
    st.info("팀장(대표자)이 팀원 5명의 정보를 모두 작성하여 제출해주세요.")

    # ----------------------------------------------------
    # 0. 성공 메시지 및 폼 초기화 상태 관리 (방법 B 핵심)
    # ----------------------------------------------------
    if "form_version" not in st.session_state:
        st.session_state.form_version = 0

    # 직전에 제출 성공한 기록이 있다면 성공 메시지 표시
    if "success_msg" in st.session_state:
        st.balloons()
        st.success(st.session_state.success_msg)
        del st.session_state.success_msg  # 1회 표시 후 메시지 삭제

    # ----------------------------------------------------
    # 1. 예선 라운드 선택 (st.form 바깥에 배치하여 실시간 반응)
    # ----------------------------------------------------
    st.markdown("##### 🗓️ 참가 희망 예선 라운드 선택 (중복 선택 가능) *")
    rc1, rc2, rc3, rc4 = st.columns(4)

    r1 = rc1.checkbox("1라운드 (10월 7일)", value=True)
    r2 = rc2.checkbox("2라운드 (10월 14일)")
    r3 = rc3.checkbox("3라운드 (10월 21일)")
    r4 = rc4.checkbox("4라운드 (10월 28일)")

    pref_rounds = []
    if r1:
        pref_rounds.append("1라운드 (10월 7일)")
    if r2:
        pref_rounds.append("2라운드 (10월 14일)")
    if r3:
        pref_rounds.append("3라운드 (10월 21일)")
    if r4:
        pref_rounds.append("4라운드 (10월 28일)")

    if pref_rounds:
        st.info(f"📌 **선택한 라운드:** {', '.join(pref_rounds)}")
    else:
        st.warning("⚠️ 최소 1개 이상의 예선 라운드를 선택해 주세요.")

    st.caption("※ 1라운드 탈락 시 2, 3, 4라운드에 재참가가 가능합니다.")
    st.markdown("---")

    # ----------------------------------------------------
    # 2. 신청서 제출 양식 (form_version을 key로 지정)
    # ----------------------------------------------------
    form_key = f"registration_form_{st.session_state.form_version}"
    
    with st.form(form_key, clear_on_submit=False):
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

        # --- 팀장 정보 ---
        st.markdown("---")
        st.markdown("##### 👑 팀장(대표자) 정보")
        lc1, lc2, lc3 = st.columns(3)
        leader_name = lc1.text_input("팀장 성명 *")
        leader_dob = lc2.text_input("팀장 생년월일 *", placeholder="YYMMDD (예: 020101)")
        leader_phone = lc3.text_input("팀장 연락처 *", placeholder="010-0000-0000")

        # --- 주전 팀원 정보 (4명) ---
        st.markdown("---")
        st.markdown("##### 👥 주전 팀원 정보 (4명)")
        members_data = []
        for i in range(1, 5):
            st.caption(f"▪ 팀원 {i}")
            mc1, mc2, mc3 = st.columns(3)
            m_name = mc1.text_input("성명 *", key=f"m_name_{i}_{st.session_state.form_version}")
            m_dob = mc2.text_input("생년월일 *", placeholder="YYMMDD", key=f"m_dob_{i}_{st.session_state.form_version}")
            m_phone = mc3.text_input("연락처 *", placeholder="010-0000-0000", key=f"m_phone_{i}_{st.session_state.form_version}")

            members_data.append({
                "name": m_name,
                "dob": m_dob,
                "phone": m_phone
            })

        # --- 후보 선수 정보 (선택 사항 - 최대 2명) ---
        st.markdown("---")
        st.markdown("##### 🔄 후보 선수 정보 (선택 사항 - 최대 2명)")
        st.caption("※ 대회 당일 참가 불가 인원 발생 시 대체할 후보 선수가 있다면 작성해 주세요. (없을 경우 비워두시면 됩니다.)")
        
        sub_members_str_list = []
        for i in range(1, 3):
            st.caption(f"▪ 후보 선수 {i} (선택)")
            sc1, sc2, sc3 = st.columns(3)
            s_name = sc1.text_input("성명", key=f"s_name_{i}_{st.session_state.form_version}")
            s_dob = sc2.text_input("생년월일", placeholder="YYMMDD", key=f"s_dob_{i}_{st.session_state.form_version}")
            s_phone = sc3.text_input("연락처", placeholder="010-0000-0000", key=f"s_phone_{i}_{st.session_state.form_version}")

            if s_name or s_dob or s_phone:
                sub_members_str_list.append(f"{s_name} ({s_dob}, {s_phone})")
            else:
                sub_members_str_list.append("")

        # --- 개인정보 동의 ---
        st.markdown("---")
        st.markdown("##### 🔒 개인정보 수집·이용 및 제3자 제공 동의")
        st.caption(
            "※ 팀장(신청자)은 본인을 포함한 팀원 및 후보 선수 전원에게 개인정보 수집·이용 및 제3자 제공 동의를 미리 받아서 신청서를 작성해야 합니다."
        )

        agree_collect = st.checkbox(
            "참가자 전원(팀장, 팀원, 후보선수)의 개인정보 수집·이용에 동의합니다. (필수) *"
        )
        agree_third_party = st.checkbox(
            "참가자 전원(팀장, 팀원, 후보선수)의 개인정보 제3자 제공에 동의합니다. (필수) *"
        )

        submitted = st.form_submit_button(
            "참가 신청서 제출하기", use_container_width=True
        )

        if submitted:
            all_members_filled = all(
                m["name"] and m["dob"] and m["phone"] for m in members_data
            )

            # 검증 실패 시: 에러 출력 (입력폼 유지)
            if not (
                team_name
                and leader_name
                and leader_dob
                and leader_phone
                and all_members_filled
                and pref_rounds
            ):
                st.error("필수 항목(*)을 모두 입력해주세요. (예선 라운드 및 팀장/주전 팀원 정보 전체 입력 필요)")
            elif not (agree_collect and agree_third_party):
                st.error("개인정보 수집·이용 동의 및 제3자 제공 동의에 모두 체크하셔야 제출이 가능합니다.")
            else:
                try:
                    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    rounds_str = ", ".join(pref_rounds)

                    leader_info_str = f"{leader_name} ({leader_dob}, {leader_phone})"
                    m_str_list = [
                        f"{m['name']} ({m['dob']}, {m['phone']})" for m in members_data
                    ]

                    row_to_insert = [
                        now_str,
                        game_category,
                        rounds_str,
                        team_name,
                        university,
                        leader_info_str,
                        m_str_list[0],
                        m_str_list[1],
                        m_str_list[2],
                        m_str_list[3],
                        sub_members_str_list[0],
                        sub_members_str_list[1],
                        "동의함",
                    ]

                    # 구글 시트에 전송
                    doc_title, sheet_title = add_registration_to_sheet(row_to_insert)

                    st.cache_data.clear()

                    # 제출 성공 시: 폼 버전을 올려 입력창을 초기화하고 성공 메시지 세팅 후 rerun
                    st.session_state.form_version += 1
                    st.session_state.success_msg = f"🎉 '{team_name}' 팀의 참가 신청이 성공적으로 완료되었습니다!"
                    st.rerun()

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
                correct_password = st.secrets.get("admin_password", "1234")
                
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
