import json
import datetime
from operator import mod
from typing import List
from unicodedata import name

from sqlalchemy import delete
from models import PlayRole, SubPlayRole
from database import db_session
from . import DataNotFoundException, BaseDao, RequestFilterException
from sqlalchemy import or_

def deserializeSub(model: SubPlayRole):
    # model.main.play_args = json.loads(model.main.play_args)
    if  isinstance(model.play_args, str):
        model.play_args = json.loads(model.play_args)
    if  isinstance(model.hosts, str):
        model.hosts =  json.loads(model.hosts)
    return model

def serializeSub(model: SubPlayRole):
        if  isinstance(model.play_args, List):
            model.play_args = json.dumps(model.play_args)
        if  isinstance(model.hosts, List):
            model.hosts =  json.dumps(model.hosts)
    #  model.main.play_args = json.dumps(model.main.play_args)
        return model

class PlayRoleDAO(BaseDao):
    mapping = {
        "String": str,
        "Int": int,
        "Boolean": bool
    }
    def __init__(self):
        pass

    def list(self):
        def process(u):
            u.play_args = json.loads(u.play_args)
            return u
        _all = PlayRole.query.all()
        return list(map(process, _all))

    
    def validate_data(self, data):
            try:
                data['name']
                data['path']
                names = []
                for i in data['play_args']:
                    names.append(i["name"])
                    if i["type"] == "Int": 
                        assert isinstance(int(i["value"]), self.mapping[i["type"]])
                        continue
                    if i["type"] == "Boolean": 
                        assert i["value"] in ["true", "false"]
                        continue
                    assert isinstance(i["value"], self.mapping[i["type"]])
                    # 不允许出现重复的变量
                assert len(names) == len(set(names))
            except Exception:
                raise RequestFilterException

    
    def _get(self,name):
        u = PlayRole.query.filter(PlayRole.name == name).first()
        if u is None:
            raise DataNotFoundException
        u.play_args = json.loads(u.play_args)
        return u

    def get(self, name):
        return self._get(name)

    def create(self, data: dict):
        self.validate_data(data)
        u = PlayRole()
        for k in data.keys():
            if k == "play_args":
                setattr(u, k, json.dumps(data[k]))
                continue
            setattr(u, k, data[k])

        db_session.add(u)
        self._try_commint()
        u.play_args = json.loads(u.play_args)
        return u

    def update(self, name, data):
        u = self._get(name)
        self.validate_data(data)

        # 得到play_args 的不同
        
        for i in u.sub_roles:
            i: SubPlayRole
            j = json.loads(i.play_args)
            for index,c in enumerate(j):
                # 删除多余变量
                if c not in data['play_args']:
                    del j[index]
                
            # 新增加变量赋值默认值
            for d in data['play_args']:
                if d not in j:
                    j.append(d)
            
            i.play_args =  json.dumps(j)
            i.main.play_args = json.dumps(i.main.play_args)
            db_session.add(serializeSub(i))
            self._try_commint()

        for k in data.keys():
            if k == "play_args":
                setattr(u, k, json.dumps(data[k]))
                continue
            setattr(u, k, data[k])

        db_session.add(u)
        self._try_commint()
        u.play_args = json.loads(u.play_args)
        return u

    def delete(self, name):
        u = self._get(name)
        db_session.delete(u)
        self._try_commint()

class SubPlayRoleDAO(BaseDao):
    def __init__(self, o_db_session=None):
        if o_db_session:
            self.db_session = o_db_session
        else:
            self.db_session = db_session

    def get(self, name):
        return self._get(name)

    def list(self):
        query = SubPlayRole.query
        query = self.handle_filter(query=query)
        return list(map(self.deserialize, query.all()))
    
    def deserialize(self, model: SubPlayRole):
        # model.main.play_args = json.loads(model.main.play_args)
        model.play_args = json.loads(model.play_args)
        model.hosts =  json.loads(model.hosts)
        return model

    def serialize(self, model: SubPlayRole):
         model.play_args = json.dumps(model.play_args)
         model.hosts =  json.dumps(model.hosts)
        #  model.main.play_args = json.dumps(model.main.play_args)
         return model

    def _get(self, name):
        u = SubPlayRole.query.filter(SubPlayRole.name == name).first()
        if u is None:
            raise DataNotFoundException
        return self.deserialize(u)
    
    def create(self, data: dict):
        # self.validate_data(data)
        u = SubPlayRole()
        for k in data.keys():
            setattr(u, k, data[k])
        setattr(u, "last_update", datetime.datetime.now())
        u = self.serialize(u)
        self.db_session.add(u)
        self._try_commint()
        return self.deserialize(u)
    
    def update(self, name, data):
        u = self._get(name)
        for k in data.keys():
            if k == "main_name":
                continue
            setattr(u, k, data[k])
        setattr(u, "last_update", datetime.datetime.now())
        u = self.serialize(u)
        self.db_session.add(u)
        self._try_commint()
        return self.deserialize(u)

    def delete(self, name):
        u = self._get(name)
        u = self.serialize(u)
        self.db_session.delete(u)
        self._try_commint()

    def handle_main_name(self, query, value):
        return query.filter(SubPlayRole.main_name == value)

    def handle_ip(self, query,value):
        return query.filter(or_(SubPlayRole.hosts.like(f"%{value},"),SubPlayRole.hosts.like(f"%{value}")))

    def handle_name(self, query,value):
        return query.filter(or_(SubPlayRole.main_name.like(f"%{value}%"),SubPlayRole.name.like(f"%{value}%")))