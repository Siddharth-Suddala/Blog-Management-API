from flask import Blueprint, request
from flask_jwt_extended import (
    jwt_required,
    get_jwt_identity,
    verify_jwt_in_request
)
from datetime import datetime
from uuid import uuid4

from .database import blogs, likes, comments


blog_bp = Blueprint(
    "blog",
    __name__,
    url_prefix="/api"
)


def generate_id(prefix):
    return prefix + "-" + str(uuid4())

@blog_bp.route("/blogs", methods=["POST"])
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
        "updated_at": now
    })

    return {
        "message": "Blog created",
        "blog_id": blog_id
    }, 201


@blog_bp.route("/blogs/<blog_id>", methods=["PUT"])
@jwt_required()
def edit_blog(blog_id):

    data = request.json

    title = data.get("title")
    content = data.get("content")

    if not title or not content:
        return "Missing data", 400

    user_id = get_jwt_identity()

    blog = blogs.find_one({
        "blog_id": blog_id
    })

    if not blog:
        return "Blog isn't there", 404

    if blog["author_id"] != user_id:
        return "Access denied to blog", 403

    now = datetime.now()

    blogs.update_one(
        {"blog_id": blog_id},
        {
            "$set": {
                "title": title,
                "content": content,
                "updated_at": now
            }
        }
    )

    return "Blog updated", 200

@blog_bp.route("/blogs/<blog_id>/publish", methods=["PATCH"])
@jwt_required()
def publish_blog(blog_id):

    blog = blogs.find_one({
        "blog_id": blog_id
    })

    if not blog:
        return "Blog doesn't exist", 404

    user_id = get_jwt_identity()

    if blog["author_id"] != user_id:
        return "Access denied to blog", 403

    if blog["status"] != "draft":
        return "Blog is already published", 400

    now = datetime.now()

    blogs.update_one(
        {"blog_id": blog_id},
        {
            "$set": {
                "published_at": now,
                "status": "published"
            }
        }
    )

    return "Blog published", 200

@blog_bp.route("/blogs/<blog_id>", methods=["GET"])
def get_blog(blog_id):

    blog = blogs.find_one({
        "blog_id": blog_id
    })

    if not blog:
        return "Blog doesn't exist", 404

    if blog["status"] == "draft":

        verify_jwt_in_request(optional=True)

        user_id = get_jwt_identity()

        if user_id != blog["author_id"]:
            return "Blog doesn't exist", 404

    blog["_id"] = str(blog["_id"])

    return blog, 200

@blog_bp.route("/blogs", methods=["GET"])
def get_blogs():

    published_blogs = list(
        blogs.find({
            "status": "published"
        })
    )

    if not published_blogs:
        return "No blogs found", 404

    for blog in published_blogs:
        blog["_id"] = str(blog["_id"])

    return published_blogs, 200

@blog_bp.route("/blogs/<blog_id>", methods=["DELETE"])
@jwt_required()
def delete_blog(blog_id):

    blog = blogs.find_one({
        "blog_id": blog_id
    })

    if not blog:
        return "Blog doesn't exist", 404

    user_id = get_jwt_identity()

    if user_id != blog["author_id"]:
        return "You don't have permission to delete", 403

    blogs.delete_one({
        "blog_id": blog_id
    })

    return "Blog deleted", 200

@blog_bp.route("/me/blogs", methods=["GET"])
@jwt_required()
def get_curruserblogs():

    user_id = get_jwt_identity()

    currbloglist = list(
        blogs.find({
            "author_id": user_id
        })
    )

    if not currbloglist:
        return "No blogs for this user", 404

    for blogitem in currbloglist:
        blogitem["_id"] = str(blogitem["_id"])

    return currbloglist, 200


@blog_bp.route("/blogs/<blog_id>/like", methods=["POST"])
@jwt_required()
def add_like(blog_id):

    user_id = get_jwt_identity()

    blog = blogs.find_one({
        "blog_id": blog_id
    })

    if not blog:
        return {
            "message": "Blog doesnt exist"
        }, 404

    existing_like = likes.find_one({
        "blog_id": blog_id,
        "user_id": user_id
    })

    if existing_like:
        return {
            "message": "Blog already liked"
        }, 400

    likes.insert_one({
        "blog_id": blog_id,
        "user_id": user_id
    })

    return {
        "message": "Blog liked successfully"
    }, 201



@blog_bp.route("/blogs/<blog_id>/like", methods=["DELETE"])
@jwt_required()
def remove_like(blog_id):

    user_id = get_jwt_identity()

    result = likes.delete_one({
        "blog_id": blog_id,
        "user_id": user_id
    })

    if result.deleted_count == 0:
        return {
            "message": "Like doesnt exist"
        }, 404

    return {
        "message": "Like removed successfully"
    }, 200


@blog_bp.route("/blogs/<blog_id>/comments", methods=["GET"])
@jwt_required()
def get_comments(blog_id):

    comment_list = list(
        comments.find(
            {"post_id": blog_id},
            {"_id": 0}
        )
    )

    if not comment_list:
        return {
            "message": "List not found"
        }, 404

    return comment_list, 200


@blog_bp.route("/blogs/<blog_id>/comments", methods=["POST"])
@jwt_required()
def post_comment(blog_id):

    body = request.json

    if not body or not body.get("comment"):
        return {
            "message": "No comment present"
        }, 400

    body["post_id"] = blog_id

    comments.insert_one(body)

    return {
        "message": "Comment added"
    }, 201