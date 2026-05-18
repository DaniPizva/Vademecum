# routes/users/users_routes.py

from flask import Blueprint, request
from flask_jwt_extended import jwt_required

import routes.users.users_controller as users_controller


users_bp = Blueprint("users_bp", __name__)


# ------------------------------------------------------------------------------
# USERS
# ------------------------------------------------------------------------------

@users_bp.route("/getAll", methods=["GET"])
def getAll():
    return users_controller.getAll()


@users_bp.route("/viewmodels", methods=["GET"])
def getViewModels():
    return users_controller.getAllViewModels()


@users_bp.route("/<string:id>", methods=["GET"])
def getById(id):
    return users_controller.getById(id)


@users_bp.route("/update/<string:id>", methods=["PUT"])
@jwt_required()
def update(id):
    return users_controller.update(id, request.get_json() or {})


@users_bp.route("/delete/<string:id>", methods=["DELETE"])
@jwt_required()
def delete(id):
    return users_controller.delete(id)


# ------------------------------------------------------------------------------
# USER IMAGES
# ------------------------------------------------------------------------------

@users_bp.route(
    "/<string:user_id>/image",
    methods=["POST"]
)
def upload_user_image(user_id):

    """
    Multipart upload endpoint.
    Expects file under key: 'image'
    """

    file = request.files.get("image")

    return users_controller.upload_user_image(
        user_id,
        file
    )


@users_bp.route(
    "/<string:user_id>/image",
    methods=["DELETE", "OPTIONS"]
)
def delete_user_image(user_id):

    return users_controller.delete_user_image(user_id)