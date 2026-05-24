from flask import Blueprint, request
import routes.Therapeutic_group.Therapeutic_group_controller as Therapeutic_group_controller
from flask_jwt_extended import jwt_required

Therapeutic_group_bp = Blueprint("Therapeutic_group_bp", __name__)
@Therapeutic_group_bp.before_request
@jwt_required()
def before_request():
    pass  #opcion de automatizacion de todas las rutas de cities , antes de que recorra cualquier ruta, verifica si hay un token 


@Therapeutic_group_bp.route("/getAll", methods=["GET"]) #nombre de la ruta getall, y metodo get
def getAll():
    return Therapeutic_group_controller.getAll()

@Therapeutic_group_bp.route("/create", methods=["POST"])
def createTg():
    return Therapeutic_group_controller.create(request.get_json() or {})

@Therapeutic_group_bp.route("/toggle-state/<int:id>", methods=["DELETE", "PATCH"]) # el path <int:id>
def deleteTg(id):
    return Therapeutic_group_controller.deleteTg(id) 

@Therapeutic_group_bp.route("/updateTg/<int:id>", methods=["PUT"]) # el path <int:id>
def updateTg(id):
    return Therapeutic_group_controller.updateTg(id , request.get_json() or {})  #que se pueda recibir un cuerp vacio
