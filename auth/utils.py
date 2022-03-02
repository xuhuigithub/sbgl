from functools import wraps
from flask import request
from flask.wrappers import Request
from models import User
from flask import abort
from . import PermissionDeniedException, LoginFailedException


# 接口使用Basic认证
def need_permission(permission, except_user=[]):
    def outer(f):
        @wraps(f)
        def inner(*args, **kwargs):
            user : User = User.query.filter_by(name=request.authorization.username).first()
            if not user.verify_password(request.authorization.password):
                raise LoginFailedException
            if request.authorization.username in except_user:
                return f(*args, **kwargs)
            if not user.has_permission(permission):
                raise PermissionDeniedException
            return f(*args, **kwargs)
        return inner
    return outer