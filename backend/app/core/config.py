from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "HS Trends API"
    DATABASE_URL: str = (
        "sqlite:///./schools.db"  # Adjust this if you're using a different database
    )

    class Config:
        env_file = ".env"


settings = Settings()
