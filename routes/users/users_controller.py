from common.http import ok, bad_request, created
### ahora cargamos el service
from routes.users import users_service as users_service


def getAll(): #a controller lo llama routes
    data, err = users_service.getAll()
    if err:
        return bad_request(message="No se pudo obtener los users", errors=err)
    return ok(data=[d.to_dict() for d in data], message="Users obtenidas con éxito")#siempre fevolver como diccionario





