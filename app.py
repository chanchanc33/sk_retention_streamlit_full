
# -*- coding: utf-8 -*-
"""
SK-Branded HR Retention Dashboard (Streamlit, Robust Upload Edition)
- CSV/Excel 업로드를 인코딩/구분자 자동 시도로 안정적 처리
- 컬럼 자동 매핑 + 수동 매핑 UI
- 누락/에러 시 UI에서 안전하게 안내 (앱 크래시 방지)
"""

import io, json, traceback
import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

LOGO_PATH = "assets/sk_group_logo.png"
DEFAULT_THEME = {"name":"SK Group","primary":"#E2231A","secondary":"#F05A22","accent":"#FFB000"}

st.set_page_config(page_title="SK Retention Dashboard", layout="wide", page_icon="🔥")
if "_brand" not in st.session_state: st.session_state["_brand"] = DEFAULT_THEME

def theme(): return st.session_state["_brand"]

# ---------- Helpers ----------
def to_number(v):
    try: return float(str(v).replace(",","").strip())
    except: return None

def fmt_int(n): return "-" if n is None else f"{int(round(n)):,}"
def fmt_float(n,d=2): return "-" if n is None else f"{float(n):.{d}f}"

def find_column(cols, cands):
    low = {c.lower(): c for c in cols}
    # exact
    for c in cands:
        if c.lower() in low: return low[c.lower()]
    # includes
    for c in cands:
        for k,raw in low.items():
            if c.lower() in k: return raw
    return None

def try_read_table_from_bytes(data: bytes, name: str):
    """Try multiple encodings & separators; if needed, try Excel engine."""
    last_err = ""
    # CSV attempts
    encs = ["utf-8", "utf-8-sig", "cp949", "euc-kr", "latin1"]
    seps = [None, ",", ";", "\t", "|"]
    for enc in encs:
        for sep in seps:
            try:
                bio = io.BytesIO(data)
                df = pd.read_csv(bio, encoding=enc, sep=sep, engine="python")
                return df, f"CSV loaded (encoding={enc}, sep={'auto' if sep is None else sep})"
            except Exception as e:
                last_err = f"[csv enc={enc} sep={sep}] {e}"
    # Excel attempts (xlsx/xls)
    try:
        bio = io.BytesIO(data)
        df = pd.read_excel(bio)  # requires openpyxl for xlsx
        return df, "Excel loaded (.xlsx/.xls)"
    except Exception as e:
        last_err = f"[excel] {e}"
    return None, last_err

@st.cache_data(show_spinner=False)
def load_data(uploaded_file):
    """Load uploaded file (CSV/XLSX) or local hr_analysis_results.csv if None."""
    debug = {}
    if uploaded_file is not None:
        raw = uploaded_file.read()
        df, msg = try_read_table_from_bytes(raw, uploaded_file.name)
        debug["source"] = f"uploaded: {uploaded_file.name}"
        debug["load_msg"] = msg
        if df is None:
            st.error("❌ 업로드 파일을 읽을 수 없습니다. CSV(UTF-8 권장) 또는 XLSX로 업로드 해주세요.")
            st.caption(f"마지막 에러: {msg}")
            st.stop()
        return df, debug

    # Fallback: local file
    try:
        with open("hr_analysis_results.csv", "rb") as f:
            raw = f.read()
        df, msg = try_read_table_from_bytes(raw, "hr_analysis_results.csv")
        debug["source"] = "local: hr_analysis_results.csv"
        debug["load_msg"] = msg
        if df is None:
            st.error("로컬 hr_analysis_results.csv 를 읽을 수 없습니다. CSV 또는 XLSX 업로드를 시도하세요.")
            st.caption(f"마지막 에러: {msg}")
            st.stop()
        return df, debug
    except FileNotFoundError:
        st.error("파일이 없습니다. CSV 또는 XLSX 파일을 업로드 해주세요.")
        st.stop()

def auto_guess_map(columns):
    cols = list(columns)
    return {
        "name": find_column(cols, ["성명","이름","name"]) or "없음",
        "org": find_column(cols, ["본부","조직","org"]) or "없음",
        "team": find_column(cols, ["팀","부서","team"]) or "없음",
        "grade": find_column(cols, ["성과등급"]) or "없음",
        "level": find_column(cols, ["직급레벨","레벨","직급"]) or "없음",
        "age": find_column(cols, ["나이"]) or "없음",
        "tenure": find_column(cols, ["근속연수(년)","근속연수"]) or "없음",
        "salary": find_column(cols, ["연봉(원)","연봉","salary"]) or "없음",
        "talent": find_column(cols, ["인재등급"]) or "없음",
        "risk": find_column(cols, ["퇴직위험도","위험도","risk"]) or "없음",
        "riskProb": find_column(cols, ["퇴직위험예측확률","예측확률"]) or "없음",
        "riskReason": find_column(cols, ["위험요인"]) or "없음",
        "phone": find_column(cols, ["휴대폰","전화","phone"]) or "없음",
        "email": find_column(cols, ["이메일","email"]) or "없음",
    }

