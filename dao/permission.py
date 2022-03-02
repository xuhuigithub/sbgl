from models import Permission
from . import DataNotFoundException, BaseDao

class PermissionDAO(BaseDao):
    def __init__(self):
        pass

    def list(self):
        return Permission.query.all()
    
    def _get(self,id):
        u = Permission.query.filter(Permission.id == id).first()
        if u is None:
            raise DataNotFoundException
        return u

    def get(self, id):
        return self._get(id)


    # def update(self, name, data):
    #     self.__validate_data(data)
    #     u = self._get(name)
    #     for k in data.keys():
    #         setattr(u, k, data[k])
    #     db_session.add(u)
    #     self._try_commint()
    #     return u

    # def delete(self, name):
    #     u = self._get(name)
    #     db_session.delete(u)
    #     self._try_commint()
