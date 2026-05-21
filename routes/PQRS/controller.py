# routes\PQRS\controller.py

from common.http import (
    ok,
    bad_request,
    created
)

from routes.PQRS import service


# =========================================================
# PUBLIC CONTROLLERS
# =========================================================

def createPQRS(data):

    result, err = service.createPQRS(
        data
    )

    if err:

        return bad_request(
            message="Error creating PQRS ticket",
            errors=err
        )

    return created(

        data=result.to_dict(
            include_products=True
        ),

        message="PQRS ticket created successfully"
    )


def getTicket(ticket_code: str):

    result, err = service.getTicket(
        ticket_code
    )

    if err:

        return bad_request(
            message="Error retrieving PQRS ticket",
            errors=err
        )

    return ok(

        data=result.to_dict(
            include_products=True
        ),

        message="PQRS ticket retrieved successfully"
    )


def validateSKU(sku_code: str):

    result, err = service.validateSKU(
        sku_code
    )

    if err:

        return bad_request(
            message="Invalid SKU",
            errors=err
        )

    return ok(

        data=result,

        message="SKU validated successfully"
    )


def getCategories():

    result, err = service.getCategories()

    if err:

        return bad_request(
            message="Error retrieving categories",
            errors=err
        )

    return ok(

        data=result,

        message="PQRS categories retrieved successfully"
    )


def getTypes():

    result, err = service.getTypes()

    if err:

        return bad_request(
            message="Error retrieving PQRS types",
            errors=err
        )

    return ok(

        data=result,

        message="PQRS types retrieved successfully"
    )


# =========================================================
# ADMIN CONTROLLERS
# =========================================================

def getAllPQRS():

    result, err = service.getAllPQRS()

    if err:

        return bad_request(
            message="Error retrieving PQRS tickets",
            errors=err
        )

    return ok(

        data=result,

        message="PQRS tickets retrieved successfully"
    )


def getPQRSByStatus(status: str):

    result, err = service.getPQRSByStatus(
        status
    )

    if err:

        return bad_request(
            message="Error retrieving PQRS by status",
            errors=err
        )

    return ok(

        data=result,

        message="PQRS filtered successfully"
    )


def updatePQRSStatus(
    id: int,
    data_body
):

    result, err = service.updatePQRSStatus(
        id,
        data_body
    )

    if err:

        return bad_request(
            message="Error updating PQRS status",
            errors=err
        )

    return ok(

        data=result.to_dict(
            include_products=True
        ),

        message=f"PQRS ticket {id} updated successfully"
    )


def respondPQRS(
    id: int,
    data_body
):

    result, err = service.respondPQRS(
        id,
        data_body
    )

    if err:

        return bad_request(
            message="Error responding PQRS ticket",
            errors=err
        )

    return ok(

        data=result,

        message=f"Response registered for PQRS ticket {id}"
    )


def deletePQRS(id: int):

    result, err = service.deletePQRS(
        id
    )

    if err:

        return bad_request(
            message="Error deleting PQRS ticket",
            errors=err
        )

    return ok(

        data={
            "deleted": result
        },

        message=f"PQRS ticket {id} deleted successfully"
    )