import { Config } from "@remotion/cli/config";
import fs from "fs";

// En la sesión en la nube usamos el Chromium preinstalado; en tu PC Remotion descarga el suyo.
const CLOUD_CHROME = "/opt/pw-browsers/chromium_headless_shell-1243/chrome-headless-shell-linux64/chrome-headless-shell";
if (fs.existsSync(CLOUD_CHROME)) Config.setBrowserExecutable(CLOUD_CHROME);
Config.setVideoImageFormat("jpeg");
Config.setConcurrency(4);
