# routes/products/products_routes.py
from flask import Blueprint, request
from routes.products import products_controller

products_bp = Blueprint("products_bp", __name__)

@products_bp.route("/getAll", methods=["GET"])
def getAll():
    # The include_* params are kept for backward compatibility but ignored
    return products_controller.getAll(
        include_family=request.args.get("include_family", "false").lower() == "true",
        include_laboratory=request.args.get("include_laboratory", "false").lower() == "true",
        include_generic=request.args.get("include_generic", "false").lower() == "true",
        include_description=request.args.get("include_description", "false").lower() == "true",
        include_therapeutic_group=request.args.get("include_therapeutic_group", "false").lower() == "true"
    )

@products_bp.route("/getById/<int:id>", methods=["GET"])
def getById(id):
    return products_controller.getById(
        id=id,
        include_family=request.args.get("include_family", "true").lower() == "true",
        include_laboratory=request.args.get("include_laboratory", "true").lower() == "true",
        include_generic=request.args.get("include_generic", "true").lower() == "true",
        include_description=request.args.get("include_description", "true").lower() == "true",
        include_therapeutic_group=request.args.get("include_therapeutic_group", "true").lower() == "true"
    )

# NEW: Viewmodel list endpoint (used by admin product grid)
@products_bp.route("/getAllViewModels", methods=["GET"])
def getAllViewModels():
    return products_controller.getAllViewModels()

# NEW: Single viewmodel endpoint (product detail page)
@products_bp.route("/getViewById/<int:id>", methods=["GET"])
def getViewById(id):
    return products_controller.getViewById(id)

# Write operations (unchanged)
@products_bp.route("/createProduct", methods=["POST"])
def createProduct():
    return products_controller.createProduct(request.get_json() or {})

@products_bp.route("/deleteProduct/<int:id>", methods=["DELETE"])
def deleteProduct(id):
    return products_controller.deleteProduct(id)

@products_bp.route("/updateProduct/<int:id>", methods=["PUT"])
def updateProduct(id):
    return products_controller.updateProduct(id, request.get_json() or {})

# Image routes (unchanged)
@products_bp.route("/<int:product_id>/images", methods=["POST"])
def upload_product_image(product_id):
    file = request.files.get("image")
    is_main = request.form.get("is_main", "false").lower() == "true"
    return products_controller.uploadProductImage(product_id, file, is_main)

@products_bp.route("/product-images/<int:image_id>", methods=["DELETE"])
def delete_product_image(image_id):
    return products_controller.deleteProductImage(image_id)

@products_bp.route("/<int:product_id>/main-image/<int:image_id>", methods=["PUT"])
def set_main_image(product_id, image_id):
    return products_controller.setMainImage(product_id, image_id)