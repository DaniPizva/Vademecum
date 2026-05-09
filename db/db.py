# db/db.py (Corrected & Optimized)

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import NullPool  # <--- 1. IMPORT NullPool

load_dotenv()

DATABASE_URL = os.getenv("DB_URL")

engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,          
    connect_args={
        'connect_timeout': 15   # Tiempo de conneción antes de generar error.
    },
    echo=False,
    future=True
)



SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

print("Connected to DB OK")