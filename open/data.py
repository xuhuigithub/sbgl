import imp

import werkzeug
from . import open as _open
from api import wrapresp
import models
from sqlalchemy.sql import func
import flask
import typing
import sys
from multiprocessing import Event, Process
from executor.ansible_collector import Collector
import tempfile
import os


def sizeof_fmt(num, suffix='B'):
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return ("%3.1f" % (num,), unit + suffix)
        num /= 1024.0
    return ("%.1f" % (num,), 'Yi' + suffix)

@_open.route('/api/openData', methods=['GET'])
@wrapresp
def open_data():
    storage_sum = models.Assets.query.with_entities(func.sum(models.Assets.disk).label("storage_sum")).first().storage_sum
    storage_sum, storage_sum_unit = sizeof_fmt(int(storage_sum))
    os_users_sum = int(models.Assets.query.with_entities(func.sum(models.Assets.user_nums).label("os_users_sum")).first().os_users_sum)
    mem_sum = int(models.Assets.query.with_entities(func.sum(models.Assets.mem).label("mem_sum")).first().mem_sum)
    mem_sum, mem_sum_unit = sizeof_fmt(int(mem_sum))
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
            measures=[int(disk_avg_bullet.disk)],
            targets=[int(disk_taget_n)]
        ))

    mem_avg_bullets = []
    mem_taget_n = models.Assets.query.with_entities(func.avg(models.Assets.mem).label("target_n")).first().target_n
    for mem_avg_bullet in models.Assets.query.with_entities(models.Assets.sn,models.Assets.mem).order_by(models.Assets.mem.asc()).limit(5).all():
        mem_avg_bullets.append(dict(
            title=mem_avg_bullet.sn,
            measures=[int(mem_avg_bullet.mem)],
            targets=[int(mem_taget_n)]
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
                l = "data: " +  conv.convert(msg.strip(), full=False) + "\n\n" 
                s_id += 1
                yield "event: ping\n"
                yield l 
        # yield "</html>"
        fd1.close()
        fd2.close()
        exit_function()
        yield "event: ping\n"
        yield "data: EOF\n\n"
    
    def wrap_core_function():
        sys.stdout = fd2
        sys.stderr = fd2
        core_function()
        e.set()
        
    return stream, wrap_core_function

@_open.route('/api/test', methods=['GET'])
def test_open_data():
    
    a = models.Assets()
    a.ip = "192.168.99.73"
    f = tempfile.mkstemp()
    c = Collector(asset=a, logfile=f[1])
    print(f[1])
    p = Process()
    def exit_function():
        p.join()
        os.remove(f[1])
    stream, collect = make_streaming(f[1], c.collect, exit_function)
    p._target = collect
    p.start()

    return flask.Response(stream(), mimetype='text/event-stream')


@_open.route('/api/getPlayRoles', methods=['GET'])
@wrapresp
def test_getPlayRoles():
    
    return ["zookeeper"]