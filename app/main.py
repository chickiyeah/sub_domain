from datetime import datetime

from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

# 우리가 만든 모듈들 (절대 경로로 통일하여 에러 방지)
from app.db.database import engine, Base
from app.api import auth, dns

# 1. 데이터베이스 테이블 생성 (앱 시작 시 자동 실행)
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="DecoDNS Professional",
    description="나만의 세련된 서브도메인 분양 서비스",
    version="1.0.0"
)

# --- [미들웨어 설정] ---

# 2. NPM(HTTPS 프록시) 헤더 신뢰 설정
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts="*")

# 3. CORS 설정 (프론트엔드와 백엔드 간의 원활한 통신을 위해)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 실제 운영 시엔 ["https://decodns.org"] 로 제한 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- [정적 파일 및 템플릿 설정] ---

# 4. /static 경로로 들어오는 요청을 실제 static 폴더와 연결
app.mount("/static", StaticFiles(directory="static"), name="static")

# 5. HTML 템플릿 폴더 지정 (Jinja2)
templates = Jinja2Templates(directory="templates")

# --- [라우터 등록] ---

# 6. 기능별로 분리한 API 라우터 연결
app.include_router(auth.router, prefix="/auth", tags=["인증 (Auth)"])
app.include_router(dns.router, prefix="/dns", tags=["DNS 관리"])

@app.get("/sitemap.xml")
def get_sitemap():
    # 현재 날짜 (2026-03-26 기준)
    today = datetime.now().strftime("%Y-%m-%d")
    
    # 이미지에서 확인된 실제 도메인 적용
    pages = [
        {
            "loc": "https://decodns.org/", 
            "lastmod": today, 
            "changefreq": "daily", 
            "priority": "1.0"
        },
        # 추가적인 페이지가 있다면 아래에 더 넣어주면 됩니다.
        # {
        #     "loc": "https://decodns.org/service", 
        #     "lastmod": today, 
        #     "changefreq": "weekly", 
        #     "priority": "0.8"
        # },
    ]

    # XML 문자열 생성
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    for page in pages:
        xml_content += f'''  <url>
    <loc>{page["loc"]}</loc>
    <lastmod>{page["lastmod"]}</lastmod>
    <changefreq>{page["changefreq"]}</changefreq>
    <priority>{page["priority"]}</priority>
  </url>\n'''
    
    xml_content += '</urlset>'

    return Response(content=xml_content, media_type="application/xml")

# 보너스: robots.txt도 추가해서 검색 로봇에게 사이트맵 위치 알리기
@app.get("/robots.txt")
def get_robots():
    content = "User-agent: *\nAllow: /\nSitemap: https://decodns.org/sitemap.xml"
    return Response(content=content, media_type="text/plain")
# --- [페이지 렌더링 경로] ---

@app.get("/", response_class=None)
async def home(request: Request):
    """메인 로그인/회원가입 페이지"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/dashboard")
async def dashboard_page(request: Request):
    """로그인 후 도메인을 관리하는 대시보드 페이지"""
    return templates.TemplateResponse("dashboard.html", {"request": request})
