from common.http import ok, bad_request, created
### ahora cargamos el service
from routes.laboratories import laboratories_service


def getAll(): #a controller lo llama routes
    data, err = laboratories_service.getAll()
    if err:
        return bad_request(message="No se pudo obtener las laboratories", errors=err)
    return ok(data=[d.to_dict() for d in data], message="Laboratories obtenidas con éxito")#siempre fevolver como diccionario


def createLaboratory(data):
    result, err = laboratories_service.createLaboratory(data)
    if err:
        return bad_request(message="Error creating laboratory", errors=err)
    return created(data=result.to_dict(), message="Laboratory created successfully")

def deleteLaboratory(id: int): #especificar que sea como un numero porque todo llega como string 
    result, err = laboratories_service.deleteLaboratory(id)
    if err:
        return bad_request(message="Error deleting laboratory", errors=err)
    return ok(data={"delete":result}, message="Laboratory with id:" + str(id) + "deleted successfully")

def updateLaboratory(id: int, data_body): #especificar que sea como un numero porque todo llega como string 
    result, err = laboratories_service.updateLaboratory(id, data_body)
    if err:
        return bad_request(message="Error updating laboratory", errors=err)
    return ok(data=result.to_dict(), message="Laboratory with id:" + str(id) + "updated successfully") 