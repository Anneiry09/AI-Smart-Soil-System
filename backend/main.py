import os
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.database import engine, Base
from app.modules.telemetry.router import router as telemetry_router
from app.modules.soil_ai.router import router as soil_ai_router
from app.modules.recommendations.router import router as approvals_router
from app.modules.farms.router import router as farms_router

TEMPLATE_PATH = os.path.join(os.path.dirname(__file__), "app", "templates", "index.html")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Tự động tạo các bảng CSDL khi khởi động (nếu chưa có)
    Base.metadata.create_all(bind=engine)
    yield

app = FastAPI(
    title="AI Smart Soil System API",
    description="Hệ thống AIoT Giám sát, Dự báo Sinh lý Đất & Điều khiển Canh tác Tự động",
    version="2.0.0",
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

# Đăng ký các router chức năng
app.include_router(telemetry_router, prefix="/api/v1")
app.include_router(soil_ai_router, prefix="/api/v1")
app.include_router(approvals_router, prefix="/api/v1")
app.include_router(farms_router, prefix="/api/v1")

@app.get("/", tags=["Dashboard"], response_class=HTMLResponse)
def root_dashboard():
    """Trang chủ bảng điều khiển toàn diện 7 phân hệ AIoT."""
    if os.path.exists(TEMPLATE_PATH):
        return FileResponse(TEMPLATE_PATH)
    return HTMLResponse("<h1>AI Smart Soil System</h1><p><a href='/docs'>Mở Swagger API Docs</a></p>")

@app.get("/api", tags=["General"])
def api_status():
    """Thông tin trạng thái API server."""
    return {
        "status": "online",
        "service": "AI Smart Soil System API",
        "version": "2.0.0",
        "modules": [
            "Telemetry Ingestion",
            "Bi-LSTM Forecasting",
            "XGBoost Root Diagnostics",
            "Fuzzy Logic Actuator Control",
            "Human-in-the-Loop AI Agent Queue",
            "Multi-Node & Crop Configuration"
        ],
        "docs_url": "/docs"
    }

@app.get("/health", tags=["General"])
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
