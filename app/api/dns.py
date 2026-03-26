from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

# 1. 상대 경로(.) 대신 절대 경로(app.)를 사용하는 것이 가장 안전합니다.
from app.db.database import get_db
from app.db import models
from app.schemas import dns as dns_schema  # app/schemas/dns.py를 가져옴
from app.core.security import get_current_user
from app.services import cloudflare

# 2. 이 라우터 객체가 반드시 정의되어 있어야 main.py에서 인식합니다!
router = APIRouter()

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_ # CNAME 체크를 위해 필요

# 금지된 서브도메인 리스트 (시스템 보호용)
FORBIDDEN_SUBDOMAINS = [
    # 1. 시스템 및 기술 관련 (가장 중요)
    'admin', 'administrator', 'root', 'webmaster', 'postmaster', 'hostmaster',
    'www', 'www1', 'www2', 'ftp', 'ssh', 'smtp', 'pop', 'imap', 'mx', 'ns', 'ns1', 'ns2',
    'api', 'cdn', 'static', 'assets', 'media', 'img', 'images', 'video', 'cloud',
    'status', 'health', 'monitor', 'sql', 'db', 'database', 'git', 'svn', 'webhook', '@',

    # 2. 서비스 운영 및 지원
    'support', 'help', 'contact', 'info', 'service', 'mail', 'email', 'billing',
    'account', 'profile', 'login', 'signin', 'signup', 'register', 'auth', 'oauth',
    'legal', 'privacy', 'terms', 'security', 'abuse', 'jobs', 'careers', 'about',

    # 3. 개발 및 테스트
    'dev', 'development', 'staging', 'stage', 'prod', 'production', 'test', 'testing',
    'beta', 'alpha', 'demo', 'example', 'docs', 'documentation', 'wiki', 'blog',

    # 4. 비즈니스 및 마케팅
    'shop', 'store', 'market', 'mall', 'pay', 'payment', 'order', 'cart',
    'app', 'mobile', 'ios', 'android', 'portal', 'community', 'forum', 'news', 'press',

    # 5. 내 서비스 이름 관련 (본인용)
    'decodns', 'deco', 'dns', 'manager', 'dashboard', 'console'
]
@router.post("/register", response_model=dns_schema.DomainResponse)
def register_new_domain(
    domain: dns_schema.DomainCreate, 
    current_user: str = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    # 1. 관리자 여부 확인 (ruddls030 계정인지 체크)
    is_admin = (current_user == "ruddls030")

    # 2. 금지된 서브도메인 체크 (관리자가 아닐 때만 작동)
    sub_lower = domain.subdomain.lower()
    if not is_admin and sub_lower in FORBIDDEN_SUBDOMAINS:
        raise HTTPException(
            status_code=400, 
            detail=f"'{domain.subdomain}'은(는) 사용할수 없는 도메인입니다."
        )

    # 3. 유저 정보 가져오기
    user = db.query(models.User).filter(models.User.username == current_user).first()
    
    # 4. DNS 규칙 및 중복 체크
    # [A] 같은 이름 + 같은 타입이 이미 있는지 확인
    duplicate = db.query(models.Domain).filter(
        models.Domain.subdomain == domain.subdomain,
        models.Domain.type == domain.type
    ).first()
    
    if duplicate:
        raise HTTPException(status_code=400, detail=f"이미 '{domain.type}' 타입으로 등록된 주소입니다.")

    # [B] CNAME 충돌 체크 (CNAME은 다른 레코드와 공존 불가)
    existing_records = db.query(models.Domain).filter(models.Domain.subdomain == domain.subdomain).all()
    if existing_records:
        is_new_cname = (domain.type == "CNAME")
        has_existing_cname = any(r.type == "CNAME" for r in existing_records)
        
        if is_new_cname or has_existing_cname:
            raise HTTPException(
                status_code=400, 
                detail="CNAME 레코드는 동일한 이름의 다른 레코드와 함께 사용할 수 없습니다."
            )

    # 5. Cloudflare API 호출
    cf_res = cloudflare.add_dns_record(
        subdomain=domain.subdomain, 
        record_type=domain.type,
        content=domain.content,
        priority=domain.priority
    )
    
    # Cloudflare 에러 처리
    if not cf_res.get("success"):
        error_msg = cf_res['errors'][0]['message'] if cf_res.get('errors') else "Cloudflare 등록 실패"
        raise HTTPException(status_code=400, detail=error_msg)

    # 6. Cloudflare 발급 ID 가져오기
    cf_record_id = cf_res.get("result", {}).get("id")

    # 7. DB 저장
    new_domain = models.Domain(
        subdomain=domain.subdomain,
        type=domain.type,
        content=domain.content,
        priority=domain.priority,
        cloudflare_id=cf_record_id, 
        owner_id=user.id
    )
    
    db.add(new_domain)
    db.commit()
    db.refresh(new_domain)
    
    return new_domain
# 2. 삭제 로직 추가
@router.delete("/{domain_id}")
def delete_domain(domain_id: int, current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    # DB에서 해당 도메인 찾기
    domain = db.query(models.Domain).filter(models.Domain.id == domain_id).first()
    if not domain:
        raise HTTPException(status_code=404, detail="도메인을 찾을 수 없습니다.")
    
    # 소유권 확인 (본인 것만 삭제 가능)
    user = db.query(models.User).filter(models.User.username == current_user).first()
    if domain.owner_id != user.id:
        raise HTTPException(status_code=403, detail="삭제 권한이 없습니다.")

    # Cloudflare에서 삭제
    cf_res = cloudflare.delete_dns_record(domain.cloudflare_id)
    
    # DB에서 삭제
    db.delete(domain)
    db.commit()
    return {"message": "삭제 완료"}

@router.put("/{domain_id}")
def update_domain(domain_id: int, data: dns_schema.DomainUpdate, current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    domain = db.query(models.Domain).filter(models.Domain.id == domain_id).first()
    # 소유권 확인 로직 (생략 - 기존 삭제 로직과 동일)
    print(domain.cloudflare_id, data.subdomain, data.type, data.content, data.priority)
    
    # 1. Cloudflare 업데이트
    cf_res = cloudflare.update_dns_record(
        domain.cloudflare_id, data.subdomain, data.type, data.content, data.priority
    )
    
    if not cf_res.get("success"):
        raise HTTPException(status_code=400, detail="Cloudflare 동기화 실패")

    # 2. DB 업데이트
    domain.subdomain = data.subdomain
    domain.type = data.type
    domain.content = data.content
    domain.priority = data.priority
    db.commit()
    
    return {"message": "수정 완료"}

@router.get("/my-domains")
def list_my_domains(current_user: str = Depends(get_current_user), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == current_user).first()
    domains = db.query(models.Domain).filter(models.Domain.owner_id == user.id).all()
    return domains