from fastapi import FastAPI
from contextlib import asynccontextmanager

from src.routers.news_agent import router as news_agent_router
from src.routers.scrap_agent import router as scrap_agent_router
from src.routers.users import router as user_router
from src.routers.ocr_agent import router as ocr_agent_router
from src.routers.signup import router as signup_router
from src.routers.rag_agent import router as rag_agent_router
from src.routers.contexts import router as context_router
from src.models.models import Base
from src.routers.auth_route import router as auth_router
from src.services.db_connection import engine
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

@asynccontextmanager
async def lifespan(app:FastAPI):
    _ = app
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            print("Tablas de usuarios creadas o verificadas correctamente")
    except Exception as e:
            print(f"Error al crear las tablas de usuarios: {e}")
    yield

app = FastAPI(title="Sistema de Agentes Inteligentes Petroil",version="0.1",lifespan=lifespan)

app.include_router(news_agent_router,prefix="/newsagent",tags=["Agents"])
app.include_router(scrap_agent_router,prefix="/scrapagent",tags=["Agents"])
app.include_router(ocr_agent_router, prefix="/ocragent", tags=["Agents"])
app.include_router(user_router,tags=["User"])
app.include_router(auth_router,tags=["Auth"])
app.include_router(signup_router, prefix="/signup",tags=["Sign-Up"])
app.include_router(rag_agent_router, prefix="/ragagent", tags=["Agents"])
app.include_router(context_router,tags=["Context"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://agent-alchemy-front.vercel.app",
        "http://localhost",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
    allow_credentials=True    
)


@app.get("/")
def init_page():
    """
        Punto de entrada para el backend.
        Determina si el servicio está Online.
    """    
    return {"message":"La plataforma de SAIP se encuentra operativa."}

@app.get("/health")
def health_check():
    return {"message":"Agente Operativo"}