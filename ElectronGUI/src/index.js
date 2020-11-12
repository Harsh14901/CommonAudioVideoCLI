/* eslint-disable no-param-reassign */
const { app, BrowserWindow, ipcMain } = require("electron");
const path = require("path");
const fs = require("fs");
const { spawn } = require("child_process");
const { stderr } = require("process");

let pyCliStat = {
  process: null,
  running: false,
  numInstances: 0,
  stdout: "",
  stderr: "",
  error: null,
};

// Handle creating/removing shortcuts on Windows when installing/uninstalling.
// eslint-disable-next-line global-require
if (require("electron-squirrel-startup")) {
  // eslint-disable-line global-require
  app.quit();
}

const createWindow = () => {
  // Create the browser window.
  const mainWindow = new BrowserWindow({
    width: 800,
    height: 600,
    webPreferences: {
      nodeIntegration: true,
    },
  });

  mainWindow.maximize();
  // and load the index.html of the app.
  mainWindow.loadFile(path.join(__dirname, "index.html"));

  // Open the DevTools.
  mainWindow.webContents.openDevTools();
};

// This method will be called when Electron has finished
// initialization and is ready to create browser windows.
// Some APIs can only be used after this event occurs.
app.on("ready", createWindow);

// Quit when all windows are closed, except on macOS. There, it's common
// for applications and their menu bar to stay active until the user quits
// explicitly with Cmd + Q.
app.on("window-all-closed", () => {
  if (process.platform !== "darwin") {
    if (pyCliStat.process) {
      pyCliStat.process.kill("SIGINT");
    }
    app.quit();
  }
});

app.on("activate", () => {
  // On OS X it's common to re-create a window in the app when the
  // dock icon is clicked and there are no other windows open.
  if (BrowserWindow.getAllWindows().length === 0) {
    createWindow();
  }
});

// In this file you can include the rest of your app's specific main process
// code. You can also put them in separate files and import them here.

ipcMain.on("switch_page", (event, arg) => {
  const filePath = path.join(__dirname, arg);
  const windows = BrowserWindow.getAllWindows();

  if (!fs.existsSync(filePath) || windows.length !== 1) return;
  windows[0].loadFile(filePath);
});

const runCLI = async (arg) => {
  const commandArgs = [`${path.join(__dirname, "../../cli/dist/LocalParty")}`];
  arg.files.forEach((file) => {
    commandArgs.push("-f");
    commandArgs.push(`${file}`);
  });
  if (arg.onlyHost) {
    commandArgs.push("--only-host");
  }

  if (arg.qr) {
    commandArgs.push("--qr");
  }

  const pyCli = spawn("party", commandArgs, {
    cwd: path.join(__dirname, "../../cli"),
    shell: true,
  });
  pyCliStat.process = pyCli;
  pyCliStat.numInstances += 1;

  pyCli.stdout.on("data", (data) => {
    console.log(data);
    pyCliStat.stdout += data;
  });

  pyCli.stderr.on("data", (data) => {
    console.log(stderr);
    pyCliStat.stderr += data;
  });

  pyCli.on("error", (error) => {
    pyCliStat.error = error;
  });

  pyCli.on("close", (code) => {
    console.log(`child process exited with code ${code}`);
    pyCliStat = {
      process: null,
      running: false,
      numInstances: 0,
      stdout: "",
      stderr: "",
      error: null,
    };
  });
};

ipcMain.on("start_cli", async (event, arg) => {
  if (pyCliStat.process) return;
  runCLI(arg);
});

// eslint-disable-next-line no-unused-vars
ipcMain.on("terminalOutput", (event, arg) => {
  if (!pyCliStat.process) {
    event.reply("terminalOutput", "No process found");
    return;
  }
  event.reply("terminalOutput", pyCliStat.stdout);
  event.reply("terminalOutput", pyCliStat.stderr);
  pyCliStat.stdout = "";
  pyCliStat.stderr = "";
});

// eslint-disable-next-line no-unused-vars
ipcMain.on("killCLI", (event, arg) => {
  if (!pyCliStat.process) return;
  pyCliStat.process.kill();
  pyCliStat = {
    process: null,
    running: false,
    numInstances: 0,
    stdout: "",
    stderr: "",
    error: null,
  };
});
