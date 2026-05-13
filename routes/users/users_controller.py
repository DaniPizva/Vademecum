# routes\users\users_controller.py
from common.http import ok, bad_request, created
### ahora cargamos el service
from routes.users import users_service as users_service


def getAll():
    data, err = users_service.getAll()
    if err:
        return bad_request(...)
    return ok(data=data, message="Usuarios obtenidos con exito")

def delete(id: int): 
    result, err = users_service.delete(id)
    if err:
        return bad_request(message="Error deleting user", errors=err)
    return ok(data={"delete":result}, message="user with id:" + str(id) + "deleted successfully")

def update(id: int, data_body):

    result, err = users_service.update(
        id,
        data_body
    )

    if err:

        return bad_request(
            message="Error updating user",
            errors=err
        )

    return ok(

        data=result,

        message=(
            "User with id: "
            + str(id)
            + " updated successfully"
        )
    )
    
def getAllViewModels():
    data, err = users_service.getAllViewModels()
    if err:
            return bad_request(...)
    return ok(data=data, message="Modelos de objetos obtenidos con exito")