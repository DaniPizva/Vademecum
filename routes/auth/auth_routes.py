# routes\auth\auth_routes.py
from flask import Blueprint, request, jsonify
from routes.auth import auth_controller
from flask_jwt_extended import jwt_required, get_jwt_identity

auth_bp = Blueprint("auth_bp", __name__)


@auth_bp.route("/login", methods=["POST", "OPTIONS"])
def loginUser():
    if request.method == "OPTIONS":
        return jsonify({}), 200
    return auth_controller.loginUser(request.get_json() or {})


@auth_bp.route("/create", methods=["POST", "OPTIONS"])
def createUser():
    return auth_controller.createUser(request.get_json() or {})


@auth_bp.route("/accept-terms", methods=["POST", "OPTIONS"])
@jwt_required()
def acceptTerms():
    current_user_id = get_jwt_identity()
    if not current_user_id:
        return jsonify({"message": "Authentication required"}), 401
    return auth_controller.acceptTerms(int(current_user_id))


@auth_bp.route("/change-password", methods=["POST", "OPTIONS"])
@jwt_required()
def changePassword():
    current_user_id = get_jwt_identity()
    if not current_user_id:
        return jsonify({"message": "Authentication required"}), 401
    data = request.get_json() or {}
    return auth_controller.changePassword(int(current_user_id), data)


@auth_bp.route("/me", methods=["GET", "OPTIONS"])
@jwt_required()
def me():
    current_user_id = get_jwt_identity()
    if not current_user_id:
        return jsonify({"message": "Authentication required"}), 401
    return auth_controller.me(int(current_user_id))