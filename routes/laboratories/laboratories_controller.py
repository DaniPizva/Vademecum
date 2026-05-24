# routes\laboratories\laboratories_controller.py
from common.http import ok, bad_request, created
### ahora cargamos el service
from routes.laboratories import laboratories_service


def getAll(**kwargs):
    data, err = laboratories_service.getAll()
    if err:
        return bad_request(message="No se pudo obtener los laboratorios", errors=err)
    return ok(data=data, message="Laboratorios obtenidos con éxito")

def create(data):
    result, err = laboratories_service.create(data)
    if err:
        return bad_request(message="Error creating laboratory", errors=err)
    return created(data=result, message="Laboratory created successfully")

def deleteLaboratory(id: int): #especificar que sea como un numero porque todo llega como string 
    result, err = laboratories_service.toggle_laboratory_state(id)
    if err:
        return bad_request(message="Error deleting laboratory", errors=err)
    return ok(data=result, message=f"Laboratory with {id}: {'permanently soft'} deleted")

def updateLaboratory(id: int, data_body): #especificar que sea como un numero porque todo llega como string 
    result, err = laboratories_service.updateLaboratory(id, data_body)
    if err:
        return bad_request(message="Error updating laboratory", errors=err)
    return ok(data=result.to_dict(), message="Laboratory with id:" + str(id) + "updated successfully") 