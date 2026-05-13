# routes/products/products_controller.py
from common.http import ok, bad_request, created, not_found
from routes.products import products_service, images_service

def getAll(include_family=False, include_laboratory=False, include_generic=False,
           include_description=False, include_therapeutic_group=False):
    data, err = products_service.getAll(
        include_family=include_family,
        include_laboratory=include_laboratory,
        include_generic=include_generic,
        include_description=include_description,
        include_therapeutic_group=include_therapeutic_group
    )
    if err:
        return bad_request(message="No se pudo obtener los products", errors=err)
    return ok(data=data, message="Products obtenidos con éxito")

def getById(id, include_family=True, include_laboratory=True, include_generic=True,
            include_description=True, include_therapeutic_group=True):
    product, err = products_service.getById(
        id=id,
        include_family=include_family,
        include_laboratory=include_laboratory,
        include_generic=include_generic,
        include_description=include_description,
        include_therapeutic_group=include_therapeutic_group
    )
    if err:
        return not_found(message="Producto no encontrado", errors=err)
    # product is already a dict
    return ok(data=product, message="Producto obtenido con éxito")

def getAllViewModels():
    data, err = products_service.getAllViewModels()
    if err:
        return bad_request(message="No se pudo obtener los viewmodels", errors=err)
    return ok(data=data, message="Product viewmodels obtenidos con éxito")


def getViewById(id):
    data, err = products_service.getViewById(id)
    if err:
        return not_found(message="Producto no encontrado", errors=err)
    return ok(data=data, message="Product viewmodel obtenido con éxito")


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

def deleteProduct(id):
    result, err = products_service.deleteProduct(id)
    if err:
        return bad_request(message="Error deleting product", errors=err)
    return ok(data=result, message=f"Product {id} deleted")

def updateProduct(id, data_body):
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
        message=f"Product {id} updated"
    )


def uploadProductImage(product_id, file, is_main):
    import tempfile, os
    if not file or file.filename == '':
        return bad_request(message="No image file provided")
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
        file.save(tmp.name)
        tmp_path = tmp.name
    try:
        result, err = images_service.upload_product_image(product_id, tmp_path, is_main)
    finally:
        os.unlink(tmp_path)
    if err:
        return bad_request(message="Failed to upload image", errors=err)
    return created(
        data={"id": result.id, "image_url": result.image_url, "is_main": result.is_main},
        message="Image uploaded"
    )

def deleteProductImage(image_id):
    success, err = images_service.delete_product_image(image_id)
    if err:
        return bad_request(message="Failed to delete image", errors=err)
    return ok(data={"deleted": True}, message=f"Image {image_id} deleted")

def setMainImage(product_id, image_id):
    success, err = images_service.set_main_image(product_id, image_id)
    if err:
        return bad_request(message="Failed to set main image", errors=err)
    return ok(data={"main_image_id": image_id}, message="Main image updated")