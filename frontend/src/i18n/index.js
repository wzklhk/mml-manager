import { createI18n } from 'vue-i18n'
import en from './en.json'
import zh from './zh.json'

function loadLocale() {
  const saved = localStorage.getItem('locale')
  if (saved) return saved
  const lang = navigator.language || navigator.userLanguage
  return lang.startsWith('zh') ? 'zh' : 'en'
}

const i18n = createI18n({
  locale: loadLocale(),
  fallbackLocale: 'en',
  messages: { en, zh },
  legacy: false,  // 使用 Composition API 模式
  globalInjection: true  // 允许模板中直接使用 $t
})

export default i18n
