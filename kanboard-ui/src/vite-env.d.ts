/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_KANBOARD_URL: string;
  readonly VITE_KANBOARD_USER: string;
  readonly VITE_KANBOARD_PASSWORD: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
