# app.py
import os
from flask import Flask, make_response
from flask_cors import CORS
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager
from datetime import timedelta

# Única importación de Redis
from db.Redis import r as redis_client, check_redis_connection

from routes.Therapeutic_group.Therapeutic_group_routes import Therapeutic_group_bp
from routes.descriptions.descriptions_routes import descriptions_bp
from routes.auth.auth_routes import auth_bp
from routes.generics.generics_routes import generics_bp
from routes.laboratories.laboratories_routes import laboratories_bp
from routes.families.families_routes import families_bp
from routes.products.products_routes import products_bp
from routes.users.users_routes import users_bp
from routes.PQRS.routes import pqrs_bp

def run_app():
    load_dotenv()
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(
        minutes=int(os.getenv("JWT_EXPIRES_MIN"))
    )
    jwt = JWTManager(app)

    # Asignar cliente Redis (puede ser None)
    app.redis = redis_client

    # Verificar conexión solo si el cliente existe
    if app.redis is not None:
        connected = check_redis_connection(max_retries=5, delay=2)
        if not connected:
            print(" La conexión a Redis falló. El sistema funcionará sin caché.")
            app.redis = None
        else:
            print(" Redis cliente listo y conectado.")
    else:
        print(" No se pudo crear el cliente Redis. Sistema sin caché.")

    # Configuración de CORS
    CORS(
        app,
        resources={
            r"/*": {
                "origins": [
                    "http://localhost:4200",
                    "https://frontend-test-flax.vercel.app"
                ]
            }
        },
        supports_credentials=False,
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        expose_headers=["Authorization"]
    )

    # Registro de rutas
    app.register_blueprint(Therapeutic_group_bp, url_prefix="/Therapeutic_group")
    app.register_blueprint(descriptions_bp, url_prefix="/descriptions")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(generics_bp, url_prefix="/generics")
    app.register_blueprint(laboratories_bp, url_prefix="/laboratories")
    app.register_blueprint(families_bp, url_prefix="/families")
    app.register_blueprint(products_bp, url_prefix="/products")
    app.register_blueprint(users_bp, url_prefix="/users")
    app.register_blueprint(pqrs_bp, url_prefix="/pqrs")

    return app

app = run_app()




if __name__ == "__main__":
    app.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", 5000)),
        debug=False
    )