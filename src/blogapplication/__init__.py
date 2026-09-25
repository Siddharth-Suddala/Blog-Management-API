from flask import Flask, request,render_template , make_response
from pymongo import MongoClient
from werkzeug.security import generate_password_hash, check_password_hash
from uuid import uuid4
from flask_jwt_extended import JWTManager, create_access_token,get_jwt_identity , jwt_required,verify_jwt_in_request
from datetime import datetime


mongo_url = "mongodb+srv://testuser:e2t2THGDnCZRwIdr@cluster0.fdwibcx.mongodb.net/?appName=Cluster0"

mongo_client = MongoClient(mongo_url)

db = mongo_client["blogappdb"]

users = db["users"]
blogs = db["blogs"]
comments = db["comments"]
likes = db["likes"]

app = Flask(__name__)

app.config["JWT_SECRET_KEY"] = "weggurhfurhiguirkljsjgkgksls"

jwt = JWTManager(app)

def generate_id(prefix):
    return prefix + "-" + str(uuid4())

@app.route("/api/auth/register", methods=["POST"])
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

@app.route("/api/auth/login", methods=["POST"])
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

@app.route("/api/blogs", methods=["POST"])
@jwt_required()
def create_blog():

    data = request.json

    title = data.get("title")
    content = data.get("content")

    if not title or not content:
        return "Title and content are required", 400

    user_id = get_jwt_identity()

    blog_id = generate_id("BLOG")

    now = datetime.now()
    blogs.insert_one({
        "blog_id": blog_id,
        "title": title,
        "content": content,
        "author_id": user_id,
        "status": "draft",
        "created_at": now,
        "updated_at":now
    })

    return {
        "message": "Blog created",
        "blog_id": blog_id
    }, 201

@app.route("/api/blogs/<blog_id>",methods=["PUT"])
@jwt_required()
def edit_blog(blog_id):

    data = request.json

    title = data.get("title")
    content = data.get("content")

    if not title or not content:
        return "Missing data",400

    user_id = get_jwt_identity()

    blog = blogs.find_one({"blog_id":blog_id})

    if not blog:
        return "Blog isn't there",404

    if blog['author_id'] != user_id:
        return "Access denied to blog",403

    now = datetime.now()

    blogs.update_one(
        {"blog_id":blog_id},
        {"$set":{
            "title":title,
            "content":content,
            "updated_at":now
        }}
    )

    return "Blog updated", 200

@app.route("/api/blogs/<blog_id>/publish",methods=["PATCH"])
@jwt_required()
def publish_blog(blog_id):
    now = datetime.now()

    blog = blogs.find_one({"blog_id":blog_id})

    if not blog:
        return "Blog doesn't exist",404

    user_id = get_jwt_identity()

    if blog['author_id'] != user_id:
            return "Access denied to blog",403

    if blog["status"] != "draft":
        return "Blog is already published", 400

    blogs.update_one(
        {"blog_id":blog_id},
        {"$set":{"published_at":now,"status":"published"}}
    )

    return "Blog published",200

@app.route("/api/blogs/<blog_id>",methods=["GET"])
def get_blog(blog_id):

    blog = blogs.find_one({"blog_id":blog_id})

    if not blog:
        return "Blog doesn't exist", 404

    if blog["status"]  == "draft":
        verify_jwt_in_request(optional=True)

        user_id = get_jwt_identity()

        if user_id != blog["author_id"]:
            return "Blog doesn't exist", 404

    blog["_id"] = str(blog["_id"])

    return blog,200

@app.route("/api/blogs",methods=["GET"])
def get_blogs():

    published_blogs = list(blogs.find({"status":"published"}))

    for blog in published_blogs:
        blog["_id"] = str(blog["_id"])

    if not published_blogs:
        return "No blogs found",404

    return published_blogs,200

@app.route("/api/blogs/<blog_id>",methods=["DELETE"])
@jwt_required()
def delete_blog(blog_id):

    blog = blogs.find_one({"blog_id":blog_id})

    if not blog:
        return "Blog doesn't exist",404

    user_id = get_jwt_identity()

    if user_id != blog['author_id']:
        return "You don't have permission to delete", 403

    blogs.delete_one({"blog_id":blog_id})

    return "Blog deleted",200

@app.route("/api/me/blogs",methods=["GET"])
@jwt_required()
def get_curruserblogs():

    user_id = get_jwt_identity()

    currbloglist = list(blogs.find({"author_id":user_id}))

    for blogitem in currbloglist:
        blogitem["_id"] = str(blogitem["_id"])

    if not currbloglist:
        return "No blogs for this user", 404

    return currbloglist

@app.route("/api/blogs/<blog_id>/like", methods=["POST"])
@jwt_required()
def add_like(blog_id):
    user_id = get_jwt_identity()

    blog = blogs.find_one({"blog_id": id})

    if not blog:
        return {"Message": "Blog doesnt exist"}, 404

    existing_like = likes.find_one({
        "blog_id": id,
        "user_id": user_id
    })

    if existing_like:
        return {"Message": "Blog already liked"}, 400

    likes.insert_one({
        "blog_id": blog_id,
        "user_id": user_id
    })

    return {"Message": "Blog liked successfully"}, 201


@app.route("/api/blogs/<blog_id>/like", methods=["DELETE"])
@jwt_required()
def remove_like(blog_id):
    user_id = get_jwt_identity()

    result = likes.delete_one({
        "blog_id": blog_id,
        "user_id": user_id
    })

    if result.deleted_count == 0:
        return {"Message": "Like doesnt exist"}, 404

    return {"Message": "Like removed successfully"},200


@app.route("/<blog_id>/comments",methods=["GET"])
@jwt_required()
def get_comments(blog_id):
    l = list(comments.find({"post_id":blog_id},{"_id":0}))

    if not l:
        return {"message":"List not found"} , 404

    return l

        

@app.route("/<blog_id>/comments",methods=["POST"])
@jwt_required()
def post_comment(blog_id):
    body = request.json

    if not body["comment"]:
        return {"message":"No comment present"} , 404

    body["post_id"] = blog_id


    comments.insert_one(body)

    return {"message":"Comment added"},201


if __name__  == "__main__":
    app.run(debug=True)



