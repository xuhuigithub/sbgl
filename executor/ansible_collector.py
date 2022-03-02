from copy import Error
import sys
import time
sys.path.append("./")

from ansible.parsing.dataloader import DataLoader
from ansible.playbook.play import Play
from ansible.executor.task_queue_manager import TaskQueueManager
from ansible.plugins.callback import CallbackBase
from ansible.plugins.callback.default import CallbackModule
from ansible.inventory.manager import InventoryManager
from ansible.vars.manager import VariableManager
import tempfile
from models import Assets
import os
from flask import app

class CollectorException(Error):
    
    def __init__(self, status: int) -> None:
        self.status = status
    
    def __str__(self) -> str:
        return "收集错误 TQM返回 %s" %self.status


class Collector:

    def __init__(self, asset: Assets, logfile) -> None:
        self.asset = asset
        self.logfile = logfile
    
    def collect(self):
        import sys 
        # fs = open(self.logfile, "w")
        # sys.stdout = fs
        print("staw")
        loader = DataLoader()
        # results_callback = ResultPopulater()
        results_callback = CallbackModule()
        # results_callback.asset = self.asset
        play_source =  dict(
            name = "Ansible Play",
            hosts = self.asset.ip,
            gather_facts = 'yes',
            connection="smart",
            # gather_timeout=10,
            # ssh 连接超时时间
            timeout = 60,
            user="root",
            tasks = [
                dict(name="user_nums", action=dict(module='shell', args='cat /etc/passwd |wc -l'), register='shell_out'),
            ]
        )
        a = tempfile.mktemp()
        # 跳过inventory manager 的检查。默认不填写sources的话，只让部署本地localhost
        with open(a, 'w') as f:
            f.write("")
        i = InventoryManager(loader=loader, sources=a)
        i.add_group("all")
        i.add_host(self.asset.ip, group="all")
        os.remove(a)
        v = VariableManager(loader=loader, inventory=i, version_info="4.5.0")
        play = Play().load(play_source,variable_manager=v, loader=loader)

        tqm = None
        try:
            tqm = TaskQueueManager(
                    inventory=i,
                    variable_manager=v,
                    loader=loader,
                    passwords=dict(vault_pass='secret',conn_pass=''), # 默认使用ssh秘钥链接
                    stdout_callback=results_callback,  # Use our custom callback instead of the ``default`` callback plugin
                )
            result = tqm.run(play)
            if result != tqm.RUN_OK:
                raise CollectorException(status=result)
        finally:
            if tqm is not None:
                tqm.cleanup()

if __name__ == "__main__":

    a = Assets()
    a.ip = "192.168.99.73"
    f = tempfile.mktemp()
    c = Collector(asset=a, logfile=f)
    print(f)
    c.collect()

