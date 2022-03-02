from flask import app, wrappers
from flask_restplus import Api
from functools import wraps
from flask import request
from collections import OrderedDict
from werkzeug.exceptions import abort
from models import User
import auth as auth_model


def wrapresp(func):
    exmpet_paths = ["/api/swagger.json"]
    @wraps(func)
    def wrapper(*args, **kwargs):
        __data = func(*args, **kwargs)
        msg = f"成功"
        if isinstance(__data, tuple):
            data = __data[0]
            msg = __data[1]
        else:
            data = __data
        # data, code = a.json, a.status

        if request.path in exmpet_paths:
            return data

        return OrderedDict(
            status=0,
            msg=msg,
            data=data
        ), 200
    return wrapper

api = Api(doc="/docs", prefix="/api", version='1.0', title='SBGL API',
    description="设备管理API接口",)

# swagger 需要basic认证
api.authorizations = dict(
    basicAuth=dict(type="basic")
)
api.security = dict(
    basicAuth=[]
)
# api.error_handlers = []

from flask_restplus import Resource as OringalResource
from utils import raise_error_api

class Resource(OringalResource):

    def __init__(self, api, *args, **kwargs):
        super().__init__(api=api, *args, **kwargs)

    @raise_error_api(captures=(auth_model.LoginFailedException,), err_msg="登录失败，请尝试重新登录！")
    @raise_error_api(captures=(auth_model.PermissionDeniedException,), err_msg="权限被拒绝")
    @auth_model.basic_auth.login_required
    @wrapresp
    def dispatch_request(self, *args, **kwargs):
        return super().dispatch_request(*args, **kwargs)

from .user import ns as user_ns
from .role import ns as role_ns
from .permission import ns as permission_ns
from .asset import ns as asset_ns
from .cabinet import ns as cabinet_ns
from .dc import ns as dc_ns