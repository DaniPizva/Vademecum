from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from routes.products_images import products_images_controller
 
user_images_bp = Blueprint("user_images_bp", __name__)
#en mongo en vez de ser <int:id>, es <string:id> 
 
@user_images_bp.before_request
@jwt_required()
def before_request():
    pass
 
@user_images_bp.route("/get", methods=["GET"]) #nombre de la ruta getall, y metodo get
def get():
    return products_images_controller.get()

@user_images_bp.route("/create", methods=["POST"])
def create():
    return products_images_controller.create(request.get_json() or {})

@user_images_bp.route("/delete/<string:id>", methods=["DELETE"]) # el path <int:id>
def delete(id):
    return products_images_controller.delete(id) 

@user_images_bp.route("/update/<string:id>", methods=["PUT"]) # el path <int:id>
def update(id):
    return products_images_controller.update(id , request.get_json() or {})
