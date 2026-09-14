import { createApp } from "vue";
import ElementPlus from "element-plus";
import "element-plus/dist/index.css";
import "element-plus/theme-chalk/dark/css-vars.css";
import App from "./App.vue";
import router from "./router";
import "./styles/workspace.css";
import i18n from "./i18n";
import { applyTheme, getInitialTheme } from "./appearance/themes";
import "./styles/theme.css";
import "./styles/mml.css";

applyTheme(getInitialTheme());

const app = createApp(App);
app.use(ElementPlus);
app.use(i18n);
app.use(router);
app.mount("#app");
