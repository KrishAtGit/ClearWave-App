// this file tells typescript about the setting 
// just declaration file and TS reads it


/// <reference types="vite/client" />

// adds custom env variable to vite built-in importmetaenv type
interface ImportMetaEnv {
  readonly VITE_API_URL?: string
}
