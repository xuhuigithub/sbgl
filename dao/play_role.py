import json
import datetime
from operator import mod

from sqlalchemy import delete
from models import PlayRole, SubPlayRole
from database import db_session
from . import DataNotFoundException, BaseDao, RequestFilterException
from sqlalchemy import or_


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
                for i in data['play_args']:
                    i["name"]
                    if i["type"] == "Int": 
                        assert isinstance(int(i["value"]), self.mapping[i["type"]])
                        continue
                    if i["type"] == "Boolean": 
                        assert i["value"] in ["true", "false"]
                        continue
                    assert isinstance(i["value"], self.mapping[i["type"]])
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
        return u

    def update(self, name, data):
        u = self._get(name)
        self.validate_data(data)

        for k in data.keys():
            setattr(u, k, data[k])
        db_session.add(u)
        self._try_commint()
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