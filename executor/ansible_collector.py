from copy import Error
import sys
import time
import typing
sys.path.append("./")

from ansible.parsing.dataloader import DataLoader
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.plugins.callback import CallbackBase
from ansible.plugins.callback.default import CallbackModule
from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager
import tempfile
from models import Assets, SubPlayRole
import os
from flask import app

class CollectorException(Error):
    
    def __init__(self, status: int) -> None:
        self.status = status
    
    def __str__(self) -> str:
        return "收集错误 TQM返回 %s" %self.status


class Collector:
    

    def __init__(self, logfile: str, hosts: typing.List[str],role_path: str, vars: typing.List[typing.Dict[str, str]], group_name: str) -> None:
        self.logfile = logfile
        self.role_path = role_path
        self.vars = vars
        self.group_name = group_name
        self.hosts = hosts
    
    def collect(self):
        result = 1
        # fs = open(self.logfile, "w")
        # sys.stdout = fs
        print("staw")
        loader = DataLoader()
        loader.set_basedir(self.role_path)
        _vars = {}
        for z in self.vars:
            _vars.setdefault(z["name"],z["value"])
        play_source =  dict(
            name = "Ansible Play",
            hosts = self.group_name,
            gather_facts = 'yes',
            connection="smart",
            # gather_timeout=10,
            # ssh 连接超时时间
            timeout = 300,
            user="root",
            # roles_path = self.asset.main.path,
            roles = [
            {"role": self.group_name} 
            ],
            vars = _vars,
            tasks = [
                dict(name="user_nums", action=dict(module='shell', args='cat /etc/passwd |wc -l'), register='shell_out'),
            ]
        )
        a = tempfile.mktemp()
        # 跳过inventory manager 的检查。默认不填写sources的话，只让部署本地localhost
        with open(a, 'w') as f:
            f.write("")
        i = InventoryManager(loader=loader, sources=a)
        i.add_group(self.group_name)
        for g in self.hosts:
            i.add_host(g, group=self.group_name)
        os.remove(a)
        v = VariableManager(loader=loader, inventory=i, version_info="4.5.0")

        tqm = None
        try:
            play = Play().load(play_source,variable_manager=v, loader=loader)

            tqm = TaskQueueManager(
                    inventory=i,
                    variable_manager=v,
                    loader=loader,
                    passwords=dict(vault_pass='secret',conn_pass=''), # 默认使用ssh秘钥链接
                    # stdout_callback=results_callback,  # Use our custom callback instead of the ``default`` callback plugin
                )
            result = tqm.run(play)
        finally:
            if tqm is not None:
                tqm.cleanup()

        return result


if __name__ == "__main__":

    a = Assets()
    a.ip = "192.168.99.73"
    f = tempfile.mktemp()
    c = Collector(asset=a, logfile=f)
    print(f)
    c.collect()

