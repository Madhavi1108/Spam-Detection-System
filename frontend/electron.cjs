const { BrowserWindow, app } = require("electron");
const path = require("path");

function createWindow() {
  const win = new BrowserWindow({
    width: 1200,
    height: 800
  });

  const indexPath = path.join(app.getAppPath(), "dist", "index.html");

  console.log("Loading:", indexPath);

  win.loadFile(indexPath);
}

app.whenReady().then(createWindow);