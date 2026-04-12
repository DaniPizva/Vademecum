from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from routes.description_images import description_images_controller
 
description_images_bp = Blueprint("description_images_bp", __name__)
#en mongo en vez de ser <int:id>, es <string:id> 
 
@description_images_bp.before_request
@jwt_required()
def before_request():
    pass
 
@description_images_bp.route("/getAll", methods=["GET"]) #nombre de la ruta getall, y metodo get
#@jwt_required() #si hay un login consulto la ruta 
def getAll():
    return description_images_controller.getAll()

@description_images_bp.route("/createDescriptionImage", methods=["POST"])
def createDescriptionImage():
    return description_images_controller.createDescriptionImage(request.get_json() or {})

@description_images_bp.route("/deleteDescriptionImage/<string:id>", methods=["DELETE"]) # el path <int:id>
def deleteDescriptionImage(id):
    return description_images_controller.deleteDescriptionImage(id) 

@description_images_bp.route("/updateDescriptionImage/<string:id>", methods=["PUT"]) # el path <int:id>
def updateDescriptionImage(id):
    return description_images_controller.updateDescriptionImage(id , request.get_json() or {})
