from models import User
from database import db_session
from . import DataNotFoundException, BaseDao

class UserDAO(BaseDao):
    def __init__(self):
        pass

    def list(self):
        return User.query.all()
    
    def _get(self,name):
        u = User.query.filter(User.name == name).first()
        if u is None:
            raise DataNotFoundException
        return u

    def get(self, name):
        return self._get(name)

    def create(self, data: dict):
        u = User()
        for k in data.keys():
            if k == "password":
                u.set_password(data[k])
                continue
            setattr(u, k, data[k])
        db_session.add(u)
        self._try_commint()
        return u

    def update(self, name, data):
        u = self._get(name)
        for k in data.keys():
            if k == "password":
                u.set_password(data[k])
                continue
            setattr(u, k, data[k])
        db_session.add(u)
        self._try_commint()
        return u

    def delete(self, name):
        u = self._get(name)
        db_session.delete(u)
        self._try_commint()
