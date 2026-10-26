// Genera los íconos de la PWA a partir de public/logo.svg:  npx pwa-assets-generator
import { defineConfig, minimal2023Preset } from "@vite-pwa/assets-generator/config";

export default defineConfig({
  headLinkOptions: { preset: "2023" },
  preset: {
    ...minimal2023Preset,
    // Android recorta el ícono "maskable" en círculo o gota: se le deja margen y fondo de marca.
    maskable: { ...minimal2023Preset.maskable, padding: 0.3, resizeOptions: { background: "#0D1B33" } },
    apple: { ...minimal2023Preset.apple, padding: 0.3, resizeOptions: { background: "#0D1B33" } },
  },
  images: ["public/logo.svg"],
});
