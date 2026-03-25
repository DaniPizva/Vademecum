from flask import Blueprint, request
from routes.auth import auth_controller

auth_bp = Blueprint("auth_bp", __name__)


@auth_bp.route("/loginUser", methods=["POST"])
def loginUser():
    return auth_controller.loginUser(request.get_json() or {})

@auth_bp.route("/createUser", methods=["POST"]) #para crear el user
def createUser():
    return auth_controller.createUser(request.get_json() or {})
