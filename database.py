from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base


# engine = create_engine('sqlite:///./test_installOS.db', convert_unicode=True)
engine = create_engine('mysql+mysqlconnector://root:1Qaz#123@192.168.99.79/test?charset=utf8', encoding='utf-8',echo=False, pool_size=30, max_overflow=15, )
# pool_recycle=60 * 60
db_session = scoped_session(sessionmaker(autocommit=False,
                                         autoflush=False,
                                         bind=engine))
Base = declarative_base()
Base.query = db_session.query_property()


def init_db():
    # import all modules here that might define models so that
    # they will be registered properly on the metadata.  Otherwise
    # you will have to import them first before calling init_db()
    import models
    Base.metadata.create_all(bind=engine)
    num_rows_deleted3 = db_session.query(models.User).delete()
    num_rows_deleted3 = db_session.query(models.association_table).delete()

    num_rows_deleted2 = db_session.query(models.Role).delete()
    num_rows_deleted = db_session.query(models.Permission).delete()
    print(f"权限删除...{num_rows_deleted} {num_rows_deleted2}")

    root_p = None
    user_p = []
    operator_p = []
    # 同步权限
    for index,i in enumerate(models.Permission_Enum):
        p = models.Permission()
        p.id = index + 1
        p.name = models.Permission_Enum(i).value

        if i == models.Permission_Enum.service_admin:
            root_p = p
        if i in [models.Permission_Enum.asset_create, models.Permission_Enum.asset_update, models.Permission_Enum.cabinet_update, models.Permission_Enum.cabinet_create]:
            operator_p.append(p)
        if i in [models.Permission_Enum.asset_list,models.Permission_Enum.user_list,models.Permission_Enum.cabinet_list]:
            operator_p.append(p)
            user_p.append(p)

        db_session.add(p)

    # 创建root账户如果不存在
    root = models.User.query.filter(models.User.name == "root").first()
    role_root = models.Role.query.filter(models.Role.name == models.Role_Enum.root.value).first()
    if not role_root:
        r = models.Role()
        r.name = models.Role_Enum.root.value
        r.permissions = [root_p]
        role_root = r
        db_session.add(r)

    if root is None:
        u = models.User()
        u.name = "root"
        u.email = "1498472791@qq.com"
        u.realname = "徐晖"
        u.role = role_root
        u.desc = "管理员用户"
        u.tel = "17710399068"
        u.set_password("123456")
        db_session.add(u)

    # 固定权限
    # 操作员
    role_operator = models.Role.query.filter(models.Role.name == models.Role_Enum.operator.value).first()
    if not role_operator:
        role_operator = models.Role()
        role_operator.name = models.Role_Enum.operator.value
        role_operator.permissions = operator_p

    db_session.add(role_operator)

    # 普通用户
    role_user = models.Role.query.filter(models.Role.name == models.Role_Enum.user.value).first()
    if not role_user:
        role_user = models.Role()
        role_user.name = models.Role_Enum.user.value
        role_user.permissions = user_p
        
    db_session.add(role_user)
    
    # dc
    for dc_name in ["酒仙桥","中关村"]:
        dc = models.DC.query.filter(models.DC.name == dc_name).first()
        if dc is None:
            dc = models.DC()
            dc.name = dc_name
            db_session.add(dc)

    try:
        db_session.commit()
    except Exception as e:
        db_session.rollback()
        raise e