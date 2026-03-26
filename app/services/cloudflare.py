import requests
from app.core.config import settings

def add_dns_record(subdomain: str, record_type: str, content: str, priority: int = None):
    # 이제 priority를 인자로 받습니다! (기본값은 None)
    
    url = f"https://api.cloudflare.com/client/v4/zones/{settings.CF_ZONE_ID}/dns_records"
    headers = {
        "Authorization": f"Bearer {settings.CF_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # 1. 기본 데이터 구성
    payload = {
        "type": record_type,
        "name": f"{subdomain}.{settings.DOMAIN_NAME}",
        "content": content,
        "proxied": record_type in ["A", "AAAA", "CNAME"]  # TXT, MX는 프록시 불가
    }
    
    # 2. MX 레코드일 경우에만 우선순위(priority) 추가
    if record_type == "MX" and priority is not None:
        payload["priority"] = priority

    response = requests.post(url, json=payload, headers=headers)
    return response.json()

def update_dns_record(record_id: str, subdomain: str, record_type: str, content: str, priority: int = None):
    url = f"https://api.cloudflare.com/client/v4/zones/{settings.CF_ZONE_ID}/dns_records/{record_id}"
    headers = {
        "Authorization": f"Bearer {settings.CF_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "type": record_type,
        "name": f"{subdomain}.{settings.DOMAIN_NAME}",
        "content": content,
        "proxied": record_type in ["A", "AAAA", "CNAME"]
    }
    if record_type == "MX" and priority is not None:
        payload["priority"] = priority

    response = requests.put(url, json=payload, headers=headers)
    return response.json()

def delete_dns_record(record_id: str):
    url = f"https://api.cloudflare.com/client/v4/zones/{settings.CF_ZONE_ID}/dns_records/{record_id}"
    headers = {
        "Authorization": f"Bearer {settings.CF_API_TOKEN}",
        "Content-Type": "application/json"
    }
    response = requests.delete(url, headers=headers)
    return response.json()