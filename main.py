from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.pdf_router import router as pdf_router
from routers.pdf_split_router import router as pdf_split_router
from routers.pdf_scan_split_router import router as pdf_scan_split_router
from routers.gcn_locator_router import router as gcn_locator_router
from routers.pdf_merge_router import router as pdf_merge_router
from routers.pdf_excel_router import router as pdf_excel_router

app = FastAPI(title="PDF & Excel Processing API")

# CẤU HÌNH CORS CHUẨN DÀNH CHO CẢ PORT 5173 VÀ 5174
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5174",
        "http://127.0.0.1:5174",
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "API Backend Python đang chạy rất tốt!"}

# Đăng ký router
app.include_router(pdf_router)
app.include_router(pdf_split_router)
app.include_router(pdf_scan_split_router)
app.include_router(gcn_locator_router)
app.include_router(pdf_merge_router)
app.include_router(pdf_excel_router)