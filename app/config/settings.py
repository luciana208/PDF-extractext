from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    app_name: str = "PDF Extractext"
    debug: bool = False
    mongo_url: str = Field("mongodb://localhost:27017", env="MONGO_URL")
    db_name: str = Field("pdf_extraction_db", env="DB_NAME")
    max_pdf_size_mb: int = Field(10, env="MAX_PDF_SIZE_MB")
    default_page_size: int = Field(20, env="DEFAULT_PAGE_SIZE")
    max_page_size: int = Field(100, env="MAX_PAGE_SIZE")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def max_pdf_size_bytes(self) -> int:
        return self.max_pdf_size_mb * 1024 * 1024

    # Backwards-compatible property aliases (may be accessed as settings.MONGO_URL etc.)
    @property
    def MONGO_URL(self) -> str:  # pragma: no cover - trivial alias
        return self.mongo_url

    @property
    def DB_NAME(self) -> str:  # pragma: no cover - trivial alias
        return self.db_name

    @property
    def MAX_PDF_SIZE_MB(self) -> int:  # pragma: no cover - trivial alias
        return self.max_pdf_size_mb

    @property
    def MAX_PDF_SIZE_BYTES(self) -> int:  # pragma: no cover - trivial alias
        return self.max_pdf_size_bytes

    @property
    def DEFAULT_PAGE_SIZE(self) -> int:  # pragma: no cover - trivial alias
        return self.default_page_size

    @property
    def MAX_PAGE_SIZE(self) -> int:  # pragma: no cover - trivial alias
        return self.max_page_size


settings = Settings()