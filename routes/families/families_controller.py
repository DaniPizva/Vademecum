from common.http import ok, bad_request, created
from routes.families import families_service


def getAll(include_description: bool = False, include_therapeutic_group: bool = False):
    data, err = families_service.getAll()
    if err:
        return bad_request(message="No se pudo obtener las families", errors=err)

    return ok(
        data=[
            d.to_dict(
                include_description=include_description,
                include_therapeutic_group=include_therapeutic_group
            ) for d in data
        ],
        message="Families obtenidas con éxito"
    )


def createFamily(data):
    result, err = families_service.createFamily(data)
    if err:
        return bad_request(message="Error creating family", errors=err)

    return created(
        data=result.to_dict(include_description=True, include_therapeutic_group=True),
        message="Family created successfully"
    )


def deleteFamily(id: int):
    result, err = families_service.deleteFamily(id)
    if err:
        return bad_request(message="Error deleting family", errors=err)

    return ok(
        data={"delete": result},
        message="Family with id: " + str(id) + " deleted successfully"
    )


def updateFamily(id: int, data_body):
    result, err = families_service.updateFamily(id, data_body)
    if err:
        return bad_request(message="Error updating family", errors=err)

    return ok(
        data=result.to_dict(include_description=True, include_therapeutic_group=True),
        message="Family with id: " + str(id) + " updated successfully"
    )