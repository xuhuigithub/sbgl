from datetime import datetime
import os
from subprocess import Popen
import traceback
import typing
import psutil
from dao.terminal import TerminalDAO
from models import Terminal
from queue import Queue

DAO = TerminalDAO()


class Singleton(object):
    _instance = None
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(Singleton, cls).__new__(
                                cls, *args, **kwargs)
        return cls._instance


class TerminalManager(Singleton):

    q = Queue()
    
    def __init__(self, secs_wait_for_defunct: int = 10) -> None:
        self.secs_wait_for_defunct = secs_wait_for_defunct
        


    def add_terminal_process(self, uuid ,process: Popen):
         DAO.create(
             dict(
                 id =uuid,
                 pid=process.pid,
                 p_pid=os.getpid(),
                 exec_time=datetime.now(),
                 command=" ".join(process.args),
                 is_running=True,
                 video_url=f"/tmp/{uuid}.cast"
             )
         )
         self.q.put_nowait(process)

    def list_processes(self) -> typing.List[Terminal]:
        return DAO.get_by_ppid(os.getpid())

    def kill_terminal_process(self, pid: int):
        ps =self.list_processes()
        pids = [ k.pid for k in ps ]
        if pid not in pids:
            return
        for i in ps:
            i: Terminal
            if i.pid == pid and i.p_pid == os.getpid():
                if self.__is_exists(i.pid):
                   psutil.Process(i.pid).kill()

    def __is_defunct(self, pid: int):
        p = psutil.Process(pid)
        return p.status() == psutil.STATUS_ZOMBIE
    
    def __is_exists(self, pid: int):
        try:
            p = psutil.Process(pid)
        except psutil.NoSuchProcess:
            return False
        return p.is_running()

    def clear_hang_prcess(self):
        for t in self.list_processes():
            pid = t.pid
            if self.__is_exists(pid) and self.__is_defunct(pid):
                try:
                    ps  = []
                    while not  self.q.empty():
                        p: Popen = self.q.get()
                        ps.append(p)
                    for p in ps:
                        if p.pid == pid:
                                p.communicate(timeout=self.secs_wait_for_defunct)
                        else:
                            self.q.put_nowait(p)
                except Exception as e:
                    traceback.print_exc()
                    raise e
                else:
                    DAO.update(uuid=t.id,data=dict(
                        is_running=False,
                    ))

    def clear_dead_process(self):
        for p in self.list_processes():
            if not self.__is_exists(p.pid):
                ps  = []
                while not  self.q.empty():
                    p1: Popen = self.q.get()
                    ps.append(p1)
                for p1 in ps:
                    if p.pid == p1.pid:
                        DAO.update(uuid=p.id, data=dict(
                            is_running=False,
                        ))
                    else:
                        self.q.put_nowait(p1)
                
    def run_clean(self):
        self.clear_dead_process()
        self.clear_hang_prcess()
