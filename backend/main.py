from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.database import engine, Base
from app.modules.telemetry.router import router as telemetry_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Tự động tạo các bảng CSDL khi khởi động (nếu chưa có)
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="AI Smart Soil System API",
    description="Hệ thống tiếp nhận dữ liệu cảm biến đất 7-in-1 thời gian thực từ ESP32 (nongthinh.vn)",
    version="1.0.0",
    lifespan=lifespan
)

# Cấu hình CORS để Web Dashboard và Mobile App truy cập được
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký router telemetry
app.include_router(telemetry_router, prefix="/api/v1")

@app.get("/", tags=["General"])
def root():
    return {
        "status": "online",
        "service": "AI Smart Soil System API",
        "version": "1.0.0",
        "docs_url": "/docs"
    }

@app.get("/health", tags=["General"])
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
