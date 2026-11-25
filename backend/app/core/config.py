import os


class Settings:
    PROJECT_NAME: str = "AI Smart Soil System"
    API_V1_STR: str = "/api/v1"

    # Kho lưu trữ chính (Primary Storage) cho dữ liệu lớn:
    # - MySQL:      mysql+pymysql://user:password@host:3306/smart_soil_db
    # - SQL Server: mssql+pyodbc://user:password@host:1433/smart_soil_db?driver=ODBC+Driver+17+for+SQL+Server
    # - PostgreSQL: postgresql+psycopg2://user:password@host:5432/smart_soil_db
    # Nếu chưa cấu hình DB server ngoài, mặc định fallback về SQLite cục bộ
    PRIMARY_DB_URL: str = os.getenv("PRIMARY_DB_URL") or os.getenv("DATABASE_URL", "")

    # Kho lưu trữ phụ (Secondary / Offline Storage) khi mất mạng hoặc mất kết nối DB chính
    OFFLINE_SQLITE_URL: str = os.getenv("OFFLINE_SQLITE_URL", "sqlite:///./soil_system.db")

    @property
    def DATABASE_URL(self) -> str:
        return self.PRIMARY_DB_URL or self.OFFLINE_SQLITE_URL

    @property
    def PRIMARY_ENGINE_TYPE(self) -> str:
        url = self.DATABASE_URL.lower()
        if url.startswith("mysql"):
            return "MySQL"
        if url.startswith("mssql"):
            return "SQL Server"
        if url.startswith("postgresql") or url.startswith("postgres"):
            return "PostgreSQL"
        return "SQLite (Local Fallback)"


settings = Settings()
