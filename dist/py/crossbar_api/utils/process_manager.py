
import sys
import os
import subprocess
import threading
import time
import datetime
import re
import datetime
from utils.logging import print
from queue import Queue, Empty
import asyncio


CONST_TICKET_TIME = 10  # 时钟刻度/秒
class managerThread(threading.Thread):
    def __init__(self, name, cmd, cwd, bind_cwd=False,
                 ready_pattern=None, watched_pattern=None, stop_cmd=None, envs=None, mq_out=None,**kwargs):
        threading.Thread.__init__(self)
        self.__running = threading.Event()  # 用于停止线程的标识
        self.__running.set()  # 将running设置为True

        self.__ready = threading.Event()  # 用于服务已就绪的通知
        self.__ready.clear()

        self.__watched = threading.Event()  # watch命令行事件
        self.__watched.clear()

        self.name = name
        self.cmd = cwd + cmd if bind_cwd else cmd
        self.cwd = cwd
        self.ready_pattern = ready_pattern
        self.watched_pattern = watched_pattern
        self.stop_cmd = cwd + stop_cmd if bind_cwd and stop_cmd != None else stop_cmd
        # 系统环境变量
        self.sys_envs = os.environ.copy()
        if envs != None and len(envs.keys()) > 0:
            self.sys_envs.update(envs)
        
        self.mq_out = mq_out
        self.__lines = []
        self.last_at = None

        self.kwargs=kwargs
        #额外的参数处理
        if 'fix_wmic' in self.kwargs:
            # windows 下 wmic额外处理，修复wmic无法找到的问题
            if 'PATH' in self.sys_envs:
                self.sys_envs['PATH']+=";%s;"%kwargs['fix_wmic']
    def print(self, msg, end='\r\n'):
        if self.mq_out != None:
            self.mq_out.put((self.name, msg.strip()))
        else:
            print(str(msg), end)
    def status_assert(self, state):
        self.print('__status__:%s进程状态更改为%s' % (self.name, state))
    def run(self):
        try:
            self.process = subprocess.Popen(
                self.cmd, cwd=self.cwd, encoding='gbk', creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                env=self.sys_envs,
                bufsize=10240, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, shell=True, close_fds=True
            )
            self.print('%s进程正在启动:%s @ %s' % (self.name, self.cmd, self.cwd))
            self.status_assert('starting')
        except Exception as e:
            self.print('启动进程失败:%s' % e)
            self.__running.clear()

        while self.__running.isSet():
            returncode = self.process.poll()
            if returncode is not None:
                self.print('%s进程已自动退出，returncode=%s' % (self.name, returncode))
                break
            try:
                line = self.process.stdout.readline()  # 阻塞方法
                self.__lines.append(line)
                self.last_at = datetime.datetime.now()
                self.print('%s:%s' % (self.name, line), end="")
                if not self.__ready.isSet() and (self.ready_pattern == None or re.match(self.ready_pattern, line) != None):
                    self.__ready.set()
                    self.print('%s:服务已就绪' % (self.name))
                    self.status_assert('running')
                if not self.__watched.isSet() and (self.watched_pattern != None and re.match(self.watched_pattern, line) != None):
                    self.__watched.set()
                    self.print('%s:服务已命中监视器' % (self.name))
            except KeyboardInterrupt:
                pass
            except Exception as e:
                self.print('%s:服务发生未知异常:%s' % (self.name, e))
                self.process.kill()

        self.status_assert('stop')
        self.__watched.clear()
        self.__ready.clear()
        self.__running.clear()
        self.print('%s:线程已退出' % (self.name))
    def stop(self):
        self.print('%s进程接受手工停止要求' % (self.name))
        if self.process != None and self.process.poll() == None:
            if self.stop_cmd == None:               
                if 'fix_stop' in self.kwargs and self.kwargs["fix_stop"].strip()=='taskkill':
                    # 通过cmd命令中止，强制关闭且关闭子进程
                    exit = subprocess.Popen(['taskkill', '/F', '/T', '/PID', str(self.process.pid)])
                else:
                    self.process.terminate()
                # exit.wait()
            else:
                # 通过退出命令退出
                exit = subprocess.Popen(self.stop_cmd, cwd=self.cwd, env=self.sys_envs)
                # exit.wait(CONST_TICKET_TIME)
            try:
                outs, errs = self.process.communicate(timeout=CONST_TICKET_TIME)  # 等待进程退出
            except subprocess.TimeoutExpired:
                outs, errs = self.process.communicate()
            self.print('退出指令返回:outs:%s,errs:%s' % (outs, errs))
            if not self.process.stdout.closed:
                self.print('%sstdout未关闭' % (self.name))
                self.process.stdout.close()
            self.print('%s进程已被手工停止,线程退出' % (self.name))
        self.__running.clear()  # 设置为False，线程脱离阻塞后关闭

    def event_ready(self):
        return self.__ready
    def event_watched(self):
        return self.__watched
    def event_running(self):
        return self.__running
    @property
    def status(self):
        return 'running' if self.event_ready().isSet() else 'starting' if self.event_running().isSet() else 'stop'

class ProcessManager:
    def __init__(self, enabled_reader=False):
        self.SingletonWatchPrint = None
        self.SingletonWatchStatus = None
        self.configs = {}
        self.threads = {}
        self.mq_out = Queue()
        if enabled_reader:
            self.task_mq_reader = asyncio.ensure_future(self.__mq_reader())  # 启动异步任务
    async def __mq_reader(self):
        while True:
            try:
                name, msg = self.mq_out.get_nowait()
                is_status = msg.startswith('__status__:')
                if is_status:
                    if self.SingletonWatchStatus != None:
                        await self.SingletonWatchStatus(name)
                    else:
                        print('%s:' % (name, msg))
                else:
                    if self.SingletonWatchPrint != None:
                        await self.SingletonWatchPrint(name, msg)
                    else:
                        print('%s:' % (name, msg))
            except Empty:
                await asyncio.sleep(0.1)
            await asyncio.sleep(0)  # 释放事件

    def start(self, name,**kwargs):
        if name in self.configs and self.services_dict()[name]['status'] in ['stop', None]:
            cfg = self.configs[name]
            print(cfg['start'])
            print(cfg['cwd'])
            t = managerThread(name=cfg['full_name'], cmd=cfg['start'], cwd=cfg['cwd'], bind_cwd=True,
                              ready_pattern=cfg['ready_pattern'],  # 通过控制台输出判断服务就绪的正则表达式
                              stop_cmd=cfg['stop'] if 'stop' in cfg else None,
                              watched_pattern=cfg['check_point_pattern'] if 'check_point_pattern' in cfg else None,
                              envs=cfg['envs'] if 'envs' in cfg else None,
                              mq_out=self.mq_out,
                              **kwargs
                              )
            self.threads[name] = t
            t.start()


    def stop(self, name):
        if name in self.configs and self.services_dict()[name]['status'] in ['running', 'starting']:
            self.threads[name].stop()
        pass
    def restart(self, name):
        pass
    def register_service(self, cfg):
        self.configs[cfg['full_name']] = cfg
    def unregister_service(self, name):
        self.configs.pop(name)
    def services_dict(self):
        result = {}
        for cfg in self.configs.values():
            name = cfg['full_name']
            result[name] = {
                'status': self.threads[name].status if name in self.threads else None,
                'last_at': self.threads[name].last_at if name in self.threads else None,
            }
        return result

    def exec(self, cfg):
        pass
