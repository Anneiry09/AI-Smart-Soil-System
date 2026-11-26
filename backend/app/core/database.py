import os
from sqlalchemy import create_engine, event
from sqlalchemy.engine.url import make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from app.core.config import settings

# Đảm bảo thư mục cha chứa file SQLite tồn tại (nếu dùng đường dẫn file SQLite)
if "sqlite" in settings.DATABASE_URL:
    try:
        url_obj = make_url(settings.DATABASE_URL)
        if url_obj.database and url_obj.database != ":memory:":
            db_dir = os.path.dirname(os.path.abspath(url_obj.database))
            if db_dir:
                os.makedirs(db_dir, exist_ok=True)
    except Exception:
        pass

# Cấu hình engine kết nối SQLite
connect_args = {"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

# Kích hoạt WAL (Write-Ahead Logging) cho SQLite để tối ưu hóa đọc/ghi đồng thời
if "sqlite" in settings.DATABASE_URL:
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL;")
        cursor.execute("PRAGMA synchronous=NORMAL;")
        cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
