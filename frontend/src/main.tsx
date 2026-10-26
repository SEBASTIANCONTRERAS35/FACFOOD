import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import "leaflet/dist/leaflet.css";
import "./theme/global.css";
import "./components/componentes.css";
import App from "./app/App";
// Escucha "beforeinstallprompt" desde el arranque (puede llegar antes de que React monte).
import "./pwa/instalacion";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
);
