import datetime

from sqlalchemy.util.langhelpers import attrsetter
from . import api, Resource as _Resource
from flask_restplus import Api, fields
from dao.asset import AssetDAO, IllegalStateException
from dao import DataNotFoundException, DataBaseCommitException,RequestFilterException
from utils import raise_error_api
from flask import request
from auth.utils import need_permission
from models import Permission_Enum
from collector import ansible_collector

mac = api.model('NSDevice', {
    "name": fields.String(),
    "address": fields.String(),
    "mac": fields.String(),
    "module": fields.String()
})


asset = api.model('Asset', {
    "sn": fields.String(),
    "real_sn": fields.String(),
    "created_time": fields.DateTime(readonly=True),
    "model": fields.String(),
    "disk": fields.String(),
    "comment": fields.String(),
    "user_name": fields.String(),
    "port": fields.String(),
    "mem": fields.String(),
    "cpu": fields.String(),
    "mac": fields.String(),
    "system": fields.String(),
    "ip": fields.String(),
    "family": fields.String(),
    "cabinet": fields.String(attribute="cabinet.name"),
    "dc": fields.String(attribute="cabinet.dc_name"),
    "user_nums": fields.Integer(),
    "last_seen": fields.String(),
    "network_devices": fields.List(fields.Nested(mac))
})
page_asset = api.model('PageAsset',{
    "start": fields.Integer(required=True),
    "limit": fields.Integer(required=True),
    "count": fields.Integer(required=True),
    "previous": fields.String(required=True),
    "next": fields.String(required=True),
    "results":fields.List(fields.Nested(asset))
})
ns = api.namespace('asset', description='Asset operations')
# ns.default_error_handler

class Resource(_Resource):

    @raise_error_api(captures=(DataNotFoundException,), err_msg="资产没有找到")
    @raise_error_api(captures=(DataBaseCommitException,RequestFilterException), err_msg="数据查询异常")
    @raise_error_api(captures=(ansible_collector.CollectorException,), err_msg="数据采集异常,请检查服务器的联通性")
    @raise_error_api(captures=(IllegalStateException,), err_msg="参数异常")
    def dispatch_request(self, *args, **kwargs):
        return super().dispatch_request(*args, **kwargs)

DAO = AssetDAO()

@ns.route('/')
class AssetList(Resource):
    @need_permission(Permission_Enum.asset_list.value)
    @ns.doc("list_asset")
    @ns.marshal_list_with(page_asset)
    @ns.param("start", description="分页开始")
    @ns.param("limit", description="页面数据大小")
    def get(self):
        start = request.args.get("start", 1)
        limit = request.args.get("limit", 20)
        return DAO.get_paginated_list(url=api.url_for(self), results=DAO.list(), start=start, limit=limit) 

    @need_permission(Permission_Enum.asset_create.value)
    @ns.doc('create_asset')
    @ns.expect(asset)
    @ns.marshal_with(asset)
    @ns.param("auto_populate", description="是否自动采集")
    def post(self):
        data = api.payload
        a = data.get("created_time", datetime.datetime.now())
        a = fields.DateTime().parse(a)
        data["created_time"] = a
        auto_populate = request.args.get('auto_populate', 'false')
        return DAO.create(data, auto_populate),"创建资产成功"


@ns.route("sn")
@ns.param("sn", "资产sn编码")
@ns.route('/<sn>')
class Asset(Resource):
    @need_permission(Permission_Enum.asset_list.value)
    @ns.doc('get_asset')
    @ns.marshal_with(asset)
    def get(self, sn):
        a = DAO.get(sn)
        # a.mac = [
        #     dict(
        #         name="lo",
        #         address="127.0.0.1",
        #         mac="loop"
        #     )
        # ]
        return a

    @need_permission(Permission_Enum.asset_delete.value)
    @ns.doc("delete_asset")
    def delete(self, sn):
        DAO.delete(sn)
        return {}

    @need_permission(Permission_Enum.asset_update.value)
    @ns.expect(asset)
    @ns.marshal_with(asset)
    @ns.param("auto_populate", description="是否自动采集")
    def put(self, sn):
        auto_populate = request.args.get('auto_populate', 'false')
        return DAO.update(sn, api.payload,auto_populate)