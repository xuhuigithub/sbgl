import subprocess
from io import StringIO
import multiprocessing
import time
import traceback
from xml.etree.ElementTree import VERSION
from flask import request
from dao.play_role import SubPlayRoleDAO
from dao import DataNotFoundException
from . import open as _open
from api import wrapresp
import models
import datetime
from sqlalchemy.sql import func
import flask
import typing
import sys
from multiprocessing import Event, Process
from executor.ansible_collector import Collector
import tempfile
import os
from utils import raise_error_api


def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return ("%3.1f" % (num,), unit + suffix)
        num /= 1024.0
    return ("%.1f" % (num,), 'Yi' + suffix)

def try_int(num):
    try:
        return int(num)
    except TypeError:
        return 0

@_open.route('/api/openData', methods=['GET'])
@wrapresp
def open_data():
    storage_sum = models.Assets.query.with_entities(func.sum(models.Assets.disk).label("storage_sum")).first().storage_sum
    storage_sum, storage_sum_unit = sizeof_fmt(try_int(storage_sum))
    os_users_sum = try_int(models.Assets.query.with_entities(func.sum(models.Assets.user_nums).label("os_users_sum")).first().os_users_sum)
    mem_sum = try_int(models.Assets.query.with_entities(func.sum(models.Assets.mem).label("mem_sum")).first().mem_sum)
    mem_sum, mem_sum_unit = sizeof_fmt(try_int(mem_sum))
    dc_data = []
    
    for dc in models.DC.query.all():
        dc_data.append(dict(name=dc.name, value=len(dc.cabinets)))
    
    asset_family_bullets = []
    for asset_family_bullet in models.Assets.query.with_entities(models.Assets.family, func.count(models.Assets.sn).label("count_n")).group_by(models.Assets.family).all():
        asset_family_bullets.append(dict(
            title=asset_family_bullet.family,
            measures=[asset_family_bullet.count_n],
        ))

    disk_avg_bullets = []
    disk_taget_n = models.Assets.query.with_entities(func.avg(models.Assets.disk).label("target_n")).first().target_n
    for disk_avg_bullet in models.Assets.query.with_entities(models.Assets.sn,models.Assets.disk).order_by(models.Assets.disk.asc()).limit(5).all():
        disk_avg_bullets.append(dict(
            title=disk_avg_bullet.sn,
            measures=[try_int(disk_avg_bullet.disk)],
            targets=[try_int(disk_taget_n)]
        ))

    mem_avg_bullets = []
    mem_taget_n = models.Assets.query.with_entities(func.avg(models.Assets.mem).label("target_n")).first().target_n
    for mem_avg_bullet in models.Assets.query.with_entities(models.Assets.sn,models.Assets.mem).order_by(models.Assets.mem.asc()).limit(5).all():
        mem_avg_bullets.append(dict(
            title=mem_avg_bullet.sn,
            measures=[try_int(mem_avg_bullet.mem)],
            targets=[try_int(mem_taget_n)]
        ))

    return dict(
        server_count = str(models.Assets.query.with_entities(models.Assets.sn).count()),
        storage_sum = str(storage_sum),
        storage_sum_unit = str(storage_sum_unit),
        os_users_sum = str(os_users_sum),
        mem_sum = str(mem_sum),
        mem_sum_unit = str(mem_sum_unit),
        dc_data_cabinets = dc_data,
        asset_family_bullets = asset_family_bullets,
        disk_avg_bullets = disk_avg_bullets,
        mem_avg_bullets = mem_avg_bullets
    )

from ansi2html import Ansi2HTMLConverter
conv = Ansi2HTMLConverter(inline=True, scheme="xterm")


def make_streaming(stream_filename, core_function, exit_function):
    result_q = multiprocessing.Queue()
    e = Event()
    fd1: typing.IO = open(stream_filename, "r")
    fd1.seek(0)
    fd2: typing.IO = open(stream_filename, "w")
    def stream():
#         yield "<html>"
#         yield """
#         <style>
#     span {
#         display: block;
#     }
# </style>
#         """
        s_id = 1
        while e.is_set() != True:
            msg = fd1.readline()
            if msg != "":
                if msg.strip() == "End of file":
                    e.set()
                    continue
                l = "data: " +  conv.convert(msg.strip(), full=False) + "\n\n" 
                s_id += 1
                yield "event: ping\n"
                yield l 
        # yield "</html>"
        fd1.close()
        fd2.close()
        exit_function(result_q)
        yield "event: ping\n"
        yield "data: EOF\n\n"
    
    def wrap_core_function():
        # 这将在新进程里运行
        sys.stdout = fd2
        sys.stderr = fd2
        try:
            result = core_function()
            result_q.put(result)
        except Exception as ex:
            traceback.print_exc()
            # 为了进程退出代码为1
            raise ex
        finally:
            print("End of file",file=fd2)
        
    return stream, wrap_core_function, result_q

