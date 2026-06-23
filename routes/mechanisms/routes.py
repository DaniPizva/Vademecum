# routes\laboratories\laboratories_routes.py
from flask import Blueprint, request
from routes.mechanisms import controller

mechanisms_bp = Blueprint("mechanisms_bp", __name__)

@mechanisms_bp.route("/getAll", methods=["GET"]) #nombre de la ruta getall, y metodo get
def getAll():
    return controller.getAll()

@mechanisms_bp.route("/create", methods=["POST"])
def create():
    return controller.create(request.get_json() or {})

@mechanisms_bp.route("/toggle-state/<int:id>", methods=["DELETE", "PATCH"]) # el path <int:id>
def delete(id):
    return controller.delete(id) 

@mechanisms_bp.route("/update/<int:id>", methods=["PUT"]) # el path <int:id>
def update(id):
    return controller.update(id , request.get_json() or {})  #que se pueda recibir un cuerp vacio
