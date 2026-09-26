import { createRoot } from "react-dom/client";
import App from "./App.jsx";
import "./style.css";

// ============================================================
// REACT ENTRY POINT
// ============================================================
//
// This file only starts the React application. All of the
// actual UI and logic lives in App.jsx and the files it uses.
// ============================================================

createRoot(document.getElementById("root")).render(<App />);
