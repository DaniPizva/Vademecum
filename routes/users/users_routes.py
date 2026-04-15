from flask import Blueprint, request
import routes.users.users_controller as users_controller
from flask_jwt_extended import jwt_required

users_bp = Blueprint("users_bp", __name__)
@users_bp.before_request
@jwt_required()
def before_request():
    pass  #opcion de automatizacion de todas las rutas de cities , antes de que recorra cualquier ruta, verifica si hay un token 


@users_bp.route("/getAll", methods=["GET"]) #nombre de la ruta getall, y metodo get
def getAll():
    return users_controller.getAll()