def apply_numeric(df, mapping, keys=("level","age","tenure","salary","risk","riskProb")):
    for k in keys:
        c = mapping.get(k)
        if c and c != "없음" and c in df.columns:
            df[c] = pd.to_numeric(df[c].astype(str).str.replace(",", "").str.strip(), errors="coerce")

# ---------- UI: Sidebar Upload ----------
with st.sidebar:
    st.markdown("### 📤 데이터 업로드")
    upl = st.file_uploader("CSV 또는 Excel(xlsx) 업로드", type=["csv","xlsx","xls"])

# Load
df, dbg = load_data(upl)
df.columns = [c.strip() for c in df.columns]

# ---------- Header ----------
left, right = st.columns([1,5])
with left:
    try:
        st.image(LOGO_PATH, width=120)
    except Exception:
        st.write("SK")
with right:
    st.markdown(f"""
    <div style="padding:12px 16px;border-radius:16px;background:linear-gradient(90deg,{theme()['primary']}22,{theme()['secondary']}22);border:1px solid {theme()['primary']}33">
      <div style="font-weight:800;color:{theme()['primary']};font-size:24px;line-height:1">실행형 핵심인재 리텐션 대시보드</div>
      <div style="color:#555">CSV/XLSX 업로드 → 컬럼 매핑 → 필터/차트 → 리텐션 패키지</div>
    </div>
    """, unsafe_allow_html=True)

with st.expander("🔧 로딩 정보 / 디버그", expanded=False):
    st.write(dbg)
    st.write("데이터 shape:", df.shape)
    st.dataframe(df.head(10), use_container_width=True)

# ---------- Column Mapping UI ----------
st.subheader("1) 컬럼 매핑 (필수)")
columns = ["없음"] + df.columns.tolist()
if "colmap" not in st.session_state:
    st.session_state["colmap"] = auto_guess_map(df.columns)

colmap = st.session_state["colmap"]
c1, c2, c3 = st.columns(3)
with c1:
    colmap["name"] = st.selectbox("성명 컬럼", columns, index=columns.index(colmap["name"]) if colmap["name"] in columns else 0)
    colmap["org"] = st.selectbox("본부/조직 컬럼", columns, index=columns.index(colmap["org"]) if colmap["org"] in columns else 0)
    colmap["team"] = st.selectbox("팀 컬럼", columns, index=columns.index(colmap["team"]) if colmap["team"] in columns else 0)
with c2:
    colmap["talent"] = st.selectbox("인재등급 컬럼", columns, index=columns.index(colmap["talent"]) if colmap["talent"] in columns else 0)
    colmap["grade"]  = st.selectbox("성과등급 컬럼", columns, index=columns.index(colmap["grade"])  if colmap["grade"]  in columns else 0)
    colmap["level"]  = st.selectbox("직급레벨 컬럼", columns, index=columns.index(colmap["level"])  if colmap["level"]  in columns else 0)
with c3:
    colmap["risk"] = st.selectbox("퇴직위험도 컬럼 (필수)", columns, index=columns.index(colmap["risk"]) if colmap["risk"] in columns else 0)
    colmap["salary"] = st.selectbox("연봉(원) 컬럼", columns, index=columns.index(colmap["salary"]) if colmap["salary"] in columns else 0)
    colmap["riskReason"] = st.selectbox("위험요인 컬럼", columns, index=columns.index(colmap["riskReason"]) if colmap["riskReason"] in columns else 0)

c4, c5 = st.columns(2)
with c4:
    colmap["age"] = st.selectbox("나이 컬럼", columns, index=columns.index(colmap["age"]) if colmap["age"] in columns else 0)
    colmap["tenure"] = st.selectbox("근속연수(년) 컬럼", columns, index=columns.index(colmap["tenure"]) if colmap["tenure"] in columns else 0)
with c5:
    colmap["phone"] = st.selectbox("휴대폰 컬럼", columns, index=columns.index(colmap["phone"]) if colmap["phone"] in columns else 0)
    colmap["email"] = st.selectbox("이메일 컬럼", columns, index=columns.index(colmap["email"]) if colmap["email"] in columns else 0)

