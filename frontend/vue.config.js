const path = require('path')

module.exports = {
  // 生产环境：前端静态文件由 Flask 在 /static 路径下提供
  // 开发环境：Vue CLI devServer 代理 /api 到 Flask (localhost:5000)
  publicPath: '/static/',
  outputDir: path.resolve(__dirname, '../converter/static'),

  devServer: {
    port: 8080,
    proxy: {
      '/api': {
        target: 'http://localhost:5000',
        changeOrigin: true
      }
    }
  }
}
