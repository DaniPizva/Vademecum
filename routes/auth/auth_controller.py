# routes\auth\auth_controller.py
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required
import re
from common.http import ok, bad_request, unauthorized, created
from routes.auth import auth_service
from flask import request



def loginUser(data):
    auth_data, err = auth_service.loginUser(data)
    if err:
        return unauthorized(message="login invalido", errors=err)

    # user dict already contains terms_accepted, must_change_password, etc.
    access_token = create_access_token(
        identity=str(auth_data["user"]["id"]),
        additional_claims={"roles": [role["code"] for role in auth_data["authorization"]["roles"]]}
    )

    return ok(
        data={
            "access_token": access_token,
            **auth_data
        },
        message="Login exitoso"
    )


def createUser(data):
    result, err = auth_service.createUser(data)

    if err:
        return bad_request(message="Error creating user", errors=err)

    user = result["user"]
    temp_password = result["temp_password"]

    return created(
        data={
            "user": user.to_dict(),
            "temp_password": temp_password  # solo para desarrollo, luego ha de ser implementado en un sistema.
        },
        message="User created successfully"
    )


# ----- new endpoints -----

def acceptTerms(user_id):
    ip_address = request.remote_addr
    user_agent = request.headers.get("User-Agent")

    success, err = auth_service.accept_terms(
        user_id=user_id,
        ip_address=ip_address,
        user_agent=user_agent
    )

    if err:
        return bad_request(message="Error accepting terms", errors=err)

    return ok(message="Terms accepted", data={})

def changePassword(user_id, data):
    """Changes password, conditionally requiring current password."""
    success, err = auth_service.change_password(user_id, data)
    if err:
        return bad_request(message="Error changing password", errors=err)
    return ok(message="Password updated", data={})


def me(user_id):
    """Returns current user state and a new access token to extend the session."""
    user_state, err = auth_service.get_me(user_id)
    if err:
        return bad_request(message="User not found", errors=err)

    # Issue a new token to refresh the session (sliding expiration)
    new_token = create_access_token(
        identity=str(user_state["user"]["id"]),
        additional_claims={"roles": [
            role["code"]
            for role in user_state["authorization"]["roles"]
        ]}
    )

    return ok(
        data={
            **user_state,
            "access_token": new_token
        },
        message="User state refreshed"
    )