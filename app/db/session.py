
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.config.settings import settings

engine = create_engine(
    settings.database_url,
    connect_args={
        "client_encoding": "utf8",
        "options": "-c client_encoding=utf8"
    },
    echo=False
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()