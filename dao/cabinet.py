from models import Cabinet, DC
from database import db_session
from . import DataNotFoundException, BaseDao, IllegalStateException

class CabinetDAO(BaseDao):
    def __init__(self):
        pass

    def __validate_data(self, data):
        # raise ValueError if not a valid Role_Enum
        dc_name = data.get("dc_name")
        if dc_name:
            if DC.query.filter(DC.name == dc_name).first():
                return 
        raise IllegalStateException

    def list(self):
        query = Cabinet.query
        query = self.handle_filter(query)
        return query.all()
    
    def _get(self,id):
        u = Cabinet.query.filter(Cabinet.id == id).first()
        if u is None:
            raise DataNotFoundException
        return u

    def get(self, id):
        return self._get(id)

    def create(self, data: dict):
        # self.__validate_data(data)
        u = Cabinet()
        for k in data.keys():
            if k == "dc":
                a = DC()
                a.name = data[k]
                u.dc = a
                continue
            
            setattr(u, k, data[k])
        db_session.add(u)
        self._try_commint()
        return u

    def update(self, id, data):
        u = self._get(id)
        self.__validate_data(data)
        for k in data.keys():
            setattr(u, k, data[k])
        db_session.add(u)
        self._try_commint()
        return u

    def delete(self, id):
        u = self._get(id)
        db_session.delete(u)
        self._try_commint()

    def handle_name(self, query, value):
        return query.filter(Cabinet.name.like(f"%{value}%"))