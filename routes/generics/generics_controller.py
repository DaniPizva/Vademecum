from common.http import ok, bad_request, created
### ahora cargamos el service
from routes.generics import generics_service

def getAll(**kwargs):
    data, err = generics_service.getAll()
    if err:
        return bad_request(message="No se pudo obtener los genéricos", errors=err)
    return ok(data=data, message="Genéricos obtenidos con éxito")

def createGeneric(data):
    result, err = generics_service.createGeneric(data)
    if err:
        return bad_request(message="Error creating generic", errors=err)
    return created(data=result.to_dict(), message="Generic created successfully")

def deleteGeneric(id: int): #especificar que sea como un numero porque todo llega como string 
    result, err = generics_service.deleteGeneric(id)
    if err:
        return bad_request(message="Error deleting generic", errors=err)
    return ok(data={"delete":result}, message="Generic with id:" + str(id) + "deleted successfully")

def updateGeneric(id: int, data_body): #especificar que sea como un numero porque todo llega como string 
    result, err = generics_service.updateGeneric(id, data_body)
    if err:
        return bad_request(message="Error updating generic", errors=err)
    return ok(data=result.to_dict(), message="Generic with id:" + str(id) + "updated successfully") 