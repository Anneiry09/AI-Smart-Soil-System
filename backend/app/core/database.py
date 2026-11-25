from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings


def _create_db_engine(db_url: str):
    is_sqlite = db_url.startswith("sqlite")
    if is_sqlite:
        eng = create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            echo=False,
        )

        @event.listens_for(eng, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL;")
            cursor.execute("PRAGMA synchronous=NORMAL;")
            cursor.close()

        return eng

    # Cấu hình connection pool tối ưu cho MySQL / SQL Server / PostgreSQL
    return create_engine(
        db_url,
        pool_pre_ping=True,
        pool_recycle=3600,
        pool_size=10,
        max_overflow=20,
        echo=False,
    )


def _init_primary_or_fallback():
    """
    Thử kết nối Kho lưu trữ chính (MySQL / SQL Server / PostgreSQL).
    Nếu chưa cấu hình hoặc mất kết nối mạng tới DB chính, tự động chuyển sang SQLite lưu trữ phụ.
    """
    primary_url = settings.PRIMARY_DB_URL
    if primary_url and not primary_url.startswith("sqlite"):
        try:
            eng = _create_db_engine(primary_url)
            with eng.connect() as conn:
                conn.execute(text("SELECT 1"))
            return eng, settings.PRIMARY_ENGINE_TYPE, False
        except Exception as exc:
            print(f"[Storage Warning] Không thể kết nối Primary DB ({settings.PRIMARY_ENGINE_TYPE}): {exc}")
            print("[Storage Fallback] Chuyển sang lưu trữ phụ SQLite cục bộ.")

    fallback_eng = _create_db_engine(settings.OFFLINE_SQLITE_URL)
    mode_label = "SQLite (Offline/Local Fallback)" if primary_url else "SQLite (Local Storage - Chưa cấu hình MySQL/SQL Server)"
    return fallback_eng, mode_label, True


engine, active_storage_backend, is_using_sqlite_fallback = _init_primary_or_fallback()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_storage_info():
    return {
        "active_primary_backend": active_storage_backend,
        "is_sqlite_fallback": is_using_sqlite_fallback,
        "configured_primary_engine": settings.PRIMARY_ENGINE_TYPE,
        "offline_secondary_storage": "SQLite WAL (offline_buffer.db)",
    }
