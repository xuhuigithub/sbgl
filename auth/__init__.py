from flask import Blueprint
from flask.json import jsonify
from flask import request
from models import User
from utils import raise_error_api
from flask_restplus import marshal
from flask_httpauth import HTTPBasicAuth

auth = Blueprint("auth", __name__)

class LoginFailedException(Exception):
    pass

class PermissionDeniedException(Exception):
    pass

@auth.route("/api/login", methods=["POST"])
@raise_error_api(captures=(LoginFailedException, TypeError, KeyError),err_msg="登录失败，用户名或者密码错误")
def login():
    from api.user import user

    status = 0
    # raise type error
    name = request.json["user_name"]
    password = request.json["password"]
    u  = User.query.filter(User.name == name).first()
    if not u:
        raise LoginFailedException
    
    if not u.verify_password(password):
        raise LoginFailedException
    
    msg = f"登录成功，欢迎回来 {u.name}" 
    data = marshal(u, user)
    return jsonify(
        dict(
            status=status, msg=msg, data=dict(permissions=[p.name for p in u.role.permissions], **data)
        )
    )


basic_auth = HTTPBasicAuth()

@basic_auth.verify_password
def verify_password(username, password):
    u  = User.query.filter(User.name == username).first()
    if u and u.verify_password(password):
        return u
    else:
        raise LoginFailedException

auth_pl = Blueprint('auth', __name__)