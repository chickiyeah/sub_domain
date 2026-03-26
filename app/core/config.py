from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    # .env 파일의 변수명과 일치해야 함
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440
    
    DATABASE_URL: str
    
    CF_API_TOKEN: str
    CF_ZONE_ID: str
    DOMAIN_NAME: str

    # .env 파일을 읽어오기 위한 설정
    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()