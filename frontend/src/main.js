import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import 'element-plus/theme-chalk/dark/css-vars.css'
import App from './App.vue'
import router from './router'
import './styles/workspace.css'
import i18n from './i18n'
import './styles/theme.css'
import './styles/mml.css'

const savedTheme = localStorage.getItem('theme')
const prefersDark = window.matchMedia?.('(prefers-color-scheme: dark)').matches
const initialTheme = savedTheme || (prefersDark ? 'dark' : 'light')
document.documentElement.classList.toggle('dark', initialTheme === 'dark')
document.documentElement.style.colorScheme = initialTheme

const app = createApp(App)
app.use(ElementPlus)
app.use(i18n)
app.use(router)
app.mount('#app')
