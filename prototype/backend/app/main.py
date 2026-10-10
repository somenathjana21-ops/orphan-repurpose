from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import audit, candidates, diseases, dossier, kg, literature, validation
from app.core.logging import configure_logging

configure_logging()
logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("starting_orphan_repurpose_api")
    # Initialize database tables
    try:
        from app.db.database import create_tables

        await create_tables()
        logger.info("database_tables_created")
    except Exception as e:
        logger.warning("database_init_failed", error=str(e))
    # Initialize connections, load models, etc.
    yield
    logger.info("shutting_down_orphan_repurpose_api")


app = FastAPI(
    title="OrphanRepurpose API",
    description="AI-Driven Drug Repurposing for Rare & Orphan Diseases",
    version="0.2.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Prototype only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(diseases.router, prefix="/api/v1/diseases", tags=["diseases"])
app.include_router(candidates.router, prefix="/api/v1/candidates", tags=["candidates"])
app.include_router(kg.router, prefix="/api/v1/kg", tags=["knowledge-graph"])
app.include_router(literature.router, prefix="/api/v1/literature", tags=["literature"])
app.include_router(validation.router, prefix="/api/v1/validation", tags=["validation"])
app.include_router(dossier.router, prefix="/api/v1/dossier", tags=["dossier"])
app.include_router(audit.router, prefix="/api/v1/audit", tags=["audit"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "orphan-repurpose-api"}


@app.get("/")
async def root():
    return {
        "service": "OrphanRepurpose API",
        "version": "0.2.0",
        "docs": "/docs",
        "disclaimer": "RESEARCH PROTOTYPE — Not for clinical use. Outputs require human expert validation.",
    }
