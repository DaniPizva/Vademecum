from common.http import ok, bad_request, created
### ahora cargamos el service
from routes.descriptions import descriptions_service as descriptions_service



def getAll(**kwargs):
    data, err = descriptions_service.getAll()
    if err:
        return bad_request(message="No se pudo obtener las descripciones", errors=err)
    return ok(data=data, message="Descripciones obtenidas con éxito")

def create(data):
    result, err = descriptions_service.create(data)
    if err:
        return bad_request(message="Error creating description", errors=err)
    return created(data=result, message="description created successfully")

def toggle_description_state(id: int):
    result, err = descriptions_service.toggle_description_state(id)
    if err:
        return bad_request(message="Failed to toggle description state", errors=err)
    return ok(
        data=result,   # directly {id, is_active}
        message=f"Description {'activated' if result['is_active'] else 'deactivated'} successfully"
    )
    
def updateDescription(id: int, data_body): #especificar que sea como un numero porque todo llega como string 
    result, err = descriptions_service.updateDescription(id, data_body)
    if err:
        return bad_request(message="Error updating description", errors=err)
    return ok(data=result.to_dict(), message="Description with id:" + str(id) + "updated successfully") #que muestre si quedo actualizado por eso es idferente a delete







