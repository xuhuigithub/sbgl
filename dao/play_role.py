import json
from models import PlayRole
from database import db_session
from . import DataNotFoundException, BaseDao, RequestFilterException


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

    
    def __validate_data(self, data):
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
        self.__validate_data(data)
        u = PlayRole()
        for k in data.keys():
            if k == "play_args":
                setattr(u, k, json.dumps(data[k]))
                break
            setattr(u, k, data[k])

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
