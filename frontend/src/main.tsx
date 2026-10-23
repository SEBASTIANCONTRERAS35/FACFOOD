import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import "leaflet/dist/leaflet.css";
import "./theme/global.css";
import "./components/componentes.css";
import App from "./app/App";
import { registerSW } from "virtual:pwa-register";

// Service worker de la PWA (solo existe en el build; en `npm run dev` no hace nada).
registerSW({ immediate: true });

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
);
