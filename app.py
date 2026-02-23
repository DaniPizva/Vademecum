import os
from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv

##indicar rutas de acceso a Routes
from routes.Therapeutic_group.Therapeutic_group_routes import Therapeutic_group_bp
from routes.descriptions.descriptions_routes import descriptions_bp

def run_app():
    load_dotenv()
    app = Flask(__name__)
    CORS(
        resources= {r"/*": {"origins": "*"}},
        supports_credentials= False,
        expose_headers=["Authorization"],
        allow_headers=["Content-Type", "Authorization"],
        methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"]
    )
    ## registrar rutas creadas en routes
    app.register_blueprint(Therapeutic_group_bp, url_prefix="/Therapeutic_group")
    app.register_blueprint(descriptions_bp, url_prefix="/descriptions")
    return app

app = run_app()
# 
if __name__ == "__main__":
    app.run(
        host=os.getenv("HOST", "127.0.0.1"),
        port=int(os.getenv("PORT", 5000)),
        debug=True
    )
