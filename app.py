import os, json, sqlite3, random, string
from datetime import datetime
from urllib.parse import quote
import requests
import pandas as pd
import plotly.express as px
import qrcode
import streamlit as st

st.set_page_config(page_title="가족 여행 탐험대", page_icon="🧭", layout="wide")
DB = "family_trip_explorer.db"
STYLES = ["자연·풍경", "맛집·카페", "역사·문화", "쇼핑", "액티비티", "휴식·힐링", "사진 명소", "테마파크", "바다·해변", "박물관·전시"]
PLACES = [
 {"name":"제주도","country":"대한민국","region":"국내","tags":["자연·풍경","맛집·카페","사진 명소","바다·해변","휴식·힐링"],"desc":"오름과 바다, 카페와 자연을 즐기는 섬 여행","emoji":"🌋"},
 {"name":"부산","country":"대한민국","region":"국내","tags":["맛집·카페","바다·해변","쇼핑","사진 명소"],"desc":"해변과 시장, 맛집이 어우러진 도시 여행","emoji":"🌊"},
 {"name":"강릉","country":"대한민국","region":"국내","tags":["자연·풍경","맛집·카페","바다·해변","휴식·힐링"],"desc":"동해 바다와 커피 거리에서 즐기는 여유","emoji":"☕"},
 {"name":"경주","country":"대한민국","region":"국내","tags":["역사·문화","사진 명소","자연·풍경"],"desc":"역사 유적과 한옥 풍경을 만나는 여행","emoji":"🏛️"},
 {"name":"전주","country":"대한민국","region":"국내","tags":["맛집·카페","역사·문화","사진 명소"],"desc":"한옥마을과 지역 먹거리를 즐기는 여행","emoji":"🍲"},
 {"name":"서울","country":"대한민국","region":"국내","tags":["쇼핑","맛집·카페","역사·문화","박물관·전시","테마파크"],"desc":"문화 공간과 쇼핑, 다양한 먹거리가 있는 여행","emoji":"🏙️"},
 {"name":"도쿄","country":"일본","region":"해외","tags":["쇼핑","맛집·카페","테마파크","박물관·전시"],"desc":"도시 문화와 쇼핑, 맛집을 즐기는 여행","emoji":"🗼"},
 {"name":"오사카","country":"일본","region":"해외","tags":["맛집·카페","쇼핑","테마파크"],"desc":"먹거리와 쇼핑, 즐길 거리가 풍부한 도시","emoji":"🐙"},
 {"name":"후쿠오카","country":"일본","region":"해외","tags":["맛집·카페","쇼핑","휴식·힐링"],"desc":"가까운 거리에서 맛집과 여유를 즐기는 여행","emoji":"🍜"},
 {"name":"타이베이","country":"대만","region":"해외","tags":["맛집·카페","역사·문화","쇼핑"],"desc":"야시장과 골목 문화, 근교 풍경을 즐기는 여행","emoji":"🏮"},
 {"name":"방콕","country":"태국","region":"해외","tags":["맛집·카페","역사·문화","쇼핑","휴식·힐링"],"desc":"사원과 시장, 도심 속 휴식을 함께하는 여행","emoji":"🌴"},
 {"name":"다낭","country":"베트남","region":"해외","tags":["바다·해변","휴식·힐링","맛집·카페","자연·풍경"],"desc":"해변과 리조트에서 쉬어 가는 여행","emoji":"🏖️"},
 {"name":"싱가포르","country":"싱가포르","region":"해외","tags":["테마파크","쇼핑","맛집·카페","사진 명소"],"desc":"깨끗한 도심과 다양한 명소를 즐기는 여행","emoji":"🦁"},
 {"name":"파리","country":"프랑스","region":"해외","tags":["역사·문화","박물관·전시","맛집·카페","사진 명소"],"desc":"예술과 건축, 거리 풍경을 만나는 여행","emoji":"🗼"},
]

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR:wght@400;500;600;700;800&display=swap');
:root{--green:#03c75a;--ink:#17212b;--muted:#687782;--line:#e7ecef;--surface:#ffffff}
html,body,[class*="css"]{font-family:'Noto Sans KR',sans-serif}
.stApp{background:#f4f6f8;color:var(--ink)}
header[data-testid="stHeader"]{background:rgba(244,246,248,.92)}
.block-container{max-width:1120px;padding-top:1.4rem;padding-bottom:3rem;margin:0 auto}
section[data-testid="stSidebar"]{background:#fff;border-right:1px solid var(--line)}
section[data-testid="stSidebar"] *{color:var(--ink)}
section[data-testid="stSidebar"] [data-testid="stCode"]{background:#f5f7f8}
h1,h2,h3,h4{color:#17212b!important;letter-spacing:-.035em}
p,li,label,.stMarkdown{color:#35434d}
.hero{padding:1.55rem 1.7rem;border-radius:20px;background:linear-gradient(110deg,#e9f9ef,#f1f8ff);border:1px solid #dcefe3;margin:0 0 1.15rem;box-shadow:0 4px 18px #17212b08}
.hero h1{font-size:clamp(1.7rem,3vw,2.35rem);font-weight:800;margin:0;color:#17212b!important}
.hero p,.muted{color:#65737d}
.tile{background:#fff;border:1px solid #e7ecef;border-radius:17px;padding:1.05rem 1.15rem;margin-bottom:.7rem;box-shadow:0 3px 14px #17212b08}
.pill{display:inline-block;padding:.22rem .58rem;margin:.12rem;border-radius:30px;background:#eaf8ef;color:#07883f;font-size:.76rem}
div.stButton>button{border-radius:11px;background:#03c75a;color:white;border:1px solid #03b950;font-weight:700;min-height:2.65rem;transition:.15s}
div.stButton>button:hover{background:#02b950;border-color:#02b950;color:white}
div[data-testid="stTextInput"] input,div[data-testid="stSelectbox"]>div,div[data-testid="stMultiSelect"]>div{border-radius:10px}
[data-testid="stMetric"]{background:#fff;padding:.85rem;border:1px solid #e7ecef;border-radius:14px;box-shadow:0 3px 12px #17212b06}
[data-testid="stMetricLabel"]{color:#65737d}
[data-testid="stMetricValue"]{color:#17212b}
[data-testid="stRadio"] label{font-weight:600}
div[role="radiogroup"]{gap:.35rem}
div[role="radiogroup"] label{background:#fff;border:1px solid #e7ecef;border-radius:999px;padding:.45rem .9rem}
div[role="radiogroup"] label:has(input:checked){background:#eaf8ef;border-color:#bce9cc}
.stTabs [data-baseweb="tab-list"]{gap:.45rem}
.stTabs [data-baseweb="tab"]{background:#fff;border-radius:10px 10px 0 0;padding:.65rem 1rem}
hr{border-color:#e7ecef}
@media(max-width:700px){
 .block-container{padding-left:1rem;padding-right:1rem;padding-top:.7rem}
 .hero{padding:1.15rem;border-radius:16px}
}
</style>
""", unsafe_allow_html=True)

def conn():
    c=sqlite3.connect(DB,check_same_thread=False); c.row_factory=sqlite3.Row; return c

def init():
    with conn() as c:
        c.execute("CREATE TABLE IF NOT EXISTS rooms(code TEXT PRIMARY KEY,name TEXT,created TEXT)")
        c.execute("CREATE TABLE IF NOT EXISTS members(id INTEGER PRIMARY KEY,room TEXT,name TEXT,prefs TEXT,UNIQUE(room,name))")
        c.execute("CREATE TABLE IF NOT EXISTS votes(id INTEGER PRIMARY KEY,room TEXT,member TEXT,dest TEXT,updated TEXT,UNIQUE(room,member))")
init()

def room(code):
    with conn() as c: return c.execute("SELECT * FROM rooms WHERE code=?",(code,)).fetchone()

def new_room(name):
    code=''.join(random.choices(string.digits,k=6))
    with conn() as c:
        while c.execute("SELECT 1 FROM rooms WHERE code=?",(code,)).fetchone(): code=''.join(random.choices(string.digits,k=6))
        c.execute("INSERT INTO rooms VALUES(?,?,?)",(code,name,datetime.now().isoformat()))
    return code

def members(code):
    with conn() as c: rows=c.execute("SELECT name,prefs FROM members WHERE room=? ORDER BY id",(code,)).fetchall()
    return [{"name":r["name"],"prefs":json.loads(r["prefs"])} for r in rows]

def save_member(code,name,prefs):
    with conn() as c:
        c.execute("INSERT INTO members(room,name,prefs) VALUES(?,?,?) ON CONFLICT(room,name) DO UPDATE SET prefs=excluded.prefs",(code,name,json.dumps(prefs,ensure_ascii=False)))

def votes(code):
    with conn() as c: rows=c.execute("SELECT member,dest FROM votes WHERE room=?",(code,)).fetchall()
    return [{"member":r["member"],"dest":r["dest"]} for r in rows]

def cast_vote(code,member,dest):
    with conn() as c:
        c.execute("INSERT INTO votes(room,member,dest,updated) VALUES(?,?,?,?) ON CONFLICT(room,member) DO UPDATE SET dest=excluded.dest,updated=excluded.updated",(code,member,dest,datetime.now().isoformat()))

def score(place,people):
    if not people:return 0
    tags=set(place["tags"])
    return round(sum(len(tags & set(p["prefs"]))/max(1,len(p["prefs"]))*100 for p in people)/len(people))

def live_domestic(keyword):
    key=st.secrets.get("TOUR_API_KEY",os.getenv("TOUR_API_KEY",""))
    if not key:return []
    try:
        url="https://apis.data.go.kr/B551011/KorService2/searchKeyword2"
        params={"serviceKey":key,"MobileOS":"ETC","MobileApp":"FamilyTripExplorer","_type":"json","numOfRows":12,"pageNo":1,"keyword":keyword}
        data=requests.get(url,params=params,timeout=12); data.raise_for_status()
        items=data.json().get("response",{}).get("body",{}).get("items",{}).get("item",[])
        if isinstance(items,dict):items=[items]
        return [{"name":x.get("title","관광지"),"country":"대한민국","region":"국내","tags":["자연·풍경","사진 명소"],"desc":x.get("addr1","한국관광공사 관광정보"),"emoji":"📍"} for x in items or []]
    except Exception:return []

def analyze(people):
    key=st.secrets.get("OPENAI_API_KEY",os.getenv("OPENAI_API_KEY",""))
    prompt="가족 여행 플래너로서 가족별 취향을 분석해 공통점, 차이점, 모두가 만족할 여행 방향을 한국어로 제안해줘.\\n"+ "\\n".join(f"{p['name']}: {', '.join(p['prefs'])}" for p in people)
    if key:
        try:
            r=requests.post("https://api.openai.com/v1/chat/completions",headers={"Authorization":f"Bearer {key}","Content-Type":"application/json"},json={"model":"gpt-4o-mini","messages":[{"role":"user","content":prompt}],"temperature":0.5},timeout=25)
            r.raise_for_status(); return r.json()["choices"][0]["message"]["content"]
        except Exception: pass
    counts={s:sum(s in p["prefs"] for p in people) for s in STYLES}
    common=[s for s,n in counts.items() if n==len(people)]
    popular=sorted(counts.items(),key=lambda x:x[1],reverse=True)[:4]
    return ("### 🤝 가족 공통 취향\\n"+(", ".join(common) if common else "모두가 선택한 동일 취향은 아직 없어요.")+
    "\\n\\n### 🔎 눈에 띄는 취향\\n"+", ".join(f"{s}({n}명)" for s,n in popular if n)+
    "\\n\\n### 💡 여행 계획 제안\\n공통 취향이 있는 활동을 일정의 중심에 두고, 가족별로 선호하는 활동을 하루씩 번갈아 포함해 보세요. 이동과 휴식 시간을 충분히 두면 모두가 편안한 여행이 될 수 있어요.\\n\\n*OPENAI_API_KEY 미설정 상태이므로 기본 규칙 기반 분석입니다.*")

def card(p,people):
    tags="".join(f'<span class="pill">{t}</span>' for t in p["tags"])
    st.markdown(f'<div class="tile"><div style="font-size:2rem">{p["emoji"]}</div><h3>{p["name"]}</h3><div class="muted">{p["country"]} · {p["region"]}</div><p>{p["desc"]}</p>{tags}<p style="color:#9edcff;margin-top:.7rem">가족 취향 매칭도 <b>{score(p,people)}%</b></p></div>',unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 🧭 FAMILY TRIP")
    st.caption("우리 가족의 취향을 모아 떠나는 여행")
    page=st.session_state.get("page","여행 홈")
    code=st.session_state.get("room_code","")
    if code and room(code):
        st.success(f"참여 중: {room(code)['name']}")
        st.code(code)
        st.caption(f"가족 {len(members(code))}명")
    else: st.info("먼저 여행방을 만들거나 참여하세요.")
    app_url=st.secrets.get("APP_URL",os.getenv("APP_URL",""))
    if app_url:
        with st.expander("📱 QR 코드 초대"):
            st.image(qrcode.make(app_url),width=180)
            st.code(app_url)

page=st.radio("바로가기",["여행 홈","① 취향 등록","② 가족 취향 분석","③ 여행지 탐색·투표","④ 투표 결과"],horizontal=True,label_visibility="collapsed",key="page")
st.markdown('<div style="display:flex;align-items:center;gap:.65rem;margin:.15rem 0 .75rem"><span style="font-size:1.75rem">🧭</span><span style="font-size:1.45rem;font-weight:800;letter-spacing:-.05em;color:#17212b">가족 여행 탐험대</span><span style="margin-left:auto;font-size:.8rem;color:#03a94b;font-weight:700">우리 가족 여행 플랫폼</span></div>',unsafe_allow_html=True)
st.markdown('<div class="hero"><h1>우리 가족의 다음 여행, 함께 골라봐요</h1><p>취향을 모으고, 여행지를 둘러보고, 가족 모두의 선택으로 목적지를 정해 보세요.</p></div>',unsafe_allow_html=True)
code=st.session_state.get("room_code","")
def need_room():
    if not code or not room(code):
        st.warning("여행 홈에서 여행방을 만들거나 6자리 코드로 참여해 주세요."); return False
    return True

if page=="여행 홈":
    a,b=st.columns(2)
    with a:
        st.markdown("### ✨ 여행방 시작하기")
        name=st.text_input("여행방 이름",placeholder="예: 2026 여름 가족 여행")
        if st.button("새 여행방 만들기",use_container_width=True):
            if name.strip():
                st.session_state.room_code=new_room(name.strip()); st.success("여행방 생성 완료! 가족에게 코드를 공유하세요."); st.rerun()
            else:st.error("여행방 이름을 입력해 주세요.")
        st.markdown("---")
        st.markdown("### 🔑 기존 여행방 참여")
        join=st.text_input("가족에게 받은 6자리 코드",max_chars=6)
        if st.button("여행방 참여",use_container_width=True):
            if room(join.strip()):st.session_state.room_code=join.strip();st.success("참여했습니다.");st.rerun()
            else:st.error("해당 여행방을 찾을 수 없습니다.")
    with b:
        st.markdown("### 🚀 이렇게 이용해요")
        for n,t,d in [("01","취향 등록","가족별로 좋아하는 여행 스타일 선택"),("02","취향 분석","그래프와 AI로 공통점·차이점 확인"),("03","여행지 투표","가고 싶은 여행지에 한 표 행사"),("04","최종 결과","가족 투표 1위 여행지 확인")]:
            st.markdown(f'<div class="tile"><b style="color:#7dd3fc">{n} · {t}</b><br><span class="muted">{d}</span></div>',unsafe_allow_html=True)
        st.info("가족 모두 같은 앱 주소와 여행방 코드를 사용하면 됩니다.")

elif page=="① 취향 등록":
    st.subheader("1. 좋아하는 여행 스타일을 선택해요")
    if need_room():
        people=members(code); names=[p["name"] for p in people]
        name=st.text_input("가족 구성원 이름",placeholder="예: 엄마, 아빠, 민준")
        prefs=st.multiselect("좋아하는 여행 스타일 (여러 개 선택 가능)",STYLES)
        if st.button("취향 저장하기",type="primary",use_container_width=True):
            if not name.strip():st.error("이름을 입력해 주세요.")
            elif not prefs:st.error("여행 스타일을 한 개 이상 선택해 주세요.")
            else:save_member(code,name.strip(),prefs);st.success(f"{name}님의 취향을 저장했어요.");st.rerun()
        st.divider();st.markdown("### 등록된 가족 구성원")
        if people:
            for p in people:st.markdown(f"**{p['name']}** · "+" / ".join(p["prefs"]))
        else:st.info("아직 등록된 가족이 없습니다.")

elif page=="② 가족 취향 분석":
    st.subheader("2. 가족 구성원별 취향을 비교해요")
    if need_room():
        people=members(code)
        if not people:st.info("먼저 취향을 등록해 주세요.")
        else:
            rows=[{"가족":p["name"],"스타일":s,"선택":int(s in p["prefs"])} for p in people for s in STYLES]
            matrix=pd.DataFrame(rows).pivot(index="가족",columns="스타일",values="선택")
            x,y=st.columns(2)
            with x:
                st.markdown("### 가족별 취향")
                f=px.imshow(matrix,color_continuous_scale=["#13263d","#38bdf8"],aspect="auto")
                f.update_layout(template="plotly_dark",paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",height=350)
                st.plotly_chart(f,use_container_width=True)
            with y:
                st.markdown("### 공통 취향 분포")
                dist=pd.DataFrame([{"여행 스타일":s,"가족 수":sum(s in p["prefs"] for p in people)} for s in STYLES])
                f=px.bar(dist[dist["가족 수"]>0],x="여행 스타일",y="가족 수",color="가족 수",color_continuous_scale="Blues")
                f.update_layout(template="plotly_dark",paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",height=350)
                st.plotly_chart(f,use_container_width=True)
            common=[s for s in STYLES if all(s in p["prefs"] for p in people)]
            st.metric("가족 구성원 수",f"{len(people)}명")
            st.info("모두의 공통 취향: "+(", ".join(common) if common else "아직 없어요. 서로 다른 취향을 조합해 보세요."))
            if st.button("✨ AI 가족 취향 분석",type="primary",use_container_width=True):
                with st.spinner("가족 취향을 분석하고 있어요..."):st.session_state.ai_text=analyze(people)
            if st.session_state.get("ai_text"):
                st.markdown('<div class="tile">',unsafe_allow_html=True);st.markdown(st.session_state.ai_text);st.markdown("</div>",unsafe_allow_html=True)

elif page=="③ 여행지 탐색·투표":
    st.subheader("3. 가고 싶은 여행지를 찾아 투표해요")
    if need_room():
        people=members(code)
        if not people:st.info("먼저 가족 취향을 등록해 주세요.")
        else:
            region=st.selectbox("여행 지역",["전체","국내","해외"])
            keyword=st.text_input("여행지 검색",placeholder="예: 제주, 바다, 도쿄")
            places=[p.copy() for p in PLACES if region=="전체" or p["region"]==region]
            if keyword.strip():
                places=[p for p in places if keyword.lower() in (p["name"]+p["country"]+p["desc"]).lower()]
                if region in ("전체","국내"):
                    known={p["name"] for p in places}
                    places += [p for p in live_domestic(keyword.strip()) if p["name"] not in known]
            places.sort(key=lambda p:score(p,people),reverse=True)
            if not places:st.warning("검색 결과가 없습니다. 다른 검색어를 입력해 보세요.")
            else:
                st.caption(f"여행지 {len(places)}곳 · 취향 매칭도 순으로 표시")
                cols=st.columns(2)
                for i,p in enumerate(places):
                    with cols[i%2]:
                        card(p,people)
                        with st.expander(f"{p['name']}에 투표하기"):
                            voter=st.selectbox("투표하는 가족 구성원",[m["name"] for m in people],key=f"person{i}")
                            if st.button(f"🗳️ 이곳에 투표",key=f"vote{i}",use_container_width=True):
                                cast_vote(code,voter,p["name"]);st.success(f"{voter}님의 투표를 저장했어요.");st.rerun()
                current=votes(code)
                if current:
                    st.markdown("### 현재 투표 현황")
                    st.dataframe(pd.DataFrame(current).rename(columns={"member":"가족 구성원","dest":"선택한 여행지"}),use_container_width=True,hide_index=True)
                st.caption("가족 구성원별 한 표이며, 다시 투표하면 이전 선택이 변경됩니다.")

elif page=="④ 투표 결과":
    st.subheader("4. 우리 가족의 최종 여행지를 확인해요")
    if need_room():
        people=members(code); current=votes(code)
        if not current:st.info("아직 투표가 없습니다. 여행지 탐색 메뉴에서 투표해 주세요.")
        else:
            df=pd.DataFrame(current)
            result=df["dest"].value_counts().rename_axis("여행지").reset_index(name="득표수")
            result["취향 매칭도"]=result["여행지"].apply(lambda n:next((score(p,people) for p in PLACES if p["name"]==n),0))
            result=result.sort_values(["득표수","취향 매칭도"],ascending=False)
            winner=result.iloc[0]
            a,b,c=st.columns(3);a.metric("전체 가족",f"{len(people)}명");b.metric("투표 완료",f"{len(current)}명");c.metric("현재 1위",winner["여행지"])
            st.markdown(f'<div class="hero" style="text-align:center"><div style="font-size:3rem">🏆</div><h1>{winner["여행지"]}</h1><p>가장 많은 선택을 받은 여행지 · {int(winner["득표수"])}표</p></div>',unsafe_allow_html=True)
            f=px.bar(result,x="여행지",y="득표수",text="득표수",color="득표수",color_continuous_scale="Blues")
            f.update_layout(template="plotly_dark",paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",height=350)
            st.plotly_chart(f,use_container_width=True)
            st.markdown("### 투표 상세 결과")
            st.dataframe(result,use_container_width=True,hide_index=True)
            st.dataframe(df.rename(columns={"member":"가족 구성원","dest":"투표한 여행지"}),use_container_width=True,hide_index=True)
            missing=sorted(set(p["name"] for p in people)-set(v["member"] for v in current))
            if missing:st.warning("아직 투표하지 않은 가족: "+", ".join(missing))
            else:st.success("모든 가족이 투표를 완료했어요!")

st.divider()
st.caption("가족 여행 탐험대 · OPENAI_API_KEY 설정 시 AI 분석, TOUR_API_KEY 설정 시 한국관광공사 TourAPI 국내 관광지 검색을 사용할 수 있습니다.")
st.caption("운영 참고: 기본 SQLite 데이터는 앱 서버 파일에 저장되며 Streamlit Cloud 재시작·재배포 시 초기화될 수 있습니다. 장기 사용에는 Supabase 등 외부 DB를 권장합니다. 투표자 이름 선택은 본인 인증이 아닙니다.")
