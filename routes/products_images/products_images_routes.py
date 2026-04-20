from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from routes.products_images import products_images_controller
 
products_images_bp = Blueprint("product_images_bp", __name__)
#en mongo en vez de ser <int:id>, es <string:id> 
 
@products_images_bp.before_request
@jwt_required()
def before_request():
    pass
 
@products_images_bp.route("/getAll", methods=["GET"]) #nombre de la ruta getall, y metodo get
#@jwt_required() #si hay un login consulto la ruta 
def getAll():
    return products_images_controller.getAll()

@products_images_bp.route("/create", methods=["POST"])
def createProductImage():
    return products_images_controller.createProductImage(request.get_json() or {})

@products_images_bp.route("/delete/<string:id>", methods=["DELETE"]) # el path <int:id>
def deleteProductImage(id):
    return products_images_controller.deleteProductImage(id) 

@products_images_bp.route("/update/<string:id>", methods=["PUT"]) # el path <int:id>
def updateProductImage(id):
    return products_images_controller.updateProductImage(id , request.get_json() or {})
