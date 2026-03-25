from flask import Blueprint, request
from routes.products import products_controller

products_bp = Blueprint("products_bp", __name__)


@products_bp.route("/getAll", methods=["GET"])
def getAll():
    include_family = (request.args.get("include_family", "false").lower() == "true")
    include_laboratory = (request.args.get("include_laboratory", "false").lower() == "true")
    include_generic = (request.args.get("include_generic", "false").lower() == "true")
    include_description = (request.args.get("include_description", "false").lower() == "true")
    include_therapeutic_group = (request.args.get("include_therapeutic_group", "false").lower() == "true")

    return products_controller.getAll(
        include_family=include_family,
        include_laboratory=include_laboratory,
        include_generic=include_generic,
        include_description=include_description,
        include_therapeutic_group=include_therapeutic_group
    )


@products_bp.route("/createProduct", methods=["POST"])
def createProduct():
    return products_controller.createProduct(request.get_json() or {})


@products_bp.route("/deleteProduct/<int:id>", methods=["DELETE"])
def deleteProduct(id):
    return products_controller.deleteProduct(id)


@products_bp.route("/updateProduct/<int:id>", methods=["PUT"])
def updateProduct(id):
    return products_controller.updateProduct(id, request.get_json() or {})