import os
import sys
import asyncio
import glob
import json
from utils.crossbar import RpcBase, rpc_procedure
from utils.logging import print
from utils.process_manager import ProcessManager
from pydantic import validate_arguments
from functools import reduce
import socket
import time
CONST_TICKET_TIME = 0.2  # 时钟刻度/秒
def get_host_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    finally:
        s.close()
    return ip
def TopologicalSort(G):
    '''
    生成有向无环图(DAG)并进行拓扑排序
    参数
    graph = {
        "A": ["B","C"],
        "B": ["D","E"],
        "C": ["D","E"],
        "D": ["F"],
        "E": ["F"],
        "F": [],
    }
    '''
    # 创建入度字典
    in_degrees = dict((u, 0) for u in G)
    # 获取每个节点的入度
    for u in G:
        for v in G[u]:
            in_degrees[v] += 1
    # 使用列表作为队列并将入度为0的添加到队列中
    Q = [u for u in G if in_degrees[u] == 0]
    res = []
    # 当队列中有元素时执行
    while Q:
        # 从队列首部取出元素
        u = Q.pop(0)
        # 将取出的元素存入结果中
        res.append(u)
        # 移除与取出元素相关的指向，即将所有与取出元素相关的元素的入度减少1
        for v in G[u]:
            in_degrees[v] -= 1
            # 若被移除指向的元素入度为0，则添加到队列中
            if in_degrees[v] == 0:
                Q.append(v)
    return res
