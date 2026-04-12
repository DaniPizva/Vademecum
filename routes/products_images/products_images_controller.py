from common.http import ok, bad_request, created
from routes.products_images import products_images_service
 
def getAll(): #a controller lo llama routes
    data, err = products_images_service.getAll()
    if err:
        return bad_request(message="No se pudo obtener las product images", errors=err)
    return ok(data=[d.to_dict() for d in data], message="Product Images obtenidas con éxito")

def createProductImage(data):
    result, err = products_images_service.createProductImage(data)
    if err:
        return bad_request(message="Error creating product image", errors=err)
    return created(data=result.to_dict(), message="Product image created successfully")

def deleteProductImage(id: int): 
    result, err = products_images_service.deleteProductImage(id)
    if err:
        return bad_request(message="Error deleting product image", errors=err)
    return ok(data={"delete":result}, message="Product Image with id:" + str(id) + "deleted successfully")

def updateProductImage(id: int, data_body): #especificar que sea como un numero porque todo llega como string 
    result, err = products_images_service.updateProductImage(id, data_body)
    if err:
        return bad_request(message="Error updating product image", errors=err)
    return ok(data=result.to_dict(), message="Product image with id:" + str(id) + "updated successfully") #que muestre si quedo actualizado por eso es idferente a delete
