from common.http import ok, bad_request, created
### ahora cargamos el service
from routes.Therapeutic_group import Therapeutic_group_service as Therapeutic_group_service



def getAll(): #a controller lo llama routes
    data, err = Therapeutic_group_service.getAll()
    if err:
        return bad_request(message="No se pudo obtener los Therapeutic groups", errors=err)
    return ok(data=[d.to_dict() for d in data], message="Therapeutic groups obtenidas con éxito")#siempre fevolver como diccionario

def createTg(data):
    result, err = Therapeutic_group_service.createTg(data)
    if err:
        return bad_request(message="Error creating Therapeutic group", errors=err)
    return created(data=result.to_dict(), message="Therapeutic group created successfully")

def deleteTg(id: int): #especificar que sea como un numero porque todo llega como string 
    result, err = Therapeutic_group_service.deleteTg(id)
    if err:
        return bad_request(message="Error deleting therapeutic group", errors=err)
    return ok(data={"delete":result}, message="Therapeutic group with id:" + str(id) + "deleted successfully")

def updateTg(id: int, data_body): #especificar que sea como un numero porque todo llega como string 
    result, err = Therapeutic_group_service.updateTg(id, data_body)
    if err:
        return bad_request(message="Error updating therapeutic group", errors=err)
    return ok(data=result.to_dict(), message="Therapeutic group with id:" + str(id) + "updated successfully") #que muestre si quedo actualizado por eso es idferente a delete







