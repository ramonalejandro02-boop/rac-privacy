import { loadFont } from "@remotion/fonts";
import { staticFile } from "remotion";

// Fuentes locales (public/fonts) para que el render no dependa de internet.
loadFont({ family: "Anton", url: staticFile("fonts/Anton-400.woff2"), weight: "400" });
loadFont({ family: "Inter", url: staticFile("fonts/Inter-600.woff2"), weight: "600" });
loadFont({ family: "Montserrat", url: staticFile("fonts/Montserrat-900.woff2"), weight: "900" });
