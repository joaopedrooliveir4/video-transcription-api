from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str

    max_retries: int
    worker_timeout: int
    max_concurrent_jobs: int
    polling_interval: int

    openai_api_key: str

    class Config:
        env_file = ".env"

    @property
    def database_url(self) -> str:
        return "postgresql://{}:{}@{}:{}/{}".format(
            self.db_user, self.db_password, self.db_host, self.db_port, self.db_name
        )

settings = Settings()