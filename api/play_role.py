from attr import validate
from . import api, Resource as _Resource
from flask_restplus import fields
from dao.play_role import PlayRoleDAO, SubPlayRoleDAO
from dao import DataNotFoundException, DataBaseCommitException, RequestFilterException
from utils import raise_error_api
from flask import request

_model = api.model('Prop', {
    "name": fields.String(),
    "type": fields.String(),
    "value": fields.String()
})

role = api.model('PlayRole', {
    "name": fields.String(required=True),
    "path": fields.String(required=True),
    "play_args": fields.List(fields.Nested(_model), required=True)
})

sub_role = api.model('SubPlayRole', {
    "name": fields.String(required=True),
    "main_name": fields.String(required=True),
    "play_args": fields.List(fields.Nested(_model), required=True),
    "hosts": fields.List(fields.String()),
    "last_update":fields.DateTime(),
    "last_execution":fields.DateTime(),
})

page_sub_role = api.model('PageSubRole',{
    "start": fields.Integer(required=True),
    "limit": fields.Integer(required=True),
    "count": fields.Integer(required=True),
    "previous": fields.String(required=True),
    "next": fields.String(required=True),
    "results":fields.List(fields.Nested(sub_role))
})

ns = api.namespace('play_role', description='Play Role operations', validate=True)
# ns.default_error_handler

class Resource(_Resource):

    @raise_error_api(captures=(DataNotFoundException,), err_msg="权限或者角色没有找到")
    @raise_error_api(captures=(DataBaseCommitException,), err_msg="数据查询异常")
    @raise_error_api(captures=(RequestFilterException,), err_msg="数据校验异常")
    def dispatch_request(self, *args, **kwargs):
        return super().dispatch_request(*args, **kwargs)

DAO = PlayRoleDAO()
Sub_DAO = SubPlayRoleDAO()

@ns.route('/')
class PlayRoleList(Resource):
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

@ns.route('/sub')
class SubPlayRoleList(Resource):
    @ns.doc("list_sub_play_role")
    @ns.marshal_list_with(page_sub_role)
    @ns.param("start", description="分页开始")
    @ns.param("limit", description="页面数据大小")
    def get(self):
        start = request.args.get("start", 1)
        limit = request.args.get("limit", 20)
        return DAO.get_paginated_list(url=api.url_for(self), results=Sub_DAO.list(), start=start, limit=limit) 
    
    @ns.doc('create_sub_play_role')
    @ns.expect(sub_role)
    @ns.marshal_with(sub_role)
    def post(self):
        return Sub_DAO.create(api.payload)

@ns.route("name")
@ns.param("name", "角色名")
@ns.route('/sub/<name>')
class SubRole(Resource):

    @ns.doc('get_sub_play_role')
    @ns.marshal_with(sub_role)
    def get(self, name):
        return Sub_DAO.get(name)
    
    @ns.doc("update_sub_play_role")
    @ns.expect(sub_role)
    @ns.marshal_with(sub_role)
    def put(self, name):
        return Sub_DAO.update(name, api.payload)

    @ns.doc("delete_sub_play_role")
    def delete(self, name):
        Sub_DAO.delete(name)
        return {}
