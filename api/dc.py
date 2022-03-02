from . import api, Resource as _Resource
from flask_restplus import  fields
from dao.dc import DCDAO

dc = api.model('dc', {
    "name": fields.String(required=True, readonly=True),
})

ns = api.namespace('dc', description='DC operations')
# ns.default_error_handler


DAO = DCDAO()

@ns.route('/')
class UserList(_Resource):

    @ns.doc("list_dc")
    @ns.marshal_list_with(dc)
    # @ns.param("limit", description="页面数据大小")
    def get(self):
        return DAO.list()

