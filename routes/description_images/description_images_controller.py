# routes\description_images\description_images_controller.py
from common.http import ok, bad_request, created
from routes.description_images import description_images_service
 
def getAll(): #a controller lo llama routes
    data, err = description_images_service.getAll()
    if err:
        return bad_request(message="No se pudo obtener las description images", errors=err)
    return ok(data=[d.to_dict() for d in data], message="Description Images obtenidas con éxito")

def createDescriptionImage(data):
    result, err = description_images_service.createDescriptionImage(data)
    if err:
        return bad_request(message="Error creating description image", errors=err)
    return created(data=result.to_dict(), message="Description image created successfully")

def deleteDescriptionImage(id: int): 
    result, err = description_images_service.deleteDescriptionImage(id)
    if err:
        return bad_request(message="Error deleting description image", errors=err)
    return ok(data={"delete":result}, message="Description Image with id:" + str(id) + "deleted successfully")

def updateDescriptionImage(id: int, data_body): #especificar que sea como un numero porque todo llega como string 
    result, err = description_images_service.updateDescriptionImage(id, data_body)
    if err:
        return bad_request(message="Error updating description image", errors=err)
    return ok(data=result.to_dict(), message="Description image with id:" + str(id) + "updated successfully") #que muestre si quedo actualizado por eso es idferente a delete
