# db/Redis.py
import os
import time
import redis
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")

# ------------------------------------------------------------------------------
# Creación del cliente Redis (compatible con redis-py 7.x)
# ------------------------------------------------------------------------------
def create_redis_client():
    """
    Crea un cliente Redis con parámetros compatibles y seguros.
    Retorna None si la URL no está definida o si ocurre un error crítico.
    """
    if not REDIS_URL:
        print("❌ REDIS_URL no está definida en el entorno.")
        return None

    try:
        client = redis.Redis.from_url(
            REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=10,     # tiempo para establecer conexión (incluye DNS)
            socket_timeout=10,             # timeout por operación (get/set)
            socket_keepalive=True,         # TCP keepalive (mejora detección de caídas)
            retry_on_timeout=True,         # reintentar operaciones si hay timeout
            health_check_interval=30,      # PING automático cada 30 segundos
        )
        return client
    except Exception as e:
        print(f"❌ Error al crear el cliente Redis: {e}")
        return None

# ------------------------------------------------------------------------------
# Instancia global (puede ser None si falla la creación)
# ------------------------------------------------------------------------------
r = create_redis_client()

# ------------------------------------------------------------------------------
# Verificación de conexión con reintentos (útil durante el arranque)
# ------------------------------------------------------------------------------
def check_redis_connection(max_retries: int = 5, delay: float = 2.0) -> bool:
    """
    Intenta hacer ping a Redis hasta `max_retries` veces.
    Retorna True si la conexión es exitosa, False en caso contrario.
    """
    if r is None:
        print("Cliente Redis no disponible")
        return False

    for attempt in range(1, max_retries + 1):
        try:
            r.ping()
            # Operación de prueba (la clave expira en 60 segundos)
            r.set("Base REDIS", "Conectada", ex=60)
            test_value = r.get("Base REDIS")
            print(f"Redis conectado (intento {attempt}) - valor: {test_value}")
            return True
        except redis.exceptions.ConnectionError as e:
            print(f"Falló ping a Redis (intento {attempt}/{max_retries}): {e}")
            if attempt < max_retries:
                time.sleep(delay)
                delay *= 1.5   # backoff exponencial
        except Exception as e:
            print(f" Error inesperado en Redis: {e}")
            return False

    print(" No se pudo conectar a Redis después de varios reintentos.")
    return False

# ------------------------------------------------------------------------------
# Prueba rápida si se ejecuta el módulo directamente
# ------------------------------------------------------------------------------
if __name__ == "__main__":
    check_redis_connection()