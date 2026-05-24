from flask import Blueprint, request
import routes.descriptions.descriptions_controller as descriptions_controller

descriptions_bp = Blueprint("descriptions_bp", __name__)

@descriptions_bp.route("/getAll", methods=["GET"]) #nombre de la ruta getall, y metodo get
def getAll():
    return descriptions_controller.getAll()

@descriptions_bp.route("/create", methods=["POST"])
def createDescription():
    return descriptions_controller.create(request.get_json() or {})

@descriptions_bp.route("/toggle-state/<int:id>", methods=["DELETE", "PATCH"]) # el path <int:id>
def deleteDescription(id):
  
    return descriptions_controller.toggle_description_state(id) 

@descriptions_bp.route("/update/<int:id>", methods=["PUT"]) # el path <int:id>
def updateDescription(id):
    return descriptions_controller.updateDescription(id , request.get_json() or {})  #que se pueda recibir un cuerp vacio
