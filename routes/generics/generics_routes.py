from flask import Blueprint, request
from routes.generics import generics_controller

generics_bp = Blueprint("generics_bp", __name__)

@generics_bp.route("/getAll", methods=["GET"]) #nombre de la ruta getall, y metodo get
def getAll():
    return generics_controller.getAll()

@generics_bp.route("/createGeneric", methods=["POST"])
def createGeneric():
    return generics_controller.createGeneric(request.get_json() or {})

@generics_bp.route("/deleteGeneric/<int:id>", methods=["DELETE"]) # el path <int:id>
def deleteGeneric(id):
    return generics_controller.deleteGeneric(id) 

@generics_bp.route("/updateGeneric/<int:id>", methods=["PUT"]) # el path <int:id>
def updateGeneric(id):
    return generics_controller.updateGeneric(id , request.get_json() or {})  #que se pueda recibir un cuerp vacio
