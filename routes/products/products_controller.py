from common.http import ok, bad_request, created
from routes.products import products_service


def getAll(
    include_family: bool = False,
    include_laboratory: bool = False,
    include_generic: bool = False,
    include_description: bool = False,
    include_therapeutic_group: bool = False
):
    data, err = products_service.getAll()
    if err:
        return bad_request(message="No se pudo obtener los products", errors=err)

    return ok(
        data=[
            d.to_dict(
                include_family=include_family,
                include_laboratory=include_laboratory,
                include_generic=include_generic,
                include_description=include_description,
                include_therapeutic_group=include_therapeutic_group
            ) for d in data
        ],
        message="Products obtenidos con éxito"
    )


def createProduct(data):
    result, err = products_service.createProduct(data)
    if err:
        return bad_request(message="Error creating product", errors=err)

    return created(
        data=result.to_dict(
            include_family=True,
            include_laboratory=True,
            include_generic=True,
            include_description=True,
            include_therapeutic_group=True
        ),
        message="Product created successfully"
    )


def deleteProduct(id: int):
    result, err = products_service.deleteProduct(id)
    if err:
        return bad_request(message="Error deleting product", errors=err)

    return ok(
        data={"delete": result},
        message="Product with id: " + str(id) + " deleted successfully"
    )


def updateProduct(id: int, data_body):
    result, err = products_service.updateProduct(id, data_body)
    if err:
        return bad_request(message="Error updating product", errors=err)

    return ok(
        data=result.to_dict(
            include_family=True,
            include_laboratory=True,
            include_generic=True,
            include_description=True,
            include_therapeutic_group=True
        ),
        message="Product with id: " + str(id) + " updated successfully"
    )