# sub_domain — 서브도메인 관리

**Cloudflare DNS API**를 통해 서브도메인(DNS 레코드)을 손쉽게 추가·관리하는 FastAPI 웹앱. 로그인 인증 + 웹 UI 제공.

## 기술 스택
- **백엔드**: FastAPI 0.115 + Uvicorn
- **DB**: MySQL (PyMySQL) + SQLAlchemy 2.0
- **인증**: JWT (python-jose) + bcrypt (passlib)
- **DNS**: Cloudflare API (`requests`)
- **설정**: pydantic-settings + python-dotenv
- **UI**: Jinja2 템플릿 + 정적 자원

## 구조 (`app/`)
- `main.py` — FastAPI 엔트리 (라우터 등록, 정적·템플릿 마운트, ProxyHeaders/CORS)
- `api/` — 라우터 (`auth`, `dns`)
- `services/cloudflare.py` — Cloudflare DNS API 클라이언트
- `core/` — 설정 · `db/` — DB · `schemas/` — Pydantic 스키마

## 주요 기능
- **로그인/인증** (auth)
- **서브도메인 DNS 레코드 관리** (dns) — Cloudflare 통해 조회·생성·삭제

## 실행
```
pip install -r requirements.txt
uvicorn app.main:app --reload
```
`.env`에 MySQL 접속·JWT 시크릿·**Cloudflare API 토큰/Zone ID** 설정 (실제 값 커밋 금지). 운영 시 nginx 등 리버스 프록시 뒤 배포 전제(ProxyHeaders).
