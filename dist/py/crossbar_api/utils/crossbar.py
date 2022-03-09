import abc
import os
import sys
import inspect
import glob
import copy
import asyncio
from functools import wraps
from pydantic import ValidationError
from utils.logging import print
from autobahn.asyncio.wamp import ApplicationSession

def rpc_procedure(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except ValidationError as e:  # 捕获pydantic的参数验证的异常
            raise RuntimeError('%s' % e)
    decorated.in_rpc_procedure = True  # 该函数已被装饰过
    if not hasattr(f, 'func_globals') or not 'ValidatedFunction' in f.func_globals:
        print('function [%s] recommend use decorate (validate_arguments)' % (f.__name__))
    return decorated

def rpc_instances(dir_name='rpc_set', **instance_kwargs):
    module_dir = dir_name
    result = []
    dir = os.path.dirname(os.path.realpath(sys.argv[0]))  # 启动目录
    for pkg in glob.glob('%s/%s/*%s' % (dir, module_dir, '*.py')):
        base_name = os.path.basename(pkg).split('.')[0]  # 模块名
        pkg_name = module_dir + '.' + base_name  # 模块的路径
        module = __import__(pkg_name, fromlist=[base_name])  # 导入模块，fromlist只会导入list目录
        for name, class_ in inspect.getmembers(module, inspect.isclass):
            if issubclass(class_, RpcBase) and class_ != RpcBase:
                print('create instance by %s' % class_)
                instance = class_(**instance_kwargs)  # 实例化类
                result.append(instance)
    return result
class RpcBase():
    __metaclass__ = abc.ABCMeta
    # 抽象属性Get
    @abc.abstractproperty
    def _prefix(self):
        '''
        rpc方法前缀，完整名称为
        _prefix.classname.functionname
        '''
        return ''
    # 抽象属性Get
    @abc.abstractproperty
    def context(self):
        return self._context
    def _setContext(self, context):
        self._context = context
    def _call_proc(self, func, * args):
        func_args = inspect.getargspec(func).args  # 获取函数的参数
        call_args = {}  # 调用函数的参数字典
        offset = 1 if len(func_args) > 0 and 'self' in func_args and func_args[0].lower() == 'self' else 0
        for param_i in range(offset, len(func_args)):
            val_i = param_i - offset
            call_args[func_args[param_i]] = args[val_i] if (val_i) < len(args) else None
        try:
            return func(**call_args)  # 通过**展开字典调用
        except ValidationError as e:  # 捕获pydantic的参数验证的异常
            raise RuntimeError('%s' % e)
    async def _register(self, context):
        for name, func in inspect.getmembers(self, inspect.ismethod):
            if not name.startswith('_') and hasattr(func, 'in_rpc_procedure'):  # 已被rpc_procedure装饰器装饰过
                proc_name = '%s%s.%s' % (self._prefix + '.' if self._prefix and len(self._prefix) > 0 else '', self.__class__.__name__, name)
                #proc = lambda *args: self._call_proc(func, *args)
                # await context.register(proc, proc_name)
                await context.register(func, proc_name)
                print('procedure [%s] registered' % proc_name)

class MyApplicationSession(ApplicationSession):
    def __init__(self, modules=['rpc_sets'], config=None, **kwargs):
        # 加载的模块列表
        self.__arrs_modules = modules
        # 用于rpc类实例的初始化函数的扩展参数
        self.rpc_kwargs = kwargs
        # 基类构造函数
        ApplicationSession.__init__(self, config=config)
    async def onJoin(self, details):
        # 加载rpc_set下的所有 集成 RpcBase的子类，并将其合规方法注册为rpc方法
        for m in self.__arrs_modules:
            objs = rpc_instances(m, **self.rpc_kwargs)
            for obj in objs:
                obj._setContext(self)
                await obj._register(self)
    def onUserError(self, e, msg):
        print('MyApplicationSession has error:%s' % msg)
        raise e
    def onDisconnect(self):
        asyncio.get_event_loop().stop()  # 退出事件循环，主程序理应退出
        print('MyApplicationSession is closed,app exit!')