# Validate required
required_missing = []
for k in ["name","org","risk"]:
    if colmap[k] == "없음" or colmap[k] not in df.columns:
        required_missing.append(k)

if required_missing:
    st.error("다음 필수 컬럼 매핑이 누락되었습니다: " + ", ".join(required_missing) + " — 매핑을 완료한 뒤 계속하세요.")
    st.stop()

# Apply numeric conversions
apply_numeric(df, colmap)

# ---------- Filters ----------
st.subheader("2) 필터")
c1,c2,c3,c4,c5 = st.columns([2,2,2,2,3])
with c1: search = st.text_input("🔎 검색(성명/본부/팀/인재등급/위험요인)","")
with c2: sel_org = st.multiselect("본부", sorted(df[colmap["org"]].dropna().astype(str).unique().tolist()))
with c3:
    team_col = colmap.get("team")
    sel_team = st.multiselect("팀", sorted(df[team_col].dropna().astype(str).unique().tolist())) if team_col != "없음" and team_col in df.columns else []
with c4:
    grade_col = colmap.get("grade")
    sel_grade = st.multiselect("성과등급", sorted(df[grade_col].dropna().astype(str).unique().tolist())) if grade_col != "없음" and grade_col in df.columns else []
with c5:
    reason_col = colmap.get("riskReason")
    sel_reason = st.multiselect("위험요인", sorted(df[reason_col].dropna().astype(str).unique().tolist())) if reason_col != "없음" and reason_col in df.columns else []

cc1,cc2,cc3,cc4 = st.columns(4)
with cc1:
    level_col = colmap.get("level")
    sel_level = st.multiselect("직급레벨", sorted(df[level_col].dropna().astype(int).astype(str).unique().tolist())) if level_col != "없음" and level_col in df.columns else []
with cc2:
    talent_col = colmap.get("talent")
    sel_talent = st.multiselect("인재등급", sorted(df[talent_col].dropna().astype(str).unique().tolist())) if talent_col != "없음" and talent_col in df.columns else []
with cc3:
    risk_threshold = st.slider("리스크 임계치", 0, 100, 30, 1)
    only_key = st.checkbox("핵심인재만 (Critical/High)", value=True)
with cc4:
    age_col = colmap.get("age")
    age_min, age_max = st.slider("나이 범위", 18, 70, (18, 70)) if age_col != "없음" and age_col in df.columns else (None, None)
    tenure_col = colmap.get("tenure")
    tenure_min, tenure_max = st.slider("근속연수(년) 범위", 0, 40, (0, 40)) if tenure_col != "없음" and tenure_col in df.columns else (None, None)

def passed(row):
    # search (name/org/team/talent/reason)
    if search:
        s = search.lower()
        fields = [colmap["name"], colmap["org"]]
        for k in ["team","talent","riskReason"]:
            ck = colmap.get(k)
            if ck != "없음" and ck in df.columns:
                fields.append(ck)
        if not any(s in str(row.get(f,"")).lower() for f in fields):
            return False
    # categorical filters
    if sel_org and row.get(colmap["org"]) not in sel_org: return False
    if sel_team and colmap["team"] in df.columns and row.get(colmap["team"]) not in sel_team: return False
    if sel_grade and colmap["grade"] in df.columns and row.get(colmap["grade"]) not in sel_grade: return False
    if sel_level and colmap["level"] in df.columns and str(row.get(colmap["level"])) not in sel_level: return False
    if sel_talent and colmap["talent"] in df.columns and row.get(colmap["talent"]) not in sel_talent: return False
    if sel_reason and colmap["riskReason"] in df.columns and row.get(colmap["riskReason"]) not in sel_reason: return False
    # numeric filters
    rv = row.get(colmap["risk"])
    if pd.isna(rv) or float(rv) < risk_threshold: return False
    if only_key and colmap["talent"] in df.columns and row.get(colmap["talent"]) not in ["Critical","High"]: return False
    if age_min is not None and colmap["age"] in df.columns:
        av = row.get(colmap["age"]); 
        if not (age_min <= (av or -1) <= age_max): return False
    if tenure_min is not None and colmap["tenure"] in df.columns:
        tv = row.get(colmap["tenure"]); 
        if not (tenure_min <= (tv or -1) <= tenure_max): return False
    return True

fdf = df[df.apply(passed, axis=1)].copy()
st.caption(f"필터 결과: **{len(fdf):,}명** / 원본 {len(df):,}명")

# ---------- KPI ----------
k1,k2,k3,k4 = st.columns(4)
avg = lambda s: float(s.dropna().mean()) if s.dropna().size>0 else None
with k1: st.metric("대상 인원", f"{len(fdf):,}")
with k2: st.metric("평균 위험도", fmt_float(avg(fdf[colmap["risk"]]),1))
if colmap["tenure"] in df.columns:
    with k3: st.metric("평균 근속(년)", fmt_float(avg(fdf[colmap["tenure"]]),2))
else:
    with k3: st.metric("평균 근속(년)", "-")
if colmap["salary"] in df.columns:
    with k4: st.metric("평균 연봉(원)", fmt_int(avg(fdf[colmap["salary"]])))
else:
    with k4: st.metric("평균 연봉(원)", "-")

st.divider()

# ---------- Charts ----------
c_g1,c_g2,c_g3 = st.columns(3)
with c_g1:
    st.subheader("성과등급 분포")
    if colmap["grade"] in df.columns:
        g = fdf[colmap["grade"]].value_counts().reset_index()
        g.columns = ["성과등급","인원"]
        if not g.empty:
            st.plotly_chart(px.bar(g, x="성과등급", y="인원", color_discrete_sequence=[theme()["secondary"]]), use_container_width=True)
        else: st.info("데이터 없음")
    else:
        st.info("성과등급 컬럼이 매핑되지 않았습니다.")

with c_g2:
    st.subheader("직급레벨 분포")
    if colmap["level"] in df.columns:
        lv = fdf[colmap["level"]].dropna().astype(int).astype(str)
        gv = lv.value_counts().sort_index().reset_index()
        gv.columns = ["직급레벨","인원"]
        if not gv.empty:
            st.plotly_chart(px.bar(gv, x="직급레벨", y="인원", color_discrete_sequence=[theme()["accent"]]), use_container_width=True)
        else: st.info("데이터 없음")
    else:
        st.info("직급레벨 컬럼이 매핑되지 않았습니다.")

with c_g3:
    st.subheader("퇴직위험도 구간")
    rb = pd.cut(fdf[colmap["risk"]], [0,30,50,70,100], right=False, labels=["0-29","30-49","50-69","70+"])
    bc = rb.value_counts().reindex(["0-29","30-49","50-69","70+"]).fillna(0).reset_index()
    bc.columns = ["구간","인원"]
    fig = px.pie(bc, values="인원", names="구간", color="구간",
                 color_discrete_map={"0-29":"#10b981","30-49":theme()["accent"],"50-69":theme()["secondary"],"70+":theme()["primary"]})
    st.plotly_chart(fig, use_container_width=True)

st.divider()

# ---------- Priority list ----------
st.subheader("우선순위 대응 리스트")
rank = {"Critical":4,"High":3,"Standard":2,"Development":1}
if colmap["talent"] in df.columns:
    fdf["_rankTalent"] = fdf[colmap["talent"]].map(rank).fillna(0)
else:
    fdf["_rankTalent"] = 0
sort_keys = [colmap["risk"], "_rankTalent"]
if colmap["salary"] in df.columns: sort_keys.append(colmap["salary"])
sorted_df = fdf.sort_values(sort_keys, ascending=[False, False, False][:len(sort_keys)])
cols_show = [colmap["name"], colmap["org"], colmap.get("talent"), colmap.get("level"), colmap.get("salary"), colmap["risk"], colmap.get("riskReason")]
cols_show = [c for c in cols_show if c and c != "없음" and c in df.columns]
top = sorted_df[cols_show].head(200).copy()
# Rename columns to Korean display if matched
rename_map = {}
for k,label in [("name","성명"),("org","본부"),("talent","인재등급"),("level","직급레벨"),("salary","연봉(원)"),("risk","퇴직위험도"),("riskReason","위험요인")]:
    c = colmap.get(k)
    if c in top.columns: rename_map[c] = label
top = top.rename(columns=rename_map)
st.dataframe(top, use_container_width=True, height=360)

# ---------- Per-employee package ----------
st.subheader("직원별 리텐션 패키지 생성")
names = sorted_df[colmap["name"]].astype(str).unique().tolist()
sel = st.selectbox("직원 선택", ["선택하세요"] + names)

def calc_roi(s, kr=0.3, kt=0.2, kp=0.5):
    s = to_number(s) or 0
    return {"total": s*(kr+kt+kp), "recruit": s*kr, "training": s*kt, "lost": s*kp}

