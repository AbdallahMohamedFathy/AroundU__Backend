import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from ai_service.core.config import settings
from ai_service.api import chat, recommendations

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="AroundU AI Service for Chatbot and Recommendations",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(chat.router, prefix="/chat", tags=["AI Chat"])
app.include_router(recommendations.router, prefix="/recommendations", tags=["AI Recommendations"])

@app.get("/health")
async def health():
    return {"status": "ok", "service": settings.PROJECT_NAME}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.PORT)
