import { app, BrowserWindow, dialog, nativeTheme, shell, Notification } from 'electron'
// 全局的消息中心
import msgBus from './messageBus'
import './messageProc'
import ui_tray from './ui_tray'

try {
  if (process.platform === 'win32' && nativeTheme.shouldUseDarkColors === true) {
    require('fs').unlinkSync(require('path').join(app.getPath('userData'), 'DevTools Extensions'))
  }
} catch (_) { }

/**
 * Set `__statics` path to static files in production;
 * The reason we are setting it here is that the path needs to be evaluated at runtime
 */
if (process.env.PROD) {
  global.__statics = __dirname
}

let mainWindow
function createWindow() {
  /**
   * Initial window options
   */
  mainWindow = new BrowserWindow({
    width: 840,
    height: 680,
    useContentSize: true,
    frame: false, // 无边框
    webPreferences: {
      // Change from /quasar.conf.js > electron > nodeIntegration;
      // More info: https://quasar.dev/quasar-cli/developing-electron-apps/node-integration
      nodeIntegration: process.env.QUASAR_NODE_INTEGRATION,
      nodeIntegrationInWorker: process.env.QUASAR_NODE_INTEGRATION
      // More info: /quasar-cli/developing-electron-apps/electron-preload-script
      // preload: path.resolve(__dirname, 'electron-preload.js')
    }
  })

  mainWindow.loadURL(process.env.APP_URL)

  mainWindow.on('closed', () => {
    mainWindow = null
  })
  const proc_mini = (e) => {
    ui_tray.show(mainWindow)// 任务栏托盘，需传递主窗口句柄
    ui_tray.minimize()
  }
  // 主窗口关闭或最小化即为最小化到托盘
  mainWindow.on('close', (e) => {
    dialog.showMessageBox(mainWindow, {
      type: 'info',
      title: 'Information',
      defaultId: 0,
      cancelId: 2,
      message: '确定要关闭吗？',
      buttons: ['最小化到托盘', '直接退出', '取消']
    }).then(
      (resp) => {
        console.log('对话框关闭', resp.response)
        if (resp.response === 0) {
          proc_mini()
        } else if (resp.response === 1) {
          // 执行退出逻辑
          ui_tray.close()
          mainWindow.destroy()// 主窗口退出后由app事件处理关闭
        }
      }
    )
    e.preventDefault()// 取消退出
  })
  mainWindow.on('minimize', (e) => {
    proc_mini(e)
  })
  mainWindow.on('restore', (e) => {
    console.log('restore')
    ui_tray.close()
  })
  mainWindow.on('closed', (e) => {
    mainWindow = null
    console.log('closed')
  })
}
// 确保只运行一个实例
const gotTheLock = app.requestSingleInstanceLock()
if (!gotTheLock) {
  app.quit()// 已有实例运行，则当前实例退出
} else {
  app.on('second-instance', (event, commandLine, workingDirectory) => {
    // 当运行第二个实例时,将会聚焦到myWindow这个窗口
    if (mainWindow) {
      if (mainWindow.isMinimized()) mainWindow.restore()
      mainWindow.focus()
    }
  })
  app.on('ready', () => {
    const cb = () => {
      msgBus.app.emit('service_start')
    }
    msgBus.app.emit('app_start', cb)// 应用程序启动消息
    createWindow()// 主窗口
    // 注册针对主窗口的事件处理器
    msgBus.app.on('app_setDevtools', function(callback) {
      console.log('app:setDevtools', callback)
      if (!mainWindow.webContents.isDevToolsOpened()) mainWindow.webContents.openDevTools()
      else mainWindow.webContents.closeDevTools()
    })
  })

  app.on('window-all-closed', () => {
    // 所有窗口关闭后，退出客户端
    if (process.platform !== 'darwin') {
      let notification = null
      if (Notification.isSupported()) {
        notification = new Notification({ title: '请稍候', body: '正在退出运行中的服务', timeoutType: 'never' })
        notification.show()
      }
      const exitWindow = new BrowserWindow({
        width: 350,
        height: 250,
        useContentSize: true,
        frame: false, // 无边框
        webPreferences: {
          // Change from /quasar.conf.js > electron > nodeIntegration;
          // More info: https://quasar.dev/quasar-cli/developing-electron-apps/node-integration
          nodeIntegration: process.env.QUASAR_NODE_INTEGRATION,
          nodeIntegrationInWorker: process.env.QUASAR_NODE_INTEGRATION
          // More info: /quasar-cli/developing-electron-apps/electron-preload-script
          // preload: path.resolve(__dirname, 'electron-preload.js')
        }
      })
      exitWindow.loadURL(`${process.env.APP_URL}#/exit`).then(() => {
        const cb2 = () => {
          if (notification)notification.close()
          exitWindow.destroy()
          app.quit()
        }
        const cb1 = () => {
          msgBus.app.emit('app_stop', cb2)// 再退出app
        }
        msgBus.app.emit('service_stop', cb1)// 先停止服务
      })
    }
  })

  app.on('activate', () => {
    if (mainWindow === null) {
      createWindow()
    }
  })
  app.on('web-contents-created', (e, webContents) => {
    webContents.on('new-window', (event, url) => {
      event.preventDefault()
      shell.openExternal(url)
    })
  })
}

