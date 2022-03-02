from . import api, Resource as _Resource
from flask_restplus import Api, fields
from dao.user import UserDAO
from dao import DataNotFoundException, DataBaseCommitException
from utils import raise_error_api
from flask import request
from models import User as User_M
from auth.utils import need_permission
from models import Permission_Enum

user = api.model('User', {
    "name": fields.String(required=True, readonly=True),
    "realname": fields.String(),
    "tel": fields.String(),
    "email": fields.String(),
    "desc": fields.String(),
    "role_name": fields.String()
})
page_user = api.model('PageUser',{
    "start": fields.Integer(required=True),
    "limit": fields.Integer(required=True),
    "count": fields.Integer(required=True),
    "previous": fields.String(required=True),
    "next": fields.String(required=True),
    "results":fields.List(fields.Nested(user))
})
ns = api.namespace('user', description='User operations')
# ns.default_error_handler

class Resource(_Resource):

    @raise_error_api(captures=(DataNotFoundException,), err_msg="用户没有找到")
    @raise_error_api(captures=(DataBaseCommitException,), err_msg="数据查询异常")
    def dispatch_request(self, *args, **kwargs):
        return super().dispatch_request(*args, **kwargs)

DAO = UserDAO()

@ns.route('/')
class UserList(Resource):

    @need_permission(Permission_Enum.user_list.value)
    @ns.doc("list_user")
    @ns.marshal_list_with(user)
    @ns.param("filter[*]", description="全局搜索")
    # @ns.param("limit", description="页面数据大小")
    def get(self):
        a = DAO.list()
        filter_all = request.args.get("filter[*]", "*")
        if filter_all == "*":
            return a
        else:
            res = []
            for i in a:
                for x in [a for a in dir(i) if not a.startswith('__') and not callable(getattr(i, a))]:
                    if x == "passowrd":
                        continue
                    if str(getattr(i,str(x))).__contains__(filter_all):
                        res.append(i)
                        break
            return res

    @need_permission(Permission_Enum.user_create.value)
    @ns.doc('create_user')
    @ns.expect(user)
    @ns.marshal_with(user)
    def post(self):
        return DAO.create(api.payload)


@ns.route("name")
@ns.param("name", "用户名")
@ns.route('/<name>')
class User(Resource):

    @need_permission(Permission_Enum.user_delete.value)
    @ns.doc('get_user')
    @ns.marshal_with(user)
    def get(self, name):
        return DAO.get(name)

    @need_permission(Permission_Enum.user_delete.value)
    @ns.doc("delete_user")
    def delete(self, name):
        DAO.delete(name)
        return {}

    @need_permission(Permission_Enum.user_update.value)
    @ns.expect(user)
    @ns.marshal_with(user)
    def put(self, name):
        return DAO.update(name, api.payload)
