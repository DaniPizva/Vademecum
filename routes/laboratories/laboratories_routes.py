from flask import Blueprint, request
from routes.laboratories import laboratories_controller

laboratories_bp = Blueprint("laboratories_bp", __name__)

@laboratories_bp.route("/getAll", methods=["GET"]) #nombre de la ruta getall, y metodo get
def getAll():
    return laboratories_controller.getAll()

@laboratories_bp.route("/createLaboratory", methods=["POST"])
def createLaboratory():
    return laboratories_controller.createLaboratory(request.get_json() or {})

@laboratories_bp.route("/deleteLaboratory/<int:id>", methods=["DELETE"]) # el path <int:id>
def deleteLaboratory(id):
    return laboratories_controller.deleteLaboratory(id) 

@laboratories_bp.route("/updateLaboratory/<int:id>", methods=["PUT"]) # el path <int:id>
def updateLaboratory(id):
    return laboratories_controller.updateLaboratory(id , request.get_json() or {})  #que se pueda recibir un cuerp vacio
