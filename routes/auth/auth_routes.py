from flask import Blueprint, request, jsonify
from routes.auth import auth_controller

auth_bp = Blueprint("auth_bp", __name__)


@auth_bp.route("/login", methods=["POST"])
def loginUser():
    if request.method == "OPTIONS":
        return jsonify({}), 200
    return auth_controller.loginUser(request.get_json() or {})

@auth_bp.route("/create", methods=["POST"]) #para crear el user
def createUser():
    return auth_controller.createUser(request.get_json() or {})
