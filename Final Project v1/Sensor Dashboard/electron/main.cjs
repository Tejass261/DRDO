const { app, BrowserWindow } = require("electron");
const path = require("path");

let mainWindow;


// ============================================================
// CREATE WINDOW
// ============================================================

function createWindow() {

  mainWindow = new BrowserWindow({

    width: 1250,
    height: 780,

    minWidth: 900,
    minHeight: 600,

    webPreferences: {

      preload: path.join(
        __dirname,
        "preload.cjs"
      ),

      // React is isolated from Node.js.
      contextIsolation: true,

      // React cannot directly access Node.js.
      nodeIntegration: false,

      sandbox: true
    }
  });


  // ==========================================================
  // DEVELOPMENT
  // ==========================================================

  if (process.env.VITE_DEV_SERVER_URL) {

    mainWindow.loadURL(
      process.env.VITE_DEV_SERVER_URL
    );

  }

  // ==========================================================
  // PRODUCTION
  // ==========================================================

  else {

    mainWindow.loadFile(
      path.join(
        __dirname,
        "..",
        "dist",
        "index.html"
      )
    );
  }
}


// ============================================================
// APPLICATION START
// ============================================================

app.whenReady().then(() => {

  createWindow();

});


// ============================================================
// CLOSE BEHAVIOUR
// ============================================================

app.on(
  "window-all-closed",
  () => {

    if (process.platform !== "darwin") {

      app.quit();

    }

  }
);