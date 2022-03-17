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
from queue import Queue

class CollectorException(Error):
    
    def __init__(self, status: int) -> None:
        self.status = status
    
    def __str__(self) -> str:
        return "收集错误 TQM返回 %s" %self.status

def populate(result, asset: Assets):
        if result.task_name == 'Gathering Facts':
            with open("/tmp/last-sbgl","w") as fi:
                fi.write(str(result._result['ansible_facts']))
            asset.mem = result._result['ansible_facts']['ansible_memtotal_mb'] * 1024 * 1024
            asset.system = f"{result._result['ansible_facts']['ansible_distribution']} {result._result['ansible_facts']['ansible_distribution_version']}"
            asset.mac = f"{result._result['ansible_facts']['ansible_default_ipv4']['macaddress']}"
            sockets_count = result._result['ansible_facts']['ansible_processor_count']
            # CPU型号 * CPU核心数 * CPU每个核心的线程数（超线程）* CPU 接口数
            asset.cpu = f"{result._result['ansible_facts']['ansible_processor'][1]} {result._result['ansible_facts']['ansible_processor'][2]} * {result._result['ansible_facts']['ansible_processor_cores']} * {result._result['ansible_facts']['ansible_processor_threads_per_core']} * {sockets_count}" 
            data = result._result['ansible_facts']
            asset.set_network_devices(data)
            asset.disk = sum([int(data["ansible_devices"][i]["sectors"]) * \
                        int(data["ansible_devices"][i]["sectorsize"]) \
                        for i in data["ansible_devices"] if i[0:2] in ("vd", "ss", "sd")])

            asset.model = data['ansible_product_name']
            asset.real_sn = data['ansible_product_serial']
        if result.task_name == 'user_nums':
            asset.user_nums = int(result._result['stdout'])

class ResultPopulater(CallbackBase):
    """A sample callback plugin used for performing an action as results come in

    If you want to collect all results into a single object for processing at
    the end of the execution, look into utilizing the ``json`` callback plugin
    or writing your own custom callback plugin
    """
    def __init__(self, display=None, options=None):
        super().__init__(display=display, options=options)
        self.asset: Assets = None
        self.r_q = None

    def v2_runner_on_ok(self, result, **kwargs):
        """Print a json representation of the result

        This method could store the result in an instance attribute for retrieval later
        """
        self.r_q.put(result)

class Collector:

    def __init__(self, asset: Assets) -> None:
        self.asset = asset

    
    def collect(self):
        r_q = Queue()
        loader = DataLoader()
        # results_callback = ResultPopulater()
        results_callback = ResultPopulater()
        results_callback.asset = self.asset
        results_callback.r_q = r_q
        t = [
                dict(name="user_nums", action=dict(module='shell', args='cat /etc/passwd |wc -l'), register='shell_out'),
            ]
        play_source =  dict(
            name = "Ansible Play",
            hosts = self.asset.ip,
            gather_facts = 'yes',
            connection="smart",
            # gather_timeout=10,
            # ssh 连接超时时间
            timeout = 60,
            user="root",
            tasks = t
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
            for i in range(len(t)+1):
                r = r_q.get_nowait()
                populate(r, self.asset)
        finally:
            if tqm is not None:
                tqm.cleanup()

if __name__ == "__main__":

    def test():
        while True:
            time.sleep(5)
            print(1)

    a = Assets()
    a.ip = "192.168.99.73"
    c = Collector(asset=a)
    # c.collect()
    # print(a)
    from multiprocessing import Process
    a = Process(target=c.collect)
    b = Process(target=test)
    b.daemon = True
    b.start()
    a.start()
    a.join()
    b.join()
