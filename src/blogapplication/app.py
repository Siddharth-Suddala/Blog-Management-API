from flask import Flask
from flask_jwt_extended import JWTManager

from .auth import auth_bp
from .blogs import blog_bp


app = Flask(__name__)

app.config["JWT_SECRET_KEY"] = "weggurhfurhiguirkljsjgkgksls"

jwt = JWTManager(app)

app.register_blueprint(auth_bp)
app.register_blueprint(blog_bp)


if __name__ == "__main__":
    app.run(debug=True)