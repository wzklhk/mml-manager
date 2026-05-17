import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import en from 'element-plus/dist/locale/en.mjs'
import App from './App.vue'
import i18n from './i18n'
import './styles/theme.css'

const app = createApp(App)
app.use(ElementPlus, { locale: i18n.global.locale === 'zh' ? zhCn : en })
app.use(i18n)
app.mount('#app')