class ServiceControl(RpcBase):
    '''
    需要单实例运行的服务控制类
    '''
    def __init__(self, **kwargs):
        if 'serv_dir' not in kwargs:
            raise RuntimeError('serv_dir参数必须设置')
        self.serv_dir = kwargs['serv_dir']  # Service的主目录
        self.serv_dir += '' if self.serv_dir.endswith('\\') else '\\'
        self.p_manager = ProcessManager(enabled_reader=True)  # 初始化进程管理器
        # 监控p_manager消息队列的输出
        self.p_manager.SingletonWatchPrint = self.on_queue_out
        # 监控托管进程的各服务状态变更
        self.p_manager.SingletonWatchStatus = self.on_service_status
        # 初始化本地的服务配置
        self._servCfg = {}
        self._initServiceConfig()
    async def on_queue_out(self, name, msg):
        # print(msg)
        if len(msg.strip()) > 0:
            self.context.publish('core.sevice.print', {'name': name, 'msg': msg})
    async def on_service_status(self, name):
        await self.getServiceStatus()
    def _initServiceConfig(self):
        '''
        初始化本地的服务配置
        '''
        print('initServiceConfig@%s' % self.serv_dir)
        if not os.path.exists(self.serv_dir):
            raise RuntimeError('initServiceConfig@%s Error,Directory not exists' % self.serv_dir)
        for file in glob.glob(self.serv_dir + '\*\\service.json'):
            if not os.path.isfile(file):
                continue
            cfg = None
            with open(file, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            cfg["cwd"]=os.path.abspath(os.path.join(self.serv_dir, './s/', os.path.dirname(file)))
            if 'name' in cfg and 'components' in cfg:
                group_name = cfg['name']
                for service in cfg['components']:
                    full_name = group_name + '.' + service['name']
                    service['full_name'] = full_name  # 增加完整名称，用于线程识别
                    service['group'] = group_name  # 增加分组名称，用于识别所属的组/主服务
                    service['autorun'] = True if 'autoruns' in cfg and service['name'] in cfg['autoruns'] else False  # 增加自动启动设置
                    # 转化工作路径为实际路径,永远从组的根目录开始
                    cwd = os.path.abspath(os.path.join(self.serv_dir, './s/', os.path.dirname(file), service['cwd']))
                    if not os.path.exists(cwd):
                        cwd = os.path.abspath(os.path.join(self.serv_dir, './s/', os.path.dirname(file)))
                    service['cwd'] = cwd + "\\"
                    if 'core_java'in service and service['core_java']:
                        jdk_path = os.path.abspath(os.path.join(self.serv_dir, '../c/jdk'))
                        if 'envs' in service:
                            service['envs']['JAVA_HOME'] = jdk_path
                        else:
                            service['envs'] = {'JAVA_HOME': jdk_path}
                    if 'core_erl'in service and service['core_erl']:
                        erl_path = os.path.abspath(os.path.join(self.serv_dir, '../c/erl'))
                        if 'envs' in service:
                            service['envs']['ERLANG_HOME'] = erl_path
                        else:
                            service['envs'] = {'ERLANG_HOME': erl_path}
                    self.p_manager.register_service(service)
                self._servCfg[group_name] = cfg
    @ property
    def _prefix(self):
        '''
        rpc方法前缀，完整名称为
        _prefix.classname.functionname
        '''
        return 'sys'
    
    def getGroupServices(self,name,only_auto:bool=False):
        result = []
        if name in self._servCfg and 'components' in self._servCfg[name]:
            group=self._servCfg[name]
            services = self._servCfg[name]['components'] if not only_auto else [x for x in self._servCfg[name]['components'] if group['autoruns'] !=None and x['name'] in group['autoruns']]
            dag={}#有向环图
            for s in services:
                if 'requires' in s and s['requires']!=None and len(s['requires'])>0:               
                    dag[s['name']]=[x for x in s['requires'] if x in [y['name'] for y in group['components']]]
                    for r in s['requires']:
                        comps=[y for y in group['components'] if y['name']==r]
                        if(len(comps)>1):raise RuntimeError('group的components中有多条名称相同的组件！')
                        if not r in dag and len(comps)>0:
                            comp=comps[0]
                            dag[r]=comp['requires'] if 'requires' in comp and comp["requires"] !=None and len(comp["requires"])>0 else []
                else:
                    dag[s['name']]=[]
            try:
                result=TopologicalSort(dag)#生成有向环图并拓扑排序
            except Exception as e:
                print('TopologicalSort(dag)出错，错误为%s'%e)
            result.reverse()#倒序才是正确的依赖关系
            #去重，这里使用了reduce累积迭代器，第一个传入的元素是[]，迭代时进行比较，将不重复的数据放入第一个元素
            func = lambda x,y:x if y in x else x + [y]
            result=reduce(func, [[], ] + result)#保留顺序，去重

            result=['%s.%s'%(name,x) for x in result]#返回采用full_name
        return result

    @ rpc_procedure
    @ validate_arguments
    async def getGroupsConfig(self):
        '''
        获取本地安装的服务包的完整配置
        '''
        result = []
        for key in self._servCfg:
            result.append(self._servCfg[key])
        return result
    @ rpc_procedure
    @ validate_arguments
    async def getServiceStatus(self):
        service_status = self.p_manager.services_dict()
        result = []
        for key in self.p_manager.configs:
            cfg = self.p_manager.configs[key]
            cfg['status'] = service_status[key]['status'] if key in service_status else '-noset-'
            last_at = service_status[key]['last_at'] if key in service_status else None
            cfg['last_at'] = last_at.strftime('%Y-%m-%d %H:%M:%S') if last_at != None else None
            result.append(cfg)
        self.context.publish('core.sevice.status', result)
        return result
    @ rpc_procedure
    @ validate_arguments
    async def start(self, name: str):
        if name in self.p_manager.services_dict():
            if 'kwargs' in self._servCfg[self.p_manager.configs[name]['group']]:
                self.p_manager.start(name,**self._servCfg[self.p_manager.configs[name]['group']]['kwargs'])
            else :self.p_manager.start(name)
            await self.getServiceStatus()
            return True
        else:
            raise RuntimeError('start error: name [%s] not registered!' % name)
    @ rpc_procedure
    @ validate_arguments
    async def stop(self, name: str):
        if name in self.p_manager.services_dict():
            self.p_manager.stop(name)
            await self.getServiceStatus()
            return True
        else:
            raise RuntimeError('stop error: name [%s] not registered!' % name)
    @ rpc_procedure
    @ validate_arguments
    async def restart(self, name):
        return self.p_manager.restart(name)
    
    
    @ rpc_procedure
    @ validate_arguments
    async def group_start(self, name:str,only_auto:bool=False):
        result=[]#返回成功启动的服务
        if name in self._servCfg and 'components' in self._servCfg[name]:
            curr_status=self.p_manager.services_dict()
            start_servs=self.getGroupServices(name,only_auto=only_auto)
            start_servs=[x for x in start_servs if x not in curr_status or curr_status[x]['status']=='stop' or curr_status[x]['status']==None]#已启动的服务无需启动
            print('group  %s start now ready start %s'%(name,start_servs))
            for s_name in start_servs:
                error=False
                if 'kwargs' in self._servCfg[self.p_manager.configs[s_name]['group']]:
                    self.p_manager.start(s_name,**self._servCfg[self.p_manager.configs[s_name]['group']]['kwargs'])
                else :self.p_manager.start(s_name)
                while True:
                    curr_state=self.p_manager.services_dict()[s_name]['status']
                    if curr_state =='running' or curr_state =='stop':
                        error=curr_state =='stop'
                        break
                    await asyncio.sleep(CONST_TICKET_TIME)
                if error:
                    #当前服务启动错误
                    print('group %s service %s start error!'%(name,s_name))
                    break
                else:
                    print('group %s service %s start success!'%(name,s_name))
                    result.append(s_name)
            return result
        else:
            raise RuntimeError('group  start error: name [%s] not registered' % name)
    @ rpc_procedure
    @ validate_arguments
    async def group_stop(self, name):
        result=[]#返回成功停止的服务
        if name in self._servCfg and 'components' in self._servCfg[name]:
            curr_status=self.p_manager.services_dict()
            stop_servs=self.getGroupServices(name)
            stop_servs=[x for x in stop_servs if x in curr_status and(curr_status[x]['status']=='starting' or curr_status[x]['status']=='running')]#已停止的服务无需停止
            stop_servs.reverse()
            print('group  %s stop now ready stop %s'%(name,stop_servs))
            for s_name in stop_servs:
                cfg=self.p_manager.configs[s_name]
                check_points_watchs=[]#停止时需要监听的其他服务
                if 'stop_wait_check_points' in cfg and cfg['stop_wait_check_points']!=None and len(cfg['stop_wait_check_points'])>0:
                    c_points=cfg['stop_wait_check_points']
                    for c_name in c_points:
                        watched=self.p_manager.threads['%s.%s'%(name,c_name)].event_watched()
                        watched.clear()  # 先禁用，避免启动时候命中了监视器的影响
                        check_points_watchs.append(watched)
                self.p_manager.stop(s_name)
                wait_before=int(time.time())#开始计时，当前的累记秒数
                while int(time.time())<wait_before+CONST_TICKET_TIME*200 and True:#最多等待200个时钟周期
                    curr_state=self.p_manager.services_dict()[s_name]['status']
                    if curr_state =='stop' or curr_state ==None:
                        w_count=0
                        for watched in check_points_watchs:
                            if watched.isSet():
                                w_count+=1
                        if w_count==len(check_points_watchs):
                            break
                        else:
                            print('group %s service %s stop wait check point!'%(name,s_name))
                            await asyncio.sleep(CONST_TICKET_TIME)
                            continue #跳过下面的休眠
                    else:await asyncio.sleep(CONST_TICKET_TIME)
                print('group %s service %s stop success!'%(name,s_name))
                result.append(s_name)
            return result
        else:
            raise RuntimeError('group  stop error: name [%s] not registered' % name)

    @ rpc_procedure
    @ validate_arguments
    async def autorun_start(self):
        result = []
        dag={}#依赖关系的 dag表示，如{"A": ["B","C"]}
        for name in self._servCfg:
            cfg=self._servCfg[name]
            if 'requires' in cfg and cfg['requires']!=None and len(cfg['requires'])>0:
                dag[name]=[x for x in  cfg['requires'] if x in self._servCfg]
            else:
                dag[name]=[]
        start_groups=TopologicalSort(dag)#生成有向环图并拓扑排序
        start_groups.reverse()#倒序才是正确的依赖关系
        print('autorun start service：%s'%(start_groups))
        for name in start_groups:
            #按包启动
            resp=await self.group_start(name,only_auto=True)
            result.extend(resp)
        return result
    
    @ rpc_procedure
    @ validate_arguments
    async def running_stop(self):
        result = []
        dag={}#依赖关系的 dag表示，如{"A": ["B","C"]}
        for name in self._servCfg:
            cfg=self._servCfg[name]
            if 'requires' in cfg and cfg['requires']!=None and len(cfg['requires'])>0:
                dag[name]=[x for x in  cfg['requires'] if x in self._servCfg]
            else:
                dag[name]=[]
        groups=TopologicalSort(dag)#生成有向环图并拓扑排序
        groups.reverse()#倒序才是正确的依赖关系
        print('autorun stop service：%s'%(groups))
        for name in groups:
            #按包启动
            resp=await self.group_stop(name)
            result.extend(resp)
        return result
