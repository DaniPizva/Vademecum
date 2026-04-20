# routes\auth\auth_controller.py
from flask_jwt_extended import create_access_token
import re
from common.http import ok, bad_request, unauthorized, created
from routes.auth import auth_service



def loginUser(data):
    user, err = auth_service.loginUser(data)
    print(err)
    if err:
        return unauthorized(message="login invalido", errors=err)
    
    token = create_access_token(identity=str(user["id"]),
                                additional_claims={"role_id": user["role_id"]})

    return ok(
        data={
            "access_token": token,
            "user": user
        }, message = "Login exitoso"  
    ) #user: le devuelve los datos del usuario y suinformacion asociada

def createUser(data):
    result, err = auth_service.createUser(data)
    if err:
        return bad_request(message="Error creating user", errors=err)
    return created(data=result.to_dict(), message="User created successfully")