def gen_pkg(risk, salary):
    level = "critical" if (risk or 0) >= 70 else "high" if (risk or 0) >= 50 else "medium" if (risk or 0) >= 30 else "low"
    budgets = {"critical":0.25,"high":0.15,"medium":0.08,"low":0.04}
    timelines = {"critical":"48시간 내","high":"1주일 내","medium":"2주 내","low":"1개월 내"}
    base = [
        {"action":"팀장 정기 1:1 설정","person":"팀장","deadline":"1주"},
        {"action":"근무환경 만족도 조사","person":"HR팀","deadline":"1주"},
    ]
    if level in ["critical","high"]:
        immediate = [
            {"action":"CEO/임원진 긴급 면담","person":"CEO","deadline":"24~48시간"},
            {"action":"특별 보상 인상 검토","person":"CHO","deadline":"48시간"},
            {"action":"프로젝트/팀 재배치","person":"부서장","deadline":"1주"},
        ]
    else:
        immediate = base
    follow = [{"action":"전담 멘토/성장 로드맵","person":"CHO/HR","deadline":"2주"}] if level=="critical" else [{"action":"외부 교육/세미나","person":"HR팀","deadline":"2주"}]
    return {
        "title": "🚨 긴급 리텐션 패키지" if level=="critical" else "⚠️ 집중 관리 패키지" if level=="high" else "🎯 예방적 관리 패키지" if level=="medium" else "🙂 정기 케어 패키지",
        "budget": round((to_number(salary) or 0)*budgets[level]/10000),
        "timeline": timelines[level], "immediate": immediate, "follow": follow, "level": level
    }

if sel != "선택하세요":
    r = sorted_df[sorted_df[colmap["name"]].astype(str)==sel].iloc[0]
    risk_val = r.get(colmap["risk"])
    salary_val = r.get(colmap["salary"]) if colmap["salary"] in df.columns else 0
    pkg = gen_pkg(risk_val, salary_val); roi = calc_roi(salary_val)

    left2, right2 = st.columns(2)
    with left2:
        st.markdown(f"""
        <div style="padding:16px;border-radius:16px;background:#fff5f5;border:1px solid {theme()['primary']}33">
          <div style="font-weight:700;color:{theme()['primary']}">{pkg['title']}</div>
          <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-top:8px">
            <div><div style="color:{theme()['secondary']}">예산</div><div style="font-weight:700">{pkg['budget']:,}만원</div></div>
            <div><div style="color:{theme()['secondary']}">기한</div><div style="font-weight:700">{pkg['timeline']}</div></div>
            <div><div style="color:{theme()['secondary']}">손실 방지</div><div style="font-weight:700">{int(roi['total']/10000):,}만원</div></div>
          </div>
        </div>
        """, unsafe_allow_html=True)
    with right2:
        st.write("**즉시 연락**")
        cA, cB = st.columns(2)
        if colmap["email"] in df.columns:
            cA.link_button("📧 이메일", f"mailto:{r.get(colmap['email'],'')}?subject={sel}%20면담%20요청", use_container_width=True)
        if colmap["phone"] in df.columns:
            cB.link_button("📞 전화", f"tel:{r.get(colmap['phone'],'')}", use_container_width=True)

    st.write("**실행 체크리스트**")
    done_im, done_f = [], []
    for i,a in enumerate(pkg["immediate"]):
        if st.checkbox(f"{a['action']} (담당:{a['person']}, 기한:{a['deadline']})", key=f"im_{i}"):
            done_im.append(a)
    for i,a in enumerate(pkg["follow"]):
        if st.checkbox(f"{a['action']} (담당:{a['person']}, 기한:{a['deadline']})", key=f"fu_{i}"):
            done_f.append(a)

    report = {
        "employee": sel,
        "org": r.get(colmap["org"]),
        "talent": r.get(colmap["talent"]) if colmap["talent"] in df.columns else None,
        "risk": risk_val,
        "budget(만원)": pkg["budget"],
        "expected_loss_saved(만원)": int(roi["total"]/10000),
        "completed_immediate":[a["action"] for a in done_im],
        "completed_follow":[a["action"] for a in done_f],
    }
    st.download_button("리텐션 리포트 JSON 다운로드", data=json.dumps(report, ensure_ascii=False, indent=2), file_name=f"retention_report_{sel}.json", mime="application/json")

st.divider()

# ---------- Export filtered data ----------
if not fdf.empty:
    buff = io.StringIO(); fdf.to_csv(buff, index=False, encoding="utf-8-sig")
    st.download_button("필터된 데이터 CSV 다운로드", data=buff.getvalue(), file_name="filtered_hr_data.csv", mime="text/csv")

st.caption("© SK Retention Dashboard — Streamlit Free Edition")
