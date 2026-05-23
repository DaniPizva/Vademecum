# db/db.py
import os
import socket
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.pool import QueuePool   # ← Pool de conexiones real

load_dotenv()

DATABASE_URL = os.getenv("DB_URL")

# ============================================================================
# CONFIGURACIÓN AVANZADA DEL MOTOR [Producida por deepseek]
# ============================================================================

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,               # 1. Reutiliza conexiones
    pool_size=5,                       # 2. Conexiones fijas abiertas
    max_overflow=10,                   # 3. Conexiones extra bajo demanda
    pool_pre_ping=True,                # 4. Verifica integridad antes de usar
    pool_recycle=3600,                 # 5. Recicla cada hora (evita timeouts del lado del servidor)
    pool_use_lifo=True,                # 6. Última conexión usada primero (mejor para long-lived)
    echo=False,                        # 7. No loguear SQL (para producción)
    future=True,                       # 8. Usa la nueva API de SQLAlchemy 2.0
    connect_args={
        'connect_timeout': 30,         # 9. Timeout de conexión TCP (segundos)
        'keepalives': 1,               # 10. Activa keepalive TCP
        'keepalives_idle': 30,         # 11. Envía primer keepalive a los 30 segundos inactivos
        'keepalives_interval': 10,     # 12. Intervalo entre keepalives si no hay respuesta
        'keepalives_count': 5,         # 13. Número de keepalives antes de declarar la conexión muerta
        'tcp_user_timeout': 30000,     # 14. Timeout en milisegundos para datos no confirmados (30 segundos)
        'options': '-c timezone=UTC'   # 15. Parámetro adicional para PostgreSQL
    }
)

# ============================================================================
# Configuración de sesiones
# ============================================================================

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

Base = declarative_base()

print("Motor de base de datos inicializado y en linea")