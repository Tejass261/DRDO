const { app, BrowserWindow } = require("electron");
const path = require("path");

let mainWindow;


// ============================================================
// CREATE WINDOW
// ============================================================

function createWindow() {

  mainWindow = new BrowserWindow({

    width: 1400,
    height: 850,

    minWidth: 1100,
    minHeight: 700,

    backgroundColor: "#d9d9d9",

    webPreferences: {

      preload: path.join(
        __dirname,
        "preload.cjs"
      ),

      contextIsolation: true,
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

  app.on("activate", () => {

    if (
      BrowserWindow.getAllWindows().length === 0
    ) {

      createWindow();

    }

  });

});


// ============================================================
// CLOSE
// ============================================================

app.on(
  "window-all-closed",
  () => {

    if (process.platform !== "darwin") {

      app.quit();

    }

  }
);