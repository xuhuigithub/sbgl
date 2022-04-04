from models import Terminal
from database import db_session
from . import DataNotFoundException, BaseDao

class TerminalDAO(BaseDao):
    def __init__(self):
        pass

    def list(self):
        return Terminal.query.all()
    
    def _get(self,  uuid):
        u = Terminal.query.filter(Terminal.id == uuid).first()
        if u is None:
            raise DataNotFoundException
        return u
    
    def get_by_ppid(self, ppid):
        u = Terminal.query.filter(Terminal.p_pid == ppid).all()
        return u

    def get(self, uuid):
        return self._get(uuid)

    def create(self, data: dict):
        u = Terminal()
        for k in data.keys():
            if k == "password":
                u.set_password(data[k])
                continue
            setattr(u, k, data[k])
        db_session.add(u)
        self._try_commint()
        return u

    def update(self, uuid, data):
        u = self._get(uuid)
        for k in data.keys():
            setattr(u, k, data[k])
        db_session.add(u)
        self._try_commint()
        return u

    def delete(self, name):
        u = self._get(name)
        db_session.delete(u)
        self._try_commint()
