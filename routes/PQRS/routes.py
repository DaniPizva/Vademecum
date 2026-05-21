# routes\PQRS\routes.py

from flask import Blueprint, request

from routes.PQRS import controller


pqrs_bp = Blueprint("pqrs_bp", __name__)

# =========================================================
# PUBLIC ROUTES
# =========================================================

@pqrs_bp.route("/create", methods=["POST"])
def createPQRS():

    return controller.createPQRS(
        request.get_json() or {}
    )


@pqrs_bp.route(
    "/getTicket/<string:ticket_code>",
    methods=["GET"]
)
def getTicket(ticket_code):

    return controller.getTicket(
        ticket_code
    )


@pqrs_bp.route(
    "/validateSKU/<string:sku_code>",
    methods=["GET"]
)
def validateSKU(sku_code):

    return controller.validateSKU(
        sku_code
    )


@pqrs_bp.route(
    "/getCategories",
    methods=["GET"]
)
def getCategories():

    return controller.getCategories()


@pqrs_bp.route(
    "/getTypes",
    methods=["GET"]
)
def getTypes():

    return controller.getTypes()


# =========================================================
# ADMIN ROUTES
# =========================================================

@pqrs_bp.route(
    "/admin/getAll",
    methods=["GET"]
)
def getAllPQRS():

    return controller.getAllPQRS()


@pqrs_bp.route(
    "/admin/getByStatus/<string:status>",
    methods=["GET"]
)
def getPQRSByStatus(status):

    return controller.getPQRSByStatus(
        status
    )


@pqrs_bp.route(
    "/admin/updateStatus/<int:id>",
    methods=["PUT"]
)
def updatePQRSStatus(id):

    return controller.updatePQRSStatus(
        id,
        request.get_json() or {}
    )


@pqrs_bp.route(
    "/admin/respond/<int:id>",
    methods=["POST"]
)
def respondPQRS(id):

    return controller.respondPQRS(
        id,
        request.get_json() or {}
    )


@pqrs_bp.route(
    "/admin/delete/<int:id>",
    methods=["DELETE"]
)
def deletePQRS(id):

    return controller.deletePQRS(
        id
    )