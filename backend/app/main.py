# backend/app/main.py
from fastapi import FastAPI, File, UploadFile, Form, Depends
from fastapi.middleware.cors import CORSMiddleware
from .analyze import analyze_image
from .auth import router as auth_router
from .dependencies import get_current_user  # we’ll create this next

app = FastAPI(title="Social Privacy Audit API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # later change to your Vercel URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)


@app.post("/analyze")
async def analyze(
    file: UploadFile = File(...),
    caption: str = Form(None),
    current_user: str = Depends(get_current_user)  # 🔐 protected
):
    contents = await file.read()
    report = analyze_image(contents, filename=file.filename, caption=caption)
    return {"report": report}
