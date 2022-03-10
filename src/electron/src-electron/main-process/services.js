import msgBus from './messageBus'
import path from 'path'
import fs from 'fs'
import child_process from 'child_process'
import redis from 'redis'
import autobahn from 'autobahn'
import moment from 'moment'
import { shell } from 'electron'

/*
简体中文windows命令行，都使用的是GBK编码，nodejs以utf8识别是会出问题。
child_process.exec(cmd, { cwd: cwd, encoding: 'GBK' })
iconv.decode(data, 'GBK')
如果需要nodejs在控制台输出无乱码，则需chcp 65001 && quasar dev -m electron
*/
import iconv from 'iconv-lite'
// 常量
const CONST_APP_OUT_CHANNEL = 'app_output'
// 托管的服务实例
const instances = {}
// redis连接
let rds_client = null
let rds_ready = false
// crossbar连接
let cb_connection = null
let cb_session = null
let cb_ready = false
const start_command = (name, cmd, cwd, is_spawn, args) => {
  /*
  cwd采用相对路径，实际路径为发布后的public文件夹的路径的../../
  调试模式 定位到onekey_client主目录
  发布模式 定位到exe文件的上一级目录
  */
  function runCmd(cmd, cwd) {
    const worker = !is_spawn ? child_process.exec(cmd, { cwd: cwd, encoding: 'GBK' }) : child_process.spawn(cmd, args, { cwd: cwd, encoding: 'GBK' })
    worker._closed = false
    instances[name] = worker
    worker.stdout.on('data', function (data) {
      out_message(name + ' out: ' + iconv.decode(data, 'GBK'))
    })
    worker.stderr.on('data', function (data) {
      out_message(name + ' err: ' + iconv.decode(data, 'GBK'))
    })
    worker.on('close', function (code) {
      out_message(name + ' exit code：' + code)
      worker._closed = true
    })
  }
  console.log('start_command[' + name + ']: ' + cmd + ' in: ' + cwd)
  const cmdStr = cmd// 要执行的命令
  const cwdPath = path.join(msgBus.cfg.root_dir, ((cwd.startsWith('/')) ? cwd : '/' + cwd))// 启动路径
  console.log('准备执行', cmdStr, args, cwdPath)
  runCmd(cmdStr, cwdPath)
}
const rds_connect = (host, port, cb_connected) => {
  // redis连接
  rds_client = redis.createClient(port, host)
  rds_client.on('ready', function () {
    rds_ready = true
    out_message('onekey_client redis connect ready!')
    if (cb_connected) cb_connected(rds_client)
  })
  rds_client.on('end', function (e) {
    out_message('onekey_client redis  onend!')
    rds_ready = false
  })
  rds_client.on('error', function (err) {
    out_message('onekey_client redis connect error:' + err)
  })
  rds_client.on('connect', function () {
    out_message('onekey_client redis connect success!')
  })
}
const cb_connect = (url, ns, cb_connected) => {
  // crossbario 连接
  out_message('crossbar connect to url:[' + url + '] realm:[' + ns + ']')
  cb_connection = new autobahn.Connection({ url: url, realm: ns, initial_retry_delay: 0.1 })
  cb_connection.onopen = (session, details) => {
    cb_session = session
    cb_ready = true
    out_message('crossbar opened!url:[' + url + '] realm:[' + ns + ']')
    if (cb_connected) cb_connected(session)
  }
  cb_connection.onclose = function (reason, details) {
    cb_ready = false
    out_message('crossbar closed!')
  }
  cb_connection.open()
}
const out_message = (msg) => {
  // console.log('onkey_client:out_message length is ' + msg.length)
  msg = '[' + moment().format('MM-DD HH:mm:ss:SSS') + ']:' + msg
  const proc = (e) => console.log(e)
  if (cb_ready) {
    /* redis发布
    rds_client.pubsub('numsub', CONST_APP_OUT_CHANNEL, (err, arrs) => {
      console.log('numsub:', arrs, err)
      if (arrs[1] > 0) { rds_client.publish(CONST_APP_OUT_CHANNEL, msg) } else proc(msg)
    })
    */
    /* crossbar 发布*/
    try {
      cb_session.publish('core.sevice.out', [msg])
    } catch (err) {
      console.error('publish error:' + err)
    }
  } else {
    proc(msg)
  }
}
const services = {
  app_start: async () => {
    console.log('services.app_start')
    // erl.ini的额外处理
    const erlBase = path.resolve(path.join(msgBus.cfg.root_dir, 'c/erl/'))
    if (fs.existsSync(erlBase)) {
      var iniContent = `[erlang]\r\nBindir=${erlBase}\\erts-12.2.1\\bin\r\nProgname=erl\r\nRootdir=${erlBase}`
      iniContent = iniContent.replace(/\\/g, '\\\\')
      fs.writeFileSync(`${erlBase}\\bin\\erl.ini`, iniContent)
    }
    // 启动crossbar
    start_command('app__crossbar', 'c\\python\\python.exe', './', true, ['c\\python\\Scripts\\crossbar.exe', 'start', '--cbdir', 'f\\.crossbar'])

    if (msgBus.cfg.options && msgBus.cfg.options.redis) {
      // 启动redis
      start_command('app__redis', 'c\\redis\\redis-server.exe', './', true, ['f\\redis.conf'])
      // 测试进程
      // start_command('app_test', 'c\\python\\python.exe', '../', true, ['py\\loop.py'])
      // 启用 redis连接
      rds_connect('localhost', 16379, (conn) => {
        // 启动rest_api
        if (msgBus.cfg.options && msgBus.cfg.options.restapi) start_command('app__rest_api', '..\\c\\python\\python.exe', './py/', true, ['-m', 'uvicorn', '--port=9002', 'rest_api.main:app'])
      })
    }

    // 启用 crossbar连接
    return new Promise((resolve, reject) => {
      cb_connect('ws://localhost:8081/ws', 'realm1', (session) => {
        // 注册方法
        function setDevtools() {
          msgBus.app.emit('app_setDevtools')
        }
        session.register('sys.electron.devtools', setDevtools)
        function openPath(args) {
          shell.openPath(args[0])
        }
        session.register('sys.electron.openpath', openPath)
        // 启动crossbar_api
        start_command('app__crossbar_api', '..\\c\\python\\python.exe', './py/', true, ['crossbar_api\\main.py', path.join(msgBus.cfg.root_dir, './s')])
        // 等待crossbar_api启动完成
        const cb = () => {
          if (instances['app__crossbar_api']._closed === false) resolve(true) && console.log('app__crossbar_api started!')
          else setTimeout(cb, 100)
        }
        setTimeout(cb, 100)
      })
    })
  },
  app_stop: async () => {
    console.log('services.app_stop')

    rds_client&&rds_client.quit()
    cb_connection.close()
    const rev_arr = Object.keys(instances).reverse()
    rev_arr.forEach((key) => {
      console.log('stop service:' + key)
      instances[key].kill()
    })
    // 等待所有core进程退出
    return new Promise((resolve, reject) => {
      const cb = () => {
        let exit_num = 0
        for (const key in instances) {
          if (instances[key]._closed) exit_num++
        }
        if (exit_num === Object.getOwnPropertyNames(instances).length) {
          // 退出crossbar之后，需要清理配置文件目录下的node.pid 文件，crossbar被kill时不会清理该文件，启动后会根据该文件中的pid展开逻辑，可能该pid被其他进程占用，导致无权限操作
          const pid_file = path.resolve(path.join(msgBus.cfg.root_dir, 'f/.crossbar/node.pid'))
          if (fs.existsSync(pid_file)) {
            fs.unlinkSync(pid_file)
            console.log('delete pid file is ' + pid_file)
          }
          resolve(true)
        } else setTimeout(cb, 500)
      }
      setTimeout(cb, 500)
    })
  },
  service_stopall: async () => {
    console.log('services.service_stopall')

    if (cb_session) {
      try {
        await cb_session.call('sys.ServiceControl.running_stop')
      } catch (err) {
        console.error('sys.ServiceControl.running_stop error:', err)
      }
    }
    return new Promise((resolve, reject) => {
      const cb = () => {
        cb_session.call('sys.ServiceControl.getServiceStatus').then(async (resp) => {
          // console.log('sys.ServiceControl.getServiceStatus result:',resp)
          let running_count = 0
          resp.forEach(s => {
            if (s.status && s.status !== 'stop') running_count += 1
          })
          console.log('running service count is :', running_count)
          if (running_count <= 0) {
            resolve(true)
          } else setTimeout(cb, 200)
        }, async (err) => {
          console.error('sys.ServiceControl.getServiceStatus error:', err)
          reject(err)
        })
      }
      setTimeout(cb, 200)
    })
  }
}
export default services
