import { fileURLToPath } from "node:url";
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
        // Qué se guarda para usarse sin conexión. Lo que no aparece aquí (login, perfil, órdenes,
        // pagos, entregas, panel del vendedor) SIEMPRE va a la red: son dinero y estados en vivo.
        runtimeCaching: [
          {
            // Catálogo público: puestos, menú, categorías y destinos. Con red, siempre fresco;
            // sin red (o si tarda más de 4 s), lo último guardado.
            urlPattern: ({ url, request }) =>
              request.method === "GET" && /^\/(puntos-venta|destinos)(\/|$)/.test(url.pathname),
            handler: "NetworkFirst",
            options: {
              cacheName: "api-catalogo",
              networkTimeoutSeconds: 4,
              expiration: { maxEntries: 100, maxAgeSeconds: 60 * 60 * 24 },
              cacheableResponse: { statuses: [200] },
            },
          },
          {
            // Mosaicos del mapa ya vistos. Se guardan al verlos; nunca se descargan por adelantado
            // (política de uso de OpenStreetMap).
            urlPattern: /^https:\/\/[abc]\.tile\.openstreetmap\.org\/.*/,
            handler: "CacheFirst",
            options: {
              cacheName: "mapa-osm",
              expiration: { maxEntries: 300, maxAgeSeconds: 60 * 60 * 24 * 7 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
          {
            urlPattern: /^https:\/\/fonts\.googleapis\.com\/.*/,
            handler: "StaleWhileRevalidate",
            options: { cacheName: "fuentes-css" },
          },
          {
            urlPattern: /^https:\/\/fonts\.gstatic\.com\/.*/,
            handler: "CacheFirst",
            options: {
              cacheName: "fuentes",
              expiration: { maxEntries: 20, maxAgeSeconds: 60 * 60 * 24 * 365 },
              cacheableResponse: { statuses: [0, 200] },
            },
          },
        ],
      },
    }),
  ],
  server: { port: 5173 },
  test: {
    environment: "jsdom",
    alias: { "virtual:pwa-register/react": fileURLToPath(new URL("./src/pwa/registro-prueba.ts", import.meta.url)) },
  },
});
