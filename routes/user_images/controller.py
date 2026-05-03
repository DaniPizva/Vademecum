# routes\products_images\products_images_controller.py
from common.http import ok, bad_request, created
from routes.products_images import products_images_service
 
def get(): #a controller lo llama routes
    data, err = products_images_service.getAll()
    if err:
        return bad_request(message="No se pudo obtener las product images", errors=err)
    return ok(data=[d.to_dict() for d in data], message="Product Images obtenidas con éxito")

def create(data):
    result, err = products_images_service.create(data)
    if err:
        return bad_request(message="Error creating product image", errors=err)
    return created(data=result.to_dict(), message="Product image created successfully")

def delete(id: int): 
    result, err = products_images_service.delete(id)
    if err:
        return bad_request(message="Error deleting product image", errors=err)
    return ok(data={"delete":result}, message="Product Image with id:" + str(id) + "deleted successfully")

def update(id: int, data_body): #especificar que sea como un numero porque todo llega como string 
    result, err = products_images_service.update(id, data_body)
    if err:
        return bad_request(message="Error updating product image", errors=err)
    return ok(data=result.to_dict(), message="Product image with id:" + str(id) + "updated successfully") #que muestre si quedo actualizado por eso es idferente a delete
