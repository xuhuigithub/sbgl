from . import api, Resource as _Resource
from flask_restplus import fields
from dao.play_role import PlayRoleDAO
from dao import DataNotFoundException, DataBaseCommitException, RequestFilterException
from utils import raise_error_api

_model = api.model('NSDevice', {
    "name": fields.String(),
    "type": fields.String(),
    "value": fields.String()
})

role = api.model('PlayRole', {
    "name": fields.String(required=True),
    "path": fields.String(required=True),
    "play_args": fields.List(fields.Nested(_model), required=True)
})

ns = api.namespace('play_role', description='Play Role operations')
# ns.default_error_handler

class Resource(_Resource):

    @raise_error_api(captures=(DataNotFoundException,), err_msg="权限或者角色没有找到")
    @raise_error_api(captures=(DataBaseCommitException,), err_msg="数据查询异常")
    @raise_error_api(captures=(RequestFilterException,), err_msg="数据校验异常")
    def dispatch_request(self, *args, **kwargs):
        return super().dispatch_request(*args, **kwargs)

DAO = PlayRoleDAO()

@ns.route('/')
class RoleList(Resource):
    @ns.doc("list_play_role")
    @ns.marshal_list_with(role)
    def get(self):
        return DAO.list() 

    @ns.doc('create_play_role')
    @ns.expect(role)
    @ns.marshal_with(role)
    def post(self):
        return DAO.create(api.payload)


@ns.route("name")
@ns.param("name", "角色名")
@ns.route('/<name>')
class Role(Resource):

    @ns.doc('get_play_role')
    @ns.marshal_with(role)
    def get(self, name):
        return DAO.get(name)

    # @ns.doc("delete_role")
    # def delete(self, name):
    #     DAO.delete(name)
    #     return {}

    # @ns.expect(role)
    # @ns.marshal_with(role)
    # def put(self, name):
    #     return DAO.update(name, api.payload)