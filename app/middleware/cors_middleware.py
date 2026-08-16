from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings

def setup_cors(app):
    if settings.ENVIRONMENT == "development":
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=True,  # ✅ must be False with "*"
            allow_methods=["*"],
            allow_headers=["*"],
        )
    else:
        # Production — origins come from ALLOWED_ORIGINS env var
        app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.CORS_ORIGINS,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
            expose_headers=["X-Request-ID"],
        )