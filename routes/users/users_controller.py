# routes\users\users_controller.py
from common.http import ok, bad_request, created
### ahora cargamos el service
from routes.users import users_service as users_service


def getAll(): #a controller lo llama routes
    data, err = users_service.getAll()
    if err:
        return bad_request(message="No se pudo obtener los users", errors=err)
    return ok(data=[d.to_dict() for d in data], message="Users obtenidas con éxito")#siempre fevolver como diccionario


def delete(id: int): 
    result, err = users_service.delete(id)
    if err:
        return bad_request(message="Error deleting user", errors=err)
    return ok(data={"delete":result}, message="user with id:" + str(id) + "deleted successfully")



def update(id: int, data_body): #especificar que sea como un numero porque todo llega como string 
    result, err = users_service.update(id, data_body)
    if err:
        return bad_request(message="Error updating user", errors=err)
    return ok(data=result.to_dict(), message="user with id:" + str(id) + "updated successfully")