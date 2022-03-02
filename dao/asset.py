from re import U

from sqlalchemy.sql.base import NO_ARG
from models import Assets, AssetFamily_Enum
from database import db_session
from . import DataNotFoundException, BaseDao, IllegalStateException
from collector.ansible_collector import Collector
from sqlalchemy import or_

class AssetDAO(BaseDao):
    def __init__(self):
        pass

    def __validate_data(self, data):
        # raise ValueError if not a valid Role_Enum
        family = data.get("family")
        if not family or not AssetFamily_Enum(family):
            raise IllegalStateException

        
    def list(self):
        query = Assets.query
        query = self.handle_filter(query=query)
        return query.all()
    
    def _get(self,sn):
        u = Assets.query.filter(Assets.sn == sn).first()
        if u is None:
            raise DataNotFoundException
        return u

    def get(self, name):
        return self._get(name)

    def create(self, data: dict):
        self.__validate_data(data)
        u = Assets()
        for k in data.keys():
            setattr(u, k, data[k])
        c = Collector(u)
        c.collect()
        db_session.add(u)
        self._try_commint()
        return u

    def update(self, name, data):
        u = self._get(name)
        self.__validate_data(data)

        for k in data.keys():
            setattr(u, k, data[k])
        db_session.add(u)
        self._try_commint()
        return u

    def delete(self, name):
        u = self._get(name)
        db_session.delete(u)
        self._try_commint()


    def handle_sn(self, query, value):
        return query.filter(Assets.sn == value)

    def handle_ip(self, query,value):
        return query.filter(Assets.ip == value)

    def handle_user(self, query,value):
        return query.filter(Assets.user_name == value)
    
    def handle_name(self, query,value):
        return query.filter(or_(Assets.ip.like(f"%{value}%"),Assets.sn.like(f"%{value}%")))