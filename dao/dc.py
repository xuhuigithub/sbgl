from models import DC
from . import  BaseDao

class DCDAO(BaseDao):
    def __init__(self):
        pass

    def list(self):
        return DC.query.all()
    
