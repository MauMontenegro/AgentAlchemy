from fastapi import FastAPI
from src.routers.news_agent import router as news_agent_router
from src.routers.scrap_agent import router as scrap_agent_router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Sistema de Agentes Inteligentes Petroil",version="0.1")

app.include_router(news_agent_router,prefix="/newsagent",tags=["Agents"])
app.include_router(scrap_agent_router,prefix="/scrapagent",tags=["Agents"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://agent-alchemy-front.vercel.app"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def init_page():
    """
        Punto de entrada para el backend.
        Determina si el servicio está Online.
    """
    
    return {"message":"La plataforma de SAIP se encuentra operativa."}