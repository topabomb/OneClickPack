const { app, Menu, Tray } = require('electron')
import path from 'path'
// 全局的消息中心
import msgBus from './messageBus'

let mainWindow = null
let tray = null
const util_tray = {
  show: (win) => {
    mainWindow = win
    tray = new Tray(path.join(__statics, '/trays/icon-tray.png'))
    const contextMenu = Menu.buildFromTemplate([
      { type: 'separator' },
      {
        label: '退出', type: 'normal', click: () => {
          win.destroy()// 全部窗口退出后由app事件处理关闭
        }
      }
    ])
    tray.setToolTip('Weero-OneclickPack:左键加载主界面，右键弹出快捷菜单.')
    tray.setContextMenu(contextMenu)
    tray.on('click', () => { // 我们这里模拟桌面程序点击通知区图标实现打开关闭应用的功能
      win.isVisible() ? null : tray.destroy()
      win.isVisible() ? win.hide() : win.show()
      win.isVisible() ? win.setSkipTaskbar(false) : win.setSkipTaskbar(true)
    })
  },
  minimize: () => {
    mainWindow.hide()
    mainWindow.setSkipTaskbar(true)
  },
  close: () => {
    if (tray) {
      tray.destroy()
      tray = null
    }
  }
}
export default util_tray
