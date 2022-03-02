from models import Permission_Enum, Role, Role_Enum
from database import db_session
from . import DataNotFoundException, BaseDao
from .permission import PermissionDAO

pdao = PermissionDAO()

class RoleDAO(BaseDao):
    def __init__(self):
        pass

    def list(self):
        return Role.query.all()
    
    def __validate_data(self, data):
        # raise ValueError if not a valid Role_Enum
        for i in data.get("permissions"):
            p_name = pdao.get(i).name

            Permission_Enum(p_name).value
    
    def _get(self,name):
        u = Role.query.filter(Role.name == name).first()
        if u is None:
            raise DataNotFoundException
        return u

    def get(self, name):
        return self._get(name)

    # def create(self, data: dict):
    #     self.__validate_rolename(data)
    #     u = Role()
    #     for k in data.keys():
    #         setattr(u, k, data[k])
    #     db_session.add(u)
    #     self._try_commint()
    #     return u

    def update(self, name, data):
        self.__validate_data(data)
        u = self._get(name)
        for k in data.keys():
            if k == "permissions":
                ps = []
                for p in data.get("permissions"):
                    p = pdao.get(p)
                    ps.append(p)
                u.permissions = ps
                continue
            setattr(u, k, data[k])
        db_session.add(u)
        self._try_commint()
        return u

    # def delete(self, name):
    #     u = self._get(name)
    #     db_session.delete(u)
    #     self._try_commint()
