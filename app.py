# -*- coding: utf-8 -*-
"""
CAREER NAVIGATOR | 고등학생 AI 진로 탐색
실행: streamlit run app.py

Streamlit Community Cloud > App > Settings > Secrets에 아래 값 등록:
CAREER_NET_API_KEY = "커리어넷에서 발급받은 인증키"
OPENAI_API_KEY = "선택 사항: AI 설명 생성에 사용할 OpenAI API 키"
APP_URL = "https://your-app-name.streamlit.app"

커리어넷 API 키가 없어도 데모 직업 데이터로 앱을 실행할 수 있습니다.
"""

from __future__ import annotations

import os
import re
import json
from io import BytesIO
from typing import Any

import requests
import streamlit as st

try:
    import qrcode
except ImportError:
    qrcode = None

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None


# ---------------------------------------------------------------------
# 페이지 설정 및 스타일
# ---------------------------------------------------------------------
st.set_page_config(
    page_title="NEXUS | AI Career Lab",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Pretendard:wght@400;500;600;700;800&display=swap');
    :root { color-scheme: light; }
    html, body, [class*="css"] { font-family:'Pretendard',sans-serif; }
    [data-testid="stAppViewContainer"] {
      background:
        radial-gradient(ellipse at 12% 0%, rgba(105,139,255,.15), transparent 34%),
        radial-gradient(ellipse at 95% 18%, rgba(80,216,207,.10), transparent 28%),
        #f5f7fc;
    }
    [data-testid="stHeader"] { background:transparent; }
    [data-testid="stSidebar"] { display:none; }
    .block-container { max-width:1200px; padding:1.05rem 1.4rem 1rem; }
    .brand { color:#566bd7; font-size:.76rem; font-weight:800; letter-spacing:.19em; }
    .hero {
      position:relative; overflow:hidden; border-radius:25px; padding:1.65rem 1.8rem;
      color:#fff; background:linear-gradient(115deg,#101a3b 0%,#243b79 55%,#4566d7 100%);
      box-shadow:0 18px 45px rgba(35,57,120,.18); margin:.65rem 0 1.1rem;
    }
    .hero:after {
      content:"✦"; position:absolute; right:5%; top:-42px; font-size:12rem;
      color:rgba(255,255,255,.07); transform:rotate(12deg);
    }
    .hero h1 { color:#fff; font-size:2.2rem; line-height:1.18; margin:.45rem 0 .55rem; letter-spacing:-.055em; }
    .hero p { color:#dce5ff; margin:0; font-size:.98rem; }
    .eyebrow { font-size:.72rem; letter-spacing:.18em; color:#a9bbff; font-weight:800; }
    .step { display:inline-block; padding:.34rem .75rem; border-radius:99px; background:#e8edff; color:#4058c4; font-size:.76rem; font-weight:800; margin:.45rem 0 .35rem; }
    .subtle { color:#71809c; font-size:.88rem; }
    .panel {
      background:rgba(255,255,255,.92); border:1px solid #e4e9f4; border-radius:19px;
      padding:1rem 1.1rem; box-shadow:0 7px 24px rgba(28,45,90,.045);
    }
    .panel h4 { color:#1d2b55; margin:0 0 .4rem; font-size:1rem; }
    .panel p { color:#65728b; margin:0; font-size:.88rem; line-height:1.48; }
    .metric { color:#263d91; font-size:1.45rem; font-weight:800; }
    .job-card {
      background:#fff; border:1px solid #e3e9f5; border-radius:17px; padding:1rem;
      min-height:145px; box-shadow:0 5px 18px rgba(30,48,90,.04);
    }
    .job-card h3 { color:#20336f; font-size:1.08rem; margin:.1rem 0 .4rem; }
    .tag { display:inline-block; border-radius:99px; background:#edf1ff; color:#5268c8; padding:.22rem .55rem; font-size:.72rem; font-weight:700; margin:0 .2rem .25rem 0; }
    .source { font-size:.75rem; color:#8793a8; }
    .path { color:#697897; font-size:.82rem; font-weight:600; margin:.2rem 0 .7rem; }
    .footer { text-align:center; color:#98a2b5; font-size:.72rem; padding:.65rem 0 0; }
    div.stButton > button, div.stDownloadButton > button {
      width:100%; min-height:2.85rem; border-radius:13px; font-weight:700;
      border:1px solid #dfe6f4; color:#263b80; background:#fff;
    }
    div.stButton > button:hover, div.stDownloadButton > button:hover {
      border-color:#667fe0; color:#354fb6; background:#f7f8ff;
    }
    div.stButton > button[kind="primary"] {
      background:linear-gradient(100deg,#344fbd,#5573e2); color:#fff; border:0;
    }
    div.stButton > button[kind="primary"]:hover { color:#fff; filter:brightness(1.05); }
    div[data-testid="stProgress"] > div > div { background:#526cda; }
    div[data-testid="stRadio"] label { padding:.15rem 0; }
    a { color:#405ecb !important; font-weight:650; }
    @media(max-width:700px) {
      .block-container { padding:.65rem .75rem .8rem; }
      .hero { padding:1.2rem 1.05rem; border-radius:19px; }
      .hero h1 { font-size:1.65rem; }
      .panel { padding:.8rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ---------------------------------------------------------------------
# 설정 / 데이터
# ---------------------------------------------------------------------
CAREER_NET_BASE = "https://www.career.go.kr/cnet/front/openapi"
CAREER_NET_HOME = "https://www.career.go.kr/"
CAREER_NET_JOB_SEARCH = "https://www.career.go.kr/cnet/front/base/job/jobView.do"
CAREER_NET_DEPT = "https://www.career.go.kr/cnet/front/base/major/FunivMajorView.do"

AREAS = {
    "인문·언어": ["언어", "문학", "역사", "철학", "문화", "번역"],
    "사회·경영": ["경영", "경제", "마케팅", "정책", "사회", "금융"],
    "교육·심리": ["교육", "교사", "심리", "상담", "교육공학"],
    "자연·생명": ["생명", "화학", "물리", "환경", "생태", "연구"],
    "공학·IT": ["인공지능", "소프트웨어", "데이터", "컴퓨터", "로봇", "반도체", "기계"],
    "의약·보건": ["의사", "간호", "의료", "약학", "바이오", "보건"],
    "예술·콘텐츠": ["디자인", "영상", "게임", "음악", "미술", "콘텐츠"],
    "융합·미래": ["에너지", "기후", "우주", "스마트", "콘텐츠", "AI"],
}
SUBJECTS = ["국어", "영어", "수학", "과학", "사회", "정보", "미술", "음악", "체육", "기술·가정"]
STRENGTHS = ["논리적 사고", "창의적 아이디어", "자료 분석", "의사소통", "공감·배려", "문제 해결", "관찰·탐구", "기획·조직", "손으로 만들기", "디지털 활용"]
WORK_STYLES = ["혼자 깊이 탐구하기", "팀으로 협업하기", "사람을 직접 돕기", "새로운 것을 기획·창작하기", "실험·제작·실습하기", "데이터와 정보를 분석하기"]

# API가 설정되지 않았거나 검색 결과가 없을 때만 쓰는 데모 자료
DEMO_JOBS = [
    {"name":"인공지능 전문가","summary":"데이터와 알고리즘을 활용해 인공지능 모델과 서비스를 연구·개발합니다.","work":"문제에 적합한 데이터를 수집·정리하고 알고리즘을 설계·학습·평가합니다.","field":"공학·IT","keywords":["인공지능","수학","정보","자료 분석","논리적 사고","문제 해결"],"major":"컴퓨터공학과, 인공지능학과, 데이터사이언스학과","related":"데이터 분석가, 머신러닝 엔지니어"},
    {"name":"데이터 분석가","summary":"데이터에서 패턴과 의미를 찾아 의사결정에 필요한 정보를 제공합니다.","work":"데이터를 수집·정제하고 통계·시각화 기법으로 분석 결과를 전달합니다.","field":"공학·IT","keywords":["데이터","수학","사회","자료 분석","논리적 사고"],"major":"통계학과, 데이터사이언스학과, 산업공학과","related":"데이터 과학자, 비즈니스 분석가"},
    {"name":"소프트웨어 개발자","summary":"사용자의 요구를 분석해 프로그램과 디지털 서비스를 개발합니다.","work":"요구사항 분석, 설계, 코딩, 테스트와 유지보수를 수행합니다.","field":"공학·IT","keywords":["소프트웨어","정보","수학","문제 해결","디지털 활용"],"major":"컴퓨터공학과, 소프트웨어학과","related":"앱 개발자, 웹 개발자"},
    {"name":"로봇공학자","summary":"로봇의 구조와 움직임, 센서 및 제어 기술을 연구합니다.","work":"기계·전자·소프트웨어 기술을 융합해 로봇을 설계하고 시험합니다.","field":"공학·IT","keywords":["로봇","과학","수학","기술·가정","손으로 만들기","실험·제작·실습하기"],"major":"기계공학과, 로봇공학과, 전자공학과","related":"자동화 엔지니어, 제어계측 엔지니어"},
    {"name":"반도체 엔지니어","summary":"반도체 소자와 회로, 제조 공정의 성능과 품질을 개선합니다.","work":"반도체 설계·공정·장비·소재를 연구하고 문제를 분석합니다.","field":"공학·IT","keywords":["반도체","물리","수학","과학","자료 분석"],"major":"전자공학과, 반도체공학과, 재료공학과","related":"전자회로 엔지니어, 공정 엔지니어"},
    {"name":"생명과학 연구원","summary":"생명 현상을 관찰하고 실험을 통해 생명체의 원리를 연구합니다.","work":"실험을 설계하고 생물학적 자료를 분석해 연구 결과를 정리합니다.","field":"자연·생명","keywords":["생명","과학","관찰·탐구","자료 분석"],"major":"생명과학과, 생명공학과, 생화학과","related":"생명공학 연구원, 유전공학 연구원"},
    {"name":"환경 연구원","summary":"환경오염과 생태계 변화를 조사하고 지속가능한 해결책을 연구합니다.","work":"환경 자료를 조사·측정하고 환경 영향 및 개선 방안을 분석합니다.","field":"자연·생명","keywords":["환경","생태","과학","사회","관찰·탐구"],"major":"환경공학과, 환경학과, 지구환경과학과","related":"환경공학 기술자, 생태 연구원"},
    {"name":"의사","summary":"환자의 건강 상태를 평가하고 질병의 진단·치료·예방을 수행합니다.","work":"문진과 검사 결과를 종합해 진단하고 치료 계획을 세웁니다.","field":"의약·보건","keywords":["의료","생명","과학","공감·배려","문제 해결"],"major":"의예과·의학과","related":"의학 연구원, 공중보건 전문가"},
    {"name":"간호사","summary":"환자 상태를 관찰하고 치료와 회복, 건강 관리를 지원합니다.","work":"간호 사정과 간호 수행, 환자·보호자 교육 및 의료진 협업을 합니다.","field":"의약·보건","keywords":["간호","의료","생명","공감·배려","의사소통"],"major":"간호학과","related":"전문간호사, 보건교육 전문가"},
    {"name":"약사","summary":"의약품의 안전하고 효과적인 사용을 돕고 복약 지도를 수행합니다.","work":"처방을 검토하고 약의 효능·주의사항을 확인해 환자에게 안내합니다.","field":"의약·보건","keywords":["약학","화학","생명","꼼꼼함","의사소통"],"major":"약학과","related":"임상약사, 제약 연구원"},
    {"name":"심리상담 전문가","summary":"개인의 정서와 행동, 관계의 어려움을 이해하고 상담을 지원합니다.","work":"상담 목표를 세우고 대화와 심리평가를 통해 변화 과정을 돕습니다.","field":"교육·심리","keywords":["심리","사회","공감·배려","의사소통"],"major":"심리학과, 상담심리학과","related":"청소년상담사, 임상심리 전문가"},
    {"name":"교사","summary":"교과 지식과 학습 방법을 바탕으로 학생의 배움과 성장을 돕습니다.","work":"수업을 설계·운영하고 학습을 평가하며 학생을 지도합니다.","field":"교육·심리","keywords":["교육","국어","수학","과학","의사소통","공감·배려"],"major":"사범대학 관련 학과, 교육대학","related":"교육 연구원, 교육콘텐츠 개발자"},
    {"name":"마케팅 기획자","summary":"고객과 시장을 분석해 제품·서비스의 소통 전략을 기획합니다.","work":"시장 조사, 고객 분석, 캠페인 기획과 성과 분석을 수행합니다.","field":"사회·경영","keywords":["마케팅","경영","사회","창의적 아이디어","자료 분석","기획·조직"],"major":"경영학과, 광고홍보학과, 미디어커뮤니케이션학과","related":"브랜드 매니저, 시장조사 전문가"},
    {"name":"경제 연구원","summary":"경제 현상과 정책, 시장 자료를 분석해 경제 흐름을 연구합니다.","work":"경제 지표를 분석하고 연구 보고서와 정책 제안을 작성합니다.","field":"사회·경영","keywords":["경제","수학","사회","자료 분석","논리적 사고"],"major":"경제학과, 통계학과","related":"금융 분석가, 정책 연구원"},
    {"name":"UX/UI 디자이너","summary":"사용자가 디지털 제품을 쉽고 편리하게 이용하도록 경험과 화면을 설계합니다.","work":"사용자 조사, 정보 구조 설계, 화면 디자인과 사용성 검증을 합니다.","field":"예술·콘텐츠","keywords":["디자인","미술","정보","창의적 아이디어","공감·배려"],"major":"시각디자인학과, 산업디자인학과, HCI 관련 전공","related":"서비스 기획자, 프로덕트 디자이너"},
    {"name":"영상 콘텐츠 기획자","summary":"영상 콘텐츠의 주제와 구성, 제작 방향을 기획합니다.","work":"자료 조사, 스토리 구성, 제작진 협업과 콘텐츠 성과 분석을 합니다.","field":"예술·콘텐츠","keywords":["영상","국어","미술","창의적 아이디어","기획·조직","의사소통"],"major":"영상학과, 미디어학과, 방송영상학과","related":"영상 연출가, 콘텐츠 마케터"},
    {"name":"신재생에너지 연구원","summary":"태양광·풍력 등 지속가능한 에너지 기술을 연구하고 개선합니다.","work":"에너지 시스템을 분석하고 효율과 안전성을 높이는 연구를 합니다.","field":"융합·미래","keywords":["에너지","환경","물리","수학","과학","문제 해결"],"major":"에너지공학과, 전기공학과, 환경공학과","related":"에너지 시스템 엔지니어, 전력 연구원"},
    {"name":"게임 기획자","summary":"게임의 규칙과 콘텐츠, 사용자 경험을 기획하고 개발 과정을 조율합니다.","work":"게임 콘셉트와 시스템을 설계하고 개발팀과 테스트·개선을 진행합니다.","field":"예술·콘텐츠","keywords":["게임","정보","미술","창의적 아이디어","기획·조직","협업"],"major":"게임학과, 컴퓨터공학과, 콘텐츠 관련 학과","related":"게임 디자이너, 레벨 디자이너"},
]

AREA_KEYWORDS = {
    "인문·언어":["작가","번역","언어","역사","문화"],
    "사회·경영":["경영","경제","마케팅","정책","금융"],
    "교육·심리":["교육","교사","심리","상담"],
    "자연·생명":["생명","환경","화학","물리","연구"],
    "공학·IT":["인공지능","데이터","소프트웨어","로봇","반도체","컴퓨터"],
    "의약·보건":["의사","간호","약사","의료","보건"],
    "예술·콘텐츠":["디자인","영상","게임","콘텐츠"],
    "융합·미래":["에너지","환경","AI","우주"],
}


def get_secret(name: str) -> str:
    try:
        value = st.secrets.get(name, "")
        if value:
            return str(value).strip()
    except Exception:
        pass
    return os.getenv(name, "").strip()


CAREER_NET_KEY = get_secret("CAREER_NET_API_KEY")
OPENAI_KEY = get_secret("OPENAI_API_KEY")


# ---------------------------------------------------------------------
# 커리어넷 API 연결
# ---------------------------------------------------------------------
@st.cache_data(ttl=3600, show_spinner=False)
def career_net_search(keyword: str, api_key: str) -> list[dict[str, Any]]:
    """커리어넷 직업백과 목록 API. 공식 jobs.json의 jobs 배열을 반환."""
    if not api_key or not keyword:
        return []
    url = f"{CAREER_NET_BASE}/jobs.json"
    try:
        response = requests.get(
            url,
            params={"apiKey": api_key, "pageIndex": 1, "searchJobNm": keyword},
            timeout=12,
            headers={"User-Agent": "NEXUS-Career-Explorer/1.0"},
        )
        response.raise_for_status()
        payload = response.json()
        jobs = payload.get("jobs", [])
        return jobs if isinstance(jobs, list) else []
    except (requests.RequestException, ValueError, TypeError):
        return []


@st.cache_data(ttl=3600, show_spinner=False)
def career_net_detail(seq: str, api_key: str) -> dict[str, Any]:
    """커리어넷 직업백과 상세 API."""
    if not api_key or not seq:
        return {}
    try:
        response = requests.get(
            f"{CAREER_NET_BASE}/job.json",
            params={"apiKey": api_key, "seq": seq},
            timeout=12,
            headers={"User-Agent": "NEXUS-Career-Explorer/1.0"},
        )
        response.raise_for_status()
        data = response.json()
        return data if isinstance(data, dict) else {}
    except (requests.RequestException, ValueError, TypeError):
        return {}


def safe_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (str, int, float)):
        return str(value).strip()
    return ""


def list_text(value: Any, field: str = "") -> list[str]:
    """API 응답의 list/dict/string 형태를 안전하게 문자열 목록으로 변환."""
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if isinstance(value, dict):
        if field and value.get(field):
            return [safe_text(value[field])]
        output = []
        for item in value.values():
            output.extend(list_text(item, field))
        return [x for x in output if x]
    if isinstance(value, list):
        output = []
        for item in value:
            if isinstance(item, dict):
                if field and item.get(field):
                    output.append(safe_text(item[field]))
                elif not field:
                    output.extend(safe_text(v) for v in item.values() if isinstance(v, (str, int, float)) and safe_text(v))
            elif safe_text(item):
                output.append(safe_text(item))
        return [x for x in output if x]
    return []


def normalize_api_job(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "name": safe_text(item.get("job_nm")) or "직업명 미확인",
        "summary": safe_text(item.get("work")) or "커리어넷 직업백과에서 상세 정보를 확인할 수 있습니다.",
        "work": safe_text(item.get("work")),
        "field": safe_text(item.get("top_nm") or item.get("tob_nm") or item.get("aptit_name")),
        "keywords": [safe_text(item.get("aptit_name")), safe_text(item.get("top_nm")), safe_text(item.get("tob_nm"))],
        "major": "",
        "related": safe_text(item.get("rel_job_nm")),
        "wage": safe_text(item.get("wage")),
        "social": safe_text(item.get("social")),
        "wlb": safe_text(item.get("wlb")),
        "seq": safe_text(item.get("job_cd")),
        "source": "커리어넷 직업백과 API",
        "source_url": CAREER_NET_HOME,
    }


def fetch_live_jobs(profile: dict[str, Any]) -> list[dict[str, Any]]:
    """선택 영역과 흥미 키워드로 API 검색 후 중복 직업 제거."""
    if not CAREER_NET_KEY:
        return []
    area = profile.get("area", "")
    queries = []
    queries.extend(AREA_KEYWORDS.get(area, [])[:3])
    queries.extend(profile.get("keywords", [])[:3])
    queries = list(dict.fromkeys([q for q in queries if q]))[:5]

    found: dict[str, dict[str, Any]] = {}
    for query in queries:
        for item in career_net_search(query, CAREER_NET_KEY):
            if not isinstance(item, dict):
                continue
            normalized = normalize_api_job(item)
            if normalized["name"] != "직업명 미확인":
                found[normalized["name"]] = normalized
            if len(found) >= 45:
                break
        if len(found) >= 45:
            break
    return list(found.values())


# ---------------------------------------------------------------------
# 추천 엔진: 선택 영역 + 과목 + 역량 + 업무 선호 + 키워드 유사도
# ---------------------------------------------------------------------
def job_score(job: dict[str, Any], profile: dict[str, Any]) -> tuple[int, list[str]]:
    score = 0
    matched = []
    job_text = " ".join([
        job.get("name", ""), job.get("summary", ""), job.get("work", ""),
        job.get("field", ""), " ".join(job.get("keywords", [])),
        job.get("major", ""), job.get("related", ""),
    ]).lower()

    if profile.get("area") and profile["area"] in job.get("field", ""):
        score += 5
        matched.append("관심 영역")
    for token in profile.get("keywords", []):
        if token and token.lower() in job_text:
            score += 4
            matched.append(token)
    for subject in profile.get("subjects", []):
        if subject.lower() in job_text:
            score += 2
            matched.append(f"{subject} 과목")
    for strength in profile.get("strengths", []):
        if strength.lower() in job_text:
            score += 3
            matched.append(strength)
    for style in profile.get("styles", []):
        style_map = {
            "혼자 깊이 탐구하기": ["연구", "분석", "탐구"],
            "팀으로 협업하기": ["협업", "팀", "소통"],
            "사람을 직접 돕기": ["상담", "교육", "환자", "지원", "도움"],
            "새로운 것을 기획·창작하기": ["기획", "창작", "디자인", "개발"],
            "실험·제작·실습하기": ["실험", "제작", "설계", "연구"],
            "데이터와 정보를 분석하기": ["데이터", "분석", "자료", "통계"],
        }
        if any(word in job_text for word in style_map.get(style, [])):
            score += 2
            matched.append(style)
    # 반복 매칭은 추천 이유에 한 번만 표시
    return score, list(dict.fromkeys(matched))[:5]


def make_recommendations(profile: dict[str, Any], api_jobs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    candidates = api_jobs if api_jobs else DEMO_JOBS
    scored = []
    for job in candidates:
        score, matched = job_score(job, profile)
        result = dict(job)
        result["score"] = score
        result["matched"] = matched
        scored.append(result)
    scored.sort(key=lambda x: (x["score"], x.get("name", "")), reverse=True)
    # 적합도는 후보 내 상대 점수로 표시. 검사 결과나 진단이 아님.
    max_score = max([x["score"] for x in scored], default=1) or 1
    for item in scored:
        item["fit"] = min(98, max(55, int(55 + (item["score"] / max_score) * 43)))
    return scored[:8]


def ai_rank_recommendations(profile: dict[str, Any], recommendations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """OpenAI 키가 있으면 학생 선택과 직업 설명을 바탕으로 후보 순서를 보정."""
    if not OPENAI_KEY or OpenAI is None or not recommendations:
        return recommendations
    try:
        client = OpenAI(api_key=OPENAI_KEY, timeout=20)
        candidates = [
            {"name": x.get("name", ""), "summary": x.get("summary", "")[:220],
             "field": x.get("field", ""), "matched": x.get("matched", [])}
            for x in recommendations[:8]
        ]
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            temperature=0.2,
            max_tokens=450,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content":
                 "너는 고등학생 진로 탐색 추천 도우미다. 학생이 고른 관심 영역, 과목, 강점, 활동 선호와 직업 후보의 설명을 비교해 적합한 탐색 순서를 정한다. "
                 "학생의 미래나 적성을 단정하지 말고, 제공된 후보 이름만 사용한다. JSON 객체로 ranked_names 배열과 short_reason 문자열을 반환한다."},
                {"role": "user", "content":
                 json.dumps({"profile": profile, "candidates": candidates}, ensure_ascii=False)}
            ],
        )
        payload = json.loads(response.choices[0].message.content or "{}")
        order = payload.get("ranked_names", [])
        by_name = {x.get("name"): x for x in recommendations}
        ranked = [by_name[name] for name in order if name in by_name]
        used = {x.get("name") for x in ranked}
        ranked.extend(x for x in recommendations if x.get("name") not in used)
        return ranked[:8]
    except Exception:
        return recommendations


def ai_explanation(profile: dict[str, Any], recommendations: list[dict[str, Any]]) -> str:
    """OpenAI 키가 있을 때만 설명 문장을 생성. 없으면 규칙 기반 안내."""
    if not OPENAI_KEY or OpenAI is None:
        first = recommendations[:3]
        names = ", ".join(x["name"] for x in first)
        return (
            f"선택한 관심 영역과 과목, 역량, 활동 선호를 비교했을 때 "
            f"{names} 분야를 먼저 탐색해 볼 수 있어요. 추천 점수는 입력한 선택과 "
            "직업 설명의 키워드 일치도를 계산한 탐색용 참고값이며, 적성검사나 진로 확정 결과는 아닙니다."
        )
    try:
        client = OpenAI(api_key=OPENAI_KEY, timeout=20)
        brief_jobs = [
            {"name": x["name"], "summary": x.get("summary", "")[:280], "matched": x.get("matched", [])}
            for x in recommendations[:5]
        ]
        response = client.chat.completions.create(
            model="gpt-4.1-mini",
            temperature=0.4,
            max_tokens=320,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "너는 고등학생의 진로 탐색을 돕는 진로 코치다. "
                        "입력한 관심과 직업 정보만 근거로 3~5문장 한국어 추천 설명을 작성한다. "
                        "직업을 단정하거나 성격·적성을 진단하지 말고, 다양한 가능성을 열어 둔다. "
                        "대학 합격, 연봉, 취업을 보장하지 않는다. 학생 개인정보를 요구하지 않는다."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"관심영역: {profile.get('area')}\n관심키워드: {profile.get('keywords')}\n"
                        f"좋아하는 과목: {profile.get('subjects')}\n강점: {profile.get('strengths')}\n"
                        f"선호 활동: {profile.get('styles')}\n추천 후보: {brief_jobs}\n"
                        "추천 이유와 각 직업을 더 탐구할 질문을 제안해줘."
                    ),
                },
            ],
        )
        return response.choices[0].message.content.strip()
    except Exception:
        return "AI 설명 서비스를 사용할 수 없어 키워드 기반 추천 결과를 표시합니다. 아래 직업 카드를 비교해 보세요."


# ---------------------------------------------------------------------
# 상태 / 공통 UI
# ---------------------------------------------------------------------
DEFAULTS = {
    "page": "home",
    "profile": {},
    "recommendations": [],
    "selected_job": None,
    "saved_jobs": [],
    "ai_note": "",
    "live_used": False,
}
for key, value in DEFAULTS.items():
    if key not in st.session_state:
        st.session_state[key] = value


def navigate(page: str):
    st.session_state.page = page
    st.rerun()


def header(step: str, title: str, desc: str, progress: float):
    st.markdown('<div class="brand">NEXUS · AI CAREER LAB</div>', unsafe_allow_html=True)
    st.markdown(f'<span class="step">{step}</span>', unsafe_allow_html=True)
    st.markdown(f"## {title}")
    st.markdown(f'<div class="subtle">{desc}</div>', unsafe_allow_html=True)
    st.progress(progress)


def career_detail_url(job: dict[str, Any]) -> str:
    # API에서 반환한 직업 코드가 있으면 커리어넷 직업정보 사이트로 안내
    seq = job.get("seq", "")
    if seq:
        return f"https://www.career.go.kr/cnet/front/base/job/jobView.do?SEQ={seq}"
    return CAREER_NET_HOME


# ---------------------------------------------------------------------
# 홈
# ---------------------------------------------------------------------
page = st.session_state.page

if page == "home":
    st.markdown('<div class="brand">NEXUS · AI CAREER LAB</div>', unsafe_allow_html=True)
    st.markdown(
        """
        <div class="hero">
          <div class="eyebrow">DISCOVER YOUR NEXT</div>
          <h1>미래는 선택이 아니라,<br>탐색에서 시작돼.</h1>
          <p>관심 과목과 강점, 좋아하는 활동을 바탕으로<br>나에게 맞는 진로 가능성을 발견해 보세요.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    left, right = st.columns([1.35, 1], gap="large")
    with left:
        st.markdown("### 나의 진로 탐색을 시작할까요?")
        st.markdown('<div class="subtle">정답을 찾는 검사가 아니라, 새로운 가능성을 발견하는 탐색 도구입니다.</div>', unsafe_allow_html=True)
        st.write("")
        if st.button("✦ AI 진로 추천 시작하기", type="primary", use_container_width=True):
            navigate("profile")
        st.write("")
        if st.button("직업 데이터 둘러보기", use_container_width=True):
            st.session_state.profile = {
                "area": "공학·IT", "keywords": ["데이터", "인공지능"],
                "subjects": ["정보", "수학"], "strengths": ["논리적 사고", "문제 해결"],
                "styles": ["데이터와 정보를 분석하기"],
            }
            with st.spinner("직업 데이터를 불러오는 중..."):
                live = fetch_live_jobs(st.session_state.profile)
                st.session_state.recommendations = make_recommendations(st.session_state.profile, live)
                st.session_state.recommendations = ai_rank_recommendations(st.session_state.profile, st.session_state.recommendations)
                st.session_state.ai_note = ai_explanation(st.session_state.profile, st.session_state.recommendations)
                st.session_state.live_used = bool(live)
            navigate("recommend")
    with right:
        st.markdown("### 탐색 프로세스")
        for title, desc in [
            ("01 · 나를 입력하기", "관심 분야와 좋아하는 과목, 강점 선택"),
            ("02 · AI 추천 분석", "선택한 내용과 직업 데이터의 연결"),
            ("03 · 직업 비교하기", "하는 일, 관련 학과, 진로 탐색활동 확인"),
            ("04 · 나의 탐구 기록", "관심 직업을 저장하고 탐구 질문 정리"),
        ]:
            st.markdown(f'<div class="panel" style="margin-bottom:.55rem"><h4>{title}</h4><p>{desc}</p></div>', unsafe_allow_html=True)
        if CAREER_NET_KEY:
            st.success("커리어넷 API 연결 설정됨")
        else:
            st.info("커리어넷 API 키 미설정 · 데모 데이터로 실행")
    st.markdown('<div class="footer">NEXUS는 진로 탐색을 돕는 참고 도구입니다. 추천 결과가 진로 적성이나 미래를 확정하지 않습니다.</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------------
# 학생 프로필 입력
# ---------------------------------------------------------------------
elif page == "profile":
    header("01 / PROFILE", "어떤 것에 관심이 있나요?", "정답은 없어요. 지금의 관심과 선호를 편하게 골라주세요.", 0.25)
    with st.form("profile_form"):
        area = st.selectbox("가장 탐구하고 싶은 영역", list(AREAS.keys()), index=4)
        keywords = st.multiselect(
            "관심 키워드 (최대 5개)",
            options=list(dict.fromkeys(AREAS[area] + ["AI", "데이터", "디자인", "환경", "교육", "의료", "콘텐츠", "사회문제", "창업"])),
            default=AREAS[area][:2],
            max_selections=5,
        )
        subjects = st.multiselect("좋아하거나 더 알아보고 싶은 과목", SUBJECTS, default=["수학", "정보"] if area == "공학·IT" else [])
        strengths = st.multiselect("내가 발휘하고 싶은 강점", STRENGTHS, default=["문제 해결", "창의적 아이디어"], max_selections=5)
        styles = st.multiselect("선호하는 활동 방식", WORK_STYLES, default=["새로운 것을 기획·창작하기"], max_selections=3)
        submitted = st.form_submit_button("내 관심 분석하고 직업 추천받기", type="primary", use_container_width=True)
    if submitted:
        if not keywords:
            st.warning("관심 키워드를 한 가지 이상 선택해 주세요.")
        else:
            st.session_state.profile = {
                "area": area,
                "keywords": keywords,
                "subjects": subjects,
                "strengths": strengths,
                "styles": styles,
            }
            with st.spinner("관심 분야와 직업 데이터를 분석하고 있어요..."):
                live_jobs = fetch_live_jobs(st.session_state.profile)
                st.session_state.recommendations = make_recommendations(st.session_state.profile, live_jobs)
                st.session_state.recommendations = ai_rank_recommendations(st.session_state.profile, st.session_state.recommendations)
                st.session_state.ai_note = ai_explanation(st.session_state.profile, st.session_state.recommendations)
                st.session_state.live_used = bool(live_jobs)
            navigate("recommend")
    if st.button("← 홈으로", use_container_width=True):
        navigate("home")


# ---------------------------------------------------------------------
# 추천 결과
# ---------------------------------------------------------------------
elif page == "recommend":
    profile = st.session_state.profile
    recs = st.session_state.recommendations
    header("02 / AI MATCH", "당신의 관심과 연결되는 직업", "선택한 정보를 바탕으로 탐색해 볼 만한 직업을 정리했어요.", 0.55)
    st.markdown(
        f'<div class="path">관심 영역: {profile.get("area","")}　·　키워드: {", ".join(profile.get("keywords", []))}</div>',
        unsafe_allow_html=True,
    )
    if st.session_state.live_used:
        st.success("커리어넷 직업백과 API에서 검색한 실시간 연동 데이터를 사용하고 있어요.")
    else:
        st.info("현재 데모 직업 데이터를 사용 중입니다. 실제 커리어넷 데이터를 쓰려면 CAREER_NET_API_KEY를 등록하세요.")
    st.markdown(f'<div class="panel"><h4>✦ AI 탐색 코멘트</h4><p>{st.session_state.ai_note}</p></div>', unsafe_allow_html=True)
    st.write("")
    if not recs:
        st.warning("추천할 직업 데이터가 없습니다. 프로필을 다시 선택해 주세요.")
    else:
        cols = st.columns(3)
        for i, job in enumerate(recs[:6]):
            with cols[i % 3]:
                tags = " ".join(f'<span class="tag">{t}</span>' for t in job.get("matched", [])[:3])
                st.markdown(
                    f'<div class="job-card"><div class="source">MATCH · {job.get("fit", 55)}% 탐색 일치도</div>'
                    f'<h3>{job.get("name","직업")}</h3><p style="color:#6b7890;font-size:.84rem;line-height:1.45">{job.get("summary","")[:105]}</p>{tags}</div>',
                    unsafe_allow_html=True,
                )
                if st.button("직업 상세 보기", key=f"detail_{i}", use_container_width=True):
                    st.session_state.selected_job = job
                    navigate("detail")
    st.caption("일치도는 선택한 항목과 직업 정보의 키워드가 얼마나 겹치는지 계산한 탐색용 점수입니다. 과학적 적성검사 결과가 아닙니다.")
    a, b = st.columns(2)
    with a:
        if st.button("← 프로필 수정", use_container_width=True):
            navigate("profile")
    with b:
        if st.button("저장한 직업 보기", use_container_width=True):
            navigate("saved")


# ---------------------------------------------------------------------
# 직업 상세
# ---------------------------------------------------------------------
elif page == "detail":
    job = st.session_state.selected_job or {}
    header("03 / CAREER DETAIL", job.get("name", "직업 상세"), "직업 정보와 진로 준비 방향을 확인해 보세요.", 0.78)

    detail = {}
    if job.get("seq") and CAREER_NET_KEY:
        with st.spinner("커리어넷 직업 상세 정보를 불러오는 중..."):
            detail = career_net_detail(job["seq"], CAREER_NET_KEY)

    base = detail.get("baseInfo", {}) if isinstance(detail.get("baseInfo"), dict) else {}
    work_items = list_text(detail.get("workList"), "work")
    interest_items = list_text(detail.get("interestList"), "interest")
    research_items = list_text(detail.get("researchList"), "research")
    forecast_items = list_text(detail.get("forecastList"), "forecast")
    depart_items = list_text(detail.get("departList"), "depart_name")
    ability_items = list_text(detail.get("abilityList"), "ability_name")
    related = safe_text(base.get("rel_job_nm")) or job.get("related", "")
    majors = ", ".join(depart_items) if depart_items else job.get("major", "")

    left, right = st.columns([1.2, 1], gap="large")
    with left:
        st.markdown("### 어떤 일을 하나요?")
        work_text = work_items if work_items else [job.get("work") or job.get("summary", "상세 업무 정보는 커리어넷에서 확인하세요.")]
        for text in work_text[:4]:
            st.markdown(f'<div class="panel" style="margin-bottom:.5rem"><p>{text}</p></div>', unsafe_allow_html=True)
        st.markdown("### 관련 학과")
        st.markdown(f'<div class="panel"><p>{majors or "커리어넷 상세 정보 또는 대학별 학과 안내에서 확인하세요."}</p></div>', unsafe_allow_html=True)
        if related:
            st.markdown("### 관련 직업")
            st.markdown(f'<div class="panel"><p>{related}</p></div>', unsafe_allow_html=True)
    with right:
        st.markdown("### 흥미와 적성 단서")
        for text in (interest_items[:3] or ["어떤 활동을 할 때 몰입하는지, 관련 과목에서 무엇이 흥미로운지 스스로 관찰해 보세요."]):
            st.markdown(f'<div class="panel" style="margin-bottom:.5rem"><p>{text}</p></div>', unsafe_allow_html=True)
        if ability_items:
            st.markdown("### 핵심 역량")
            st.markdown(f'<div class="panel"><p>{", ".join(ability_items[:8])}</p></div>', unsafe_allow_html=True)
        st.markdown("### 진로 탐색 활동")
        for text in (research_items[:3] or ["관련 도서·강연·학교 동아리 활동을 찾아보고 작은 탐구 프로젝트를 진행해 보세요."]):
            st.markdown(f'<div class="panel" style="margin-bottom:.5rem"><p>{text}</p></div>', unsafe_allow_html=True)

    if forecast_items:
        st.markdown("### 직업 전망 (커리어넷 제공 정보)")
        st.markdown(f'<div class="panel"><p>{forecast_items[0]}</p></div>', unsafe_allow_html=True)
        st.caption("전망은 조사 시점과 출처에 따라 달라질 수 있습니다. 최신 정보를 원문에서 확인하세요.")

    question = st.text_area("나만의 탐구 질문", placeholder="예: 이 직업은 인공지능 기술을 실제 업무에 어떻게 활용할까?", height=85)
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("☆ 관심 직업 저장", use_container_width=True):
            saved = {
                "name": job.get("name", ""),
                "area": st.session_state.profile.get("area", ""),
                "question": question,
                "seq": job.get("seq", ""),
            }
            if not any(x.get("name") == saved["name"] for x in st.session_state.saved_jobs):
                st.session_state.saved_jobs.append(saved)
            st.success("관심 직업에 저장했어요.")
    with c2:
        if st.button("커리어넷 원문 보기", use_container_width=True):
            st.link_button("커리어넷 직업정보 열기", career_detail_url(job), use_container_width=True)
    with c3:
        if st.button("← 추천 목록", use_container_width=True):
            navigate("recommend")


# ---------------------------------------------------------------------
# 저장 목록 및 간단 리포트
# ---------------------------------------------------------------------
elif page == "saved":
    header("04 / MY PATH", "나의 진로 보관함", "관심 직업과 직접 작성한 탐구 질문을 모아보세요.", 1.0)
    saved = st.session_state.saved_jobs
    if not saved:
        st.info("아직 저장한 직업이 없습니다. 추천 결과에서 직업 상세를 열고 저장해 보세요.")
    else:
        lines = ["NEXUS 진로 탐색 기록", "===================="]
        for i, item in enumerate(saved, 1):
            st.markdown(
                f'<div class="panel" style="margin-bottom:.6rem"><h4>{i}. {item.get("name","")}</h4>'
                f'<p>관심 영역: {item.get("area","")}</p><p>탐구 질문: {item.get("question") or "아직 작성하지 않음"}</p></div>',
                unsafe_allow_html=True,
            )
            lines.extend([
                f"{i}. {item.get('name','')}",
                f"관심 영역: {item.get('area','')}",
                f"탐구 질문: {item.get('question') or '아직 작성하지 않음'}",
                "",
            ])
        st.download_button(
            "⬇️ 진로 탐색 기록 다운로드",
            data="\n".join(lines),
            file_name="nexus_career_record.txt",
            mime="text/plain",
            use_container_width=True,
        )
    if st.button("← 추천 결과로", use_container_width=True):
        navigate("recommend")


# ---------------------------------------------------------------------
# 공통 하단: QR / API 상태 / 출처
# ---------------------------------------------------------------------
with st.expander("⚙️ 데이터 연결 및 QR 배포 설정"):
    st.markdown("**데이터 출처**")
    st.markdown(
        "- [커리어넷 Open API 센터](https://www.career.go.kr/cnet/front/openapi/openApiMainCenter.do)\n"
        "- [커리어넷 직업백과](https://www.career.go.kr/)\n"
        "- [고용24 직업정보](https://www.work24.go.kr/)"
    )
    st.markdown("**Streamlit Cloud Secrets 설정**")
    st.code(
        'CAREER_NET_API_KEY = "발급받은_커리어넷_API_키"\n'
        'OPENAI_API_KEY = "선택사항_OpenAI_API_키"\n'
        'APP_URL = "https://내앱이름.streamlit.app"',
        language="toml",
    )
    st.caption("API 키는 app.py에 직접 입력하거나 GitHub에 올리지 마세요. Streamlit Cloud의 Settings → Secrets에 저장하세요.")
    app_url = get_secret("APP_URL")
    if app_url:
        if qrcode:
            qr = qrcode.QRCode(box_size=6, border=2)
            qr.add_data(app_url)
            qr.make(fit=True)
            qr_img = qr.make_image(fill_color="#243b79", back_color="white")
            buffer = BytesIO()
            qr_img.save(buffer, format="PNG")
            st.image(buffer.getvalue(), width=180)
        st.code(app_url)
    else:
        st.info("배포 후 APP_URL에 Streamlit 앱 주소를 등록하면 QR 코드가 나타납니다.")
    st.write(
        f"커리어넷 API: {'연결 키 설정됨' if CAREER_NET_KEY else '키 미설정'}  ·  "
        f"AI 설명: {'OpenAI API 사용 가능' if OPENAI_KEY and OpenAI else '키 미설정(규칙 기반 추천 설명 사용)'}"
    )

st.markdown(
    '<div class="footer">NEXUS AI CAREER LAB · 직업정보 출처: 커리어넷 · 추천은 탐색 참고용이며 진로 적성 진단이나 미래 예측이 아닙니다.</div>',
    unsafe_allow_html=True,
)
