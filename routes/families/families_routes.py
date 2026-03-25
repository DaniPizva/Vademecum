from flask import Blueprint, request
from routes.families import families_controller

families_bp = Blueprint("families_bp", __name__)


@families_bp.route("/getAll", methods=["GET"])
def getAll():
    include_description = (request.args.get("include_description", "false").lower() == "true")
    include_therapeutic_group = (request.args.get("include_therapeutic_group", "false").lower() == "true")

    return families_controller.getAll(
        include_description=include_description,
        include_therapeutic_group=include_therapeutic_group
    )


@families_bp.route("/createFamily", methods=["POST"])
def createFamily():
    return families_controller.createFamily(request.get_json() or {})


@families_bp.route("/deleteFamily/<int:id>", methods=["DELETE"])
def deleteFamily(id):
    return families_controller.deleteFamily(id)


@families_bp.route("/updateFamily/<int:id>", methods=["PUT"])
def updateFamily(id):
    return families_controller.updateFamily(id, request.get_json() or {})