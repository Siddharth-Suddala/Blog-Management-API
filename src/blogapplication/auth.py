from flask import Blueprint, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token
from uuid import uuid4

from .database import users

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


def generate_id(prefix):
    return prefix + "-" + str(uuid4())


@auth_bp.route("/register", methods=["POST"])
def handle_register():

    data = request.json

    if not data or "name" not in data or "email" not in data or "password" not in data:
        return "Invalid data", 400

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    user = users.find_one({"email": email})

    if user:
        return "User already exists", 409

    hashed_password = generate_password_hash(password)

    user_id = generate_id("USER")

    users.insert_one({
        "user_id": user_id,
        "name": name,
        "email": email,
        "password": hashed_password
    })

    return "User added", 201


@auth_bp.route("/login", methods=["POST"])
def handle_login():

    data = request.json

    email = data.get("email")
    password = data.get("password")

    user = users.find_one({"email": email})

    if not user or not check_password_hash(
        user["password"], password
    ):
        return "Invalid credentials", 401

    token = create_access_token(
        identity=user["user_id"]
    )

    return {
        "message": "Login successful",
        "user_id": user["user_id"],
        "token": token
    }, 200