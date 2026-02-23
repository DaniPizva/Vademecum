from common.http import ok, bad_request, created
### ahora cargamos el service
from routes.descriptions import descriptions_service as descriptions_service



def getAll(): #a controller lo llama routes
    data, err = descriptions_service.getAll()
    if err:
        return bad_request(message="No se pudo obtener los descriptions", errors=err)
    return ok(data=[d.to_dict() for d in data], message="Descriptions obtenidas con éxito")#siempre fevolver como diccionario

def createDescription(data):
    result, err = descriptions_service.createDescription(data)
    if err:
        return bad_request(message="Error creating description", errors=err)
    return created(data=result.to_dict(), message="description created successfully")

def deleteDescription(id: int): #especificar que sea como un numero porque todo llega como string 
    result, err = descriptions_service.deleteDescription(id)
    if err:
        return bad_request(message="Error deleting description", errors=err)
    return ok(data={"delete":result}, message="Description with id:" + str(id) + "deleted successfully")

def updateDescription(id: int, data_body): #especificar que sea como un numero porque todo llega como string 
    result, err = descriptions_service.updateDescription(id, data_body)
    if err:
        return bad_request(message="Error updating description", errors=err)
    return ok(data=result.to_dict(), message="Description with id:" + str(id) + "updated successfully") #que muestre si quedo actualizado por eso es idferente a delete







