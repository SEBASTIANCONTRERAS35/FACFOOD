import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [
    react(),
    // PWA: se instala desde el navegador ("Agregar a pantalla de inicio") y abre sin conexión.
    // El service worker solo existe en el build (npm run build / preview), no en `npm run dev`.
    VitePWA({
      registerType: "prompt",
      injectRegister: false,
      includeAssets: ["favicon.ico", "favicon.svg", "apple-touch-icon-180x180.png"],
      manifest: {
        name: "FACFOOD · La comida de CU",
        short_name: "FACFOOD",
        description: "Pide comida de los puestos de Ciudad Universitaria: recoge o recibe con un estudiante.",
        lang: "es-MX",
        dir: "ltr",
        start_url: "/explorar",
        scope: "/",
        display: "standalone",
        orientation: "portrait",
        theme_color: "#0D1B33",
        background_color: "#F6F5F2",
        categories: ["food", "shopping"],
        icons: [
          { src: "pwa-64x64.png", sizes: "64x64", type: "image/png" },
          { src: "pwa-192x192.png", sizes: "192x192", type: "image/png" },
          { src: "pwa-512x512.png", sizes: "512x512", type: "image/png" },
          { src: "maskable-icon-512x512.png", sizes: "512x512", type: "image/png", purpose: "maskable" },
        ],
        shortcuts: [
          { name: "Explorar puestos", url: "/explorar", icons: [{ src: "pwa-192x192.png", sizes: "192x192" }] },
          { name: "Mis pedidos", url: "/pedidos", icons: [{ src: "pwa-192x192.png", sizes: "192x192" }] },
          { name: "Modo repartidor", url: "/repartidor", icons: [{ src: "pwa-192x192.png", sizes: "192x192" }] },
        ],
      },
      workbox: {
        globPatterns: ["**/*.{js,css,html,svg,png,ico,woff2}"],
        // Cualquier ruta de la app abre aunque no haya red (es una SPA).
        navigateFallback: "index.html",
        cleanupOutdatedCaches: true,
      },
    }),
  ],
  server: { port: 5173 },
  test: { environment: "jsdom" },
});
