# app.py
import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
from flask_jwt_extended import JWTManager

##indicar rutas de acceso a Routes
from routes.Therapeutic_group.Therapeutic_group_routes import Therapeutic_group_bp
from routes.descriptions.descriptions_routes import descriptions_bp
from routes.auth.auth_routes import auth_bp
from routes.generics.generics_routes import generics_bp
from routes.laboratories.laboratories_routes import laboratories_bp
from routes.families.families_routes import families_bp
from routes.products.products_routes import products_bp
from routes.users.users_routes import users_bp

from datetime import timedelta
# eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJmcmVzaCI6ZmFsc2UsImlhdCI6MTc3NzgyMjI4NywianRpIjoiNDdmYWRhZTktMmMyZS00ZWU3LWFhOGUtZjMwZWE3NTAwYzI4IiwidHlwZSI6ImFjY2VzcyIsInN1YiI6IjEiLCJuYmYiOjE3Nzc4MjIyODcsImNzcmYiOiI2ZjMzNWU5MS02ZTgzLTRkNDAtYTA2MS0zYTE0ODZjMGQzZGMiLCJleHAiOjE3Nzc4MjMxODcsInJvbGVfaWQiOjF9.STzSvdudp8p7fCS73E-pjnTQOPR-F610pKQYBsJc-2w
def run_app():
    load_dotenv()
    app = Flask(__name__)
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=int(os.getenv("JWT_EXPIRES_MIN")))
    jwt = JWTManager(app)
    
    CORS(
        app,
        resources= {r"/*": {"origins": "*"}},
        supports_credentials= False,
        expose_headers=["Authorization"],
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        origins=["http://localhost:4200"]
    )
    ## registrar rutas creadas en routes
    app.register_blueprint(Therapeutic_group_bp, url_prefix="/Therapeutic_group")
    app.register_blueprint(descriptions_bp, url_prefix="/descriptions")
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(generics_bp, url_prefix="/generics")
    app.register_blueprint(laboratories_bp, url_prefix="/laboratories")
    app.register_blueprint(families_bp, url_prefix="/families")
    app.register_blueprint(products_bp, url_prefix="/products")
    app.register_blueprint(users_bp, url_prefix="/users")
    return app
    

app = run_app()
# 
if __name__ == "__main__":
    app.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", 5000)),
        debug=True
    )
