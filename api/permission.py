from . import api, Resource as _Resource
from flask_restplus import fields
from dao.permission import PermissionDAO
from dao import DataNotFoundException, DataBaseCommitException
from utils import raise_error_api


permission = api.model('Permission', {
    "id": fields.String(required=True, readonly=True),
    "name": fields.String(required=True, readonly=True)
})

ns = api.namespace('permission', description='Permission operations')
# ns.default_error_handler

class Resource(_Resource):

    @raise_error_api(captures=(DataNotFoundException,), err_msg="用户没有找到")
    @raise_error_api(captures=(DataBaseCommitException,), err_msg="数据查询异常")
    @raise_error_api(captures=(ValueError,), err_msg="数据校验异常")
    def dispatch_request(self, *args, **kwargs):
        return super().dispatch_request(*args, **kwargs)

DAO = PermissionDAO()

@ns.route('/')
class PermissionList(Resource):
    @ns.doc("list_permission")
    @ns.marshal_list_with(permission)
    def get(self):
        return DAO.list() 



@ns.route("id")
@ns.param("id", "permission id")
@ns.route('/<id>')
class User(Resource):

    @ns.doc('get_permission')
    @ns.marshal_with(permission)
    def get(self, name):
        return DAO.get(name)