def inject_globals(play_args) -> typing.Dict[str, str]:
        from models import SubPlayRole
        _vars = dict()
        for z in play_args:
            _vars.setdefault(z["name"],z["value"])
        
        host_vars = dict()
        sub_vars = dict()
        # 全局变量
        dao = SubPlayRoleDAO()
        for i in dao.list():
            i: SubPlayRole
            host_vars.setdefault("{name}_HOSTS".format(name=i.name.upper().replace('-', '_')), "{hosts}".format(hosts=",".join(i.hosts)))
            for x in i.play_args:
                sub_vars.setdefault(f"{i.name.upper().replace('-', '_')}_VARS_{x['name'].upper()}", x["value"])
        _all = {**_vars, **host_vars, **sub_vars}

        return _all 

@_open.route('/api/execPlayRole', methods=['GET'])
@raise_error_api(captures=(KeyError), err_msg="传参错误请检查")
@raise_error_api(captures=(DataNotFoundException,), err_msg="权限或者角色没有找到")
def test_open_data():
    
    sub_play_name = request.args['name']
    dao = SubPlayRoleDAO()
    sub_play = dao.get(name=sub_play_name)
    f = tempfile.mkstemp()
    _vars = inject_globals(sub_play.play_args)
    # print(_vars)
    c = Collector(logfile=f[1], vars=_vars, hosts=sub_play.hosts, group_name=sub_play.main_name, role_path=sub_play.main.path)
    # print(f[1])
    p = Process()
    def exit_function(result_q):
        all_vars =dict(
            name="__all__",
            value=_vars,
            type="String"
        )
        now = datetime.datetime.now()
        p.join()
        result = result_q.get()
        with open(f[1], 'r') as fs:
            last_log = fs.read()
        # dao.update(sub_play_name, data={
        #     "last_execution": now,
        #     "last_exit_code": result,
        #     "last_log": last_log
        # })
        sub_play = dao.get(name=sub_play_name)
        sub_play.last_execution = now
        sub_play.last_exit_code = result
        sub_play.last_log = last_log
        from models import RoleExection
        r = RoleExection()
        r.name = sub_play.name
        r.main_name = sub_play.main_name
        r.exit_code = result
        r.exec_log = last_log
        r.exec_time = now
        k = sub_play.play_args
        k.extend(all_vars)
        r.play_vars = k
        r.hosts = sub_play.hosts

        from database import db_session
        try:
            db_session.add(r)
            db_session.add(sub_play)
            db_session.commit()
        except Exception:
            traceback.print_exc()
            db_session.rollback()

        os.remove(f[1])
    stream, collect,result_q = make_streaming(f[1], c.collect, exit_function)

    p._target = collect
    p.start()

    return flask.Response(stream(), mimetype='text/event-stream')

from queue import Queue
q= Queue()

@_open.route('/api/getLowerPort', methods=['GET'])
@wrapresp
def test_getPlayRoles():
    import shlex,re
    port = 0
    k = re.compile(r':(\d+)\/')

    command_line = "/home/xuhui/gotty  --once -term hterm -w -port 0  /usr/bin/python3 /home/xuhui/.local/bin/asciinema rec -y --overwrite -c  'ssh root@192.168.206.182' /tmp/test.cast"
    # shell False 可以异步读取stderr
    process  = subprocess.Popen(shlex.split(command_line), stderr=subprocess.PIPE,shell=False, close_fds=False)

    q.put(process)
    print(shlex.split(command_line))
    while True:
        output = process.stderr.readline()
        if output.decode("utf8").__contains__("HTTP server is listening"):
            port = k.findall(output.decode("utf8").strip())[0]
            break


    return {"port": int(port) , "pid": process.pid}


@_open.route('/api/q', methods=['GET'])
@wrapresp
def test_qq():
    p = q.get(timeout=10)
    p.communicate()
    return 'ok'

@_open.route('/api/version', methods=['GET'])
@wrapresp
def open_version():
    from version import VERSION
    return VERSION