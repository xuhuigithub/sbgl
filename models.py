from uuid import uuid1
from sqlalchemy import Column, Integer, String, Text, DateTime,Index,BigInteger, null
from sqlalchemy.orm import relationship
from sqlalchemy.sql.schema import ForeignKey, Table
from database import Base
import hashlib
from enum import Enum


class Assets(Base):
    __tablename__ = 'assets'
    sn = Column(String(length=50), primary_key=True, comment="序列号")
    created_time = Column(DateTime(), comment="入库时间")
    model = Column(String(length=50), comment="设备型号")
    disk = Column(BigInteger(), comment="硬盘大小，字节")
    comment  = Column(String(800), comment="备注")
    user_name = Column(String(50),ForeignKey("user.name"), comment="用户名")
    port = Column(String(20), comment="ssh 端口号", default="22")
    mem = Column(BigInteger(), comment="内存大小，字节")
    cpu = Column(String(80), comment="备注")
    mac = Column(String(50), comment="网卡mac")
    system = Column(String(50), comment="系统版本")
    ip = Column(String(50), comment="IP地址")
    cabinet_id = Column(Integer(), ForeignKey("cabinet.id"), comment="机柜ID", nullable=False)
    cabinet = relationship("Cabinet", viewonly=True)
    postion = Column(String(50), comment="机柜位置")
    family = Column(String(50), comment="设备类型", nullable=False)
    user_nums = Column(Integer, comment="系统用户数量")
    last_seen = Column(DateTime(), comment="最后确认存活时间")

    def __repr__(self):
        return '<Asset %r>' % (self.sn)


class User(Base):
    __tablename__ = 'user'
    name = Column(String(50), primary_key=True, comment="用户名")
    realname = Column(String(50), comment="姓名")
    tel = Column(String(50), comment="电话")
    email = Column(String(50), comment="邮箱")
    desc = Column(String(800), comment="描述")
    role_name = Column(String(50), ForeignKey("role.name"), comment="角色名")
    password = Column(String(200), comment="密码")
    role = relationship("Role", backref="users")

    def set_password(self,password):
        self.password = str(hashlib.md5(password.encode('utf-8')).digest())

    def verify_password(self, password):
        return str(hashlib.md5(password.encode('utf-8')).digest()) == self.password
    
    def has_permission(self,permission):
        # 包含service_admin权限 或者 包含权限
        p_names = [ i.name for i in self.role.permissions ]
        return permission in p_names or Permission_Enum.service_admin.value in p_names

    def __repr__(self):
        return '<User %r:%r>' % (self.realname, self.name)


association_table = Table('role_permission', Base.metadata,
    Column('role_name', ForeignKey('role.name'), primary_key=True),
    Column('permission_id', ForeignKey('permission.id'), primary_key=True)
)


class Role(Base):
    __tablename__ = 'role'
    name = Column(String(50), primary_key=True, comment="角色名")
    permissions = relationship("Permission", secondary=association_table, back_populates="roles")


class Permission(Base):
     __tablename__ = 'permission'
     id = Column(Integer(), autoincrement=True, primary_key=True)
     name = Column(String(50), comment="权限名称")
     roles = relationship("Role", secondary=association_table, back_populates="permissions")


class DC(Base):
     __tablename__ = 'dc'
     name = Column(String(50) ,comment="数据中心名称", primary_key=True)
    #  cabinets = relationship("Cabinet", cascade="all, delete-orphan", back_populates="dc")


class Cabinet(Base):
     __tablename__ = 'cabinet'
     id = Column(Integer(), autoincrement=True, primary_key=True)
     name = Column(String(50) ,comment="机柜名称")
     dc_name = Column(String(50),ForeignKey("dc.name") ,comment="数据中心名称")
     dc = relationship("DC", backref="cabinets")
     assets = relationship("Assets", cascade="all, delete-orphan")
     Index('myindex', name, dc_name, unique=True)


class Permission_Enum(Enum):
    service_admin = "service_admin"
    asset_list = "asset_read"
    asset_create = "asset_create"
    asset_delete = "asset_delete"
    asset_update = "asset_update"
    user_list = "user_list"
    user_create = "user_create"
    user_delete = "user_delete"
    user_update = "user_update"
    cabinet_list = "cabinet_list"
    cabinet_delete = "cabinet_delete"
    cabinet_update = "cabinet_update"
    cabinet_create = "cabinet_create"

class Role_Enum(Enum):
    root = "root"
    operator = "operator"
    user = "user"

class AssetFamily_Enum(Enum):
    SER = "服务器"
    NETWORK = "网络设备"
    DESKTOP = "桌面设备"
    SEC = "安全设备"

class PlayRole(Base):
    __tablename__ = 'play_role'
    name = Column(String(50), primary_key=True, comment="角色名")
    path = Column(String(50), comment="角色路径")
    play_args = Column(Text(), comment="模型")
    sub_roles = relationship("SubPlayRole", back_populates="main", cascade="all, delete-orphan")

class SubPlayRole(Base):
    __tablename__ = 'sub_play_role'
    name = Column(String(50), primary_key=True, comment="角色名")
    main_name = Column(String(50),ForeignKey("play_role.name") ,comment="主角色名称")
    main = relationship("PlayRole", viewonly=True, back_populates="sub_roles")
    play_args = Column(Text(), comment="模型")
    hosts =  Column(Text(), comment="主机")
    last_update = Column(DateTime(), comment="最后更新时间")
    last_execution = Column(DateTime(), comment="最后执行时间")
    last_exit_code = Column(String(50), comment="最后一次退出状态", default=None)
    last_log = Column(Text(), comment="最后一次执行日志", default=None)