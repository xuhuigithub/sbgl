from models import SubPlayRole
from dao import BaseDao
from api.play_role import page_sub_role, sub_role
from flask_restplus import marshal
if __name__ == "__main__": 
    from app import app
    dap = BaseDao()
    with app.app_context():
        # a = dap.get_paginated_list(url="test", results=SubPlayRole.query.all(), start=1, limit=20)
        
        # print(marshal(a, page_sub_role))
        c = SubPlayRole.query.all()[0]
        c = marshal(c, sub_role)
        print(c)