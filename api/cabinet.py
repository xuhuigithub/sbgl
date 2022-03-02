from sqlalchemy.orm.base import attribute_str
from . import api, Resource as _Resource
from flask_restplus import Api, fields
from dao.cabinet import CabinetDAO
from dao import DataNotFoundException, DataBaseCommitException
from utils import raise_error_api
from flask import request
from models import User as User_M
from auth.utils import need_permission
from models import Permission_Enum

cabinet = api.model('Cabinet', {
    "id": fields.String(required=True, readonly=True),
    "name": fields.String(),
    "dc_name": fields.String(),
    "dc": fields.String(attribute="dc.name"),
})
page_cabinet = api.model('PageCabinet',{
    "start": fields.Integer(required=True),
    "limit": fields.Integer(required=True),
    "count": fields.Integer(required=True),
    "previous": fields.String(required=True),
    "next": fields.String(required=True),
    "results":fields.List(fields.Nested(cabinet))
})
ns = api.namespace('cabinet', description='Cabinet operations')
# ns.default_error_handler

class Resource(_Resource):

    @raise_error_api(captures=(DataNotFoundException,), err_msg="机柜没有找到")
    @raise_error_api(captures=(DataBaseCommitException,), err_msg="数据查询异常")
    def dispatch_request(self, *args, **kwargs):
        return super().dispatch_request(*args, **kwargs)

DAO = CabinetDAO()

@ns.route('/')
class CabinetList(Resource):

    @need_permission(Permission_Enum.cabinet_list.value)
    @ns.doc("list_cabinet")
    @ns.marshal_list_with(cabinet)
    @ns.param("filter[name]", description="按机柜名称搜索")
    # @ns.param("limit", description="页面数据大小")
    def get(self):
        # start = request.args.get("start", 1)
        # limit = request.args.get("limit", 20)
        # return DAO.get_paginated_list(url=api.url_for(self), results=DAO.list(), start=start, limit=limit)
        return DAO.list() 

    @need_permission(Permission_Enum.cabinet_create.value)    
    @ns.doc('create_cabinet')
    @ns.expect(cabinet)
    @ns.marshal_with(cabinet)
    def post(self):
        return DAO.create(api.payload)


@ns.route("id")
@ns.param("id", "机柜ID")
@ns.route('/<id>')
class Cabinet(Resource):

    @need_permission(Permission_Enum.cabinet_list.value)    
    @ns.doc('get_cabinet')
    @ns.marshal_with(cabinet)
    def get(self, id):
        return DAO.get(id)

    @need_permission(Permission_Enum.cabinet_delete.value)    
    @ns.doc("delete_cabinet")
    def delete(self, id):
        DAO.delete(id)
        return {}

    @need_permission(Permission_Enum.cabinet_update.value)   
    @ns.expect(cabinet)
    @ns.marshal_with(cabinet)
    def put(self, id):
        return DAO.update(id, api.payload)
