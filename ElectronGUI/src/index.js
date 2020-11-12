const { app, BrowserWindow, ipcMain, remote } = require('electron');
const path = require('path');
const fs = require('fs');
const { spawn } = require("child_process");

// Handle creating/removing shortcuts on Windows when installing/uninstalling.
if (require('electron-squirrel-startup')) { // eslint-disable-line global-require
  app.quit();
}

const createWindow = () => {
  // Create the browser window.
  const mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      nodeIntegration: true,
    }
  });

  mainWindow.maximize();
  // and load the index.html of the app.
  mainWindow.loadFile(path.join(__dirname, 'index.html'));

  // Open the DevTools.
  mainWindow.webContents.openDevTools();
};

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.on('ready', createWindow);

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on('window-all-closed', () => {
  if (process.platform !== 'darwin') {
    app.quit();
  }
});

app.on('activate', () => {
  // On OS X it's common to re-create a window in the app when the
  // dock icon is clicked and there are no other windows open.
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// In this file you can include the rest of your app's specific main process
// code. You can also put them in separate files and import them here.


ipcMain.on('switch_page', (event, arg) => {
  const filePath = path.join(__dirname, arg);
  const windows = BrowserWindow.getAllWindows();

  if(!fs.existsSync(filePath) || windows.length !== 1) return;
  windows[0].loadFile(filePath);
})

ipcMain.on('start_cli', (event, arg) => {
  
  let commandArgs = [`${path.join(__dirname, '../../cli/main.py')}`]
  arg.files.forEach((file) => {
    commandArgs.push('-f');
    commandArgs.push(`${file}`);
  })
  if(arg.onlyHost){
    commandArgs.push('--only-host');
  }

  const pyCli = spawn('python3', commandArgs);

  pyCli.stdout.on("data", data => {
      console.log(`stdout: ${data}`);
  });

  pyCli.stderr.on("data", data => {
      console.log(`stderr: ${data}`);
  });

  pyCli.on('error', (error) => {
      console.log(`error: ${error.message}`);
  });

  pyCli.on("close", code => {
      console.log(`child process exited with code ${code}`);
  });
})