from common.http import ok, bad_request, created
from routes.families import families_service


def getAll(**kwargs):
    data, err = families_service.getAll()
    if err:
        return bad_request(message="No se pudo obtener las familias", errors=err)
    return ok(data=data, message="Familias obtenidas con éxito")

def create(data):
    result, err = families_service.create(data)
    if err:
        return bad_request(message="Error creating family", errors=err)
    
    return created(
        data=result,
        message="Family created successfully"
    )

def toggle_family(id):
    result, err = families_service.toggle_family_state(id)
    if err:
        return bad_request(message="Toggle failed", errors=err)
    return ok(data=result, message=f"Family {'activated' if result['is_active'] else 'deactivated'}")

def updateFamily(id: int, data_body):
    result, err = families_service.updateFamily(id, data_body)
    if err:
        return bad_request(message="Error updating family", errors=err)

    return ok(
        data=result.to_dict(include_description=True, include_therapeutic_group=True),
        message="Family with id: " + str(id) + " updated successfully"
    )