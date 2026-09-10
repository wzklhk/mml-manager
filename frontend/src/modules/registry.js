import { mmlMenu } from './mml/menu'
import { mmlRoutes } from './mml/routes'

/**
 * @typedef {Object} AppModule
 * @property {string} id
 * @property {string} name
 * @property {string} code
 * @property {string} description
 * @property {string} icon
 * @property {string} group
 * @property {boolean} enabled
 * @property {string} [path]
 * @property {Array<{id: string, title: string, path?: string, enabled: boolean}>} [menu]
 * @property {import('vue-router').RouteRecordRaw[]} [routes]
 */

/** @type {AppModule[]} */
export const appModules = [
  { id: 'mml', name: 'MML 配置管理', code: 'MML', description: '查询、维护与对比网元配置，管理导入快照。', icon: '≡', group: '配置管理', enabled: true, path: '/mml', menu: mmlMenu, routes: mmlRoutes },
  { id: 'templates', name: '配置模板', code: 'TEMPLATE', description: '统一维护可复用的配置模板。', icon: '▤', group: '配置管理', enabled: false },
  { id: 'generator', name: '配置生成', code: 'CONFIG', description: '根据规划参数生成设备配置。', icon: '⌘', group: '配置管理', enabled: false },
  { id: 'ipam', name: 'IP 地址规划', code: 'IPAM', description: '规划地址池、子网与 IP 分配。', icon: '⊞', group: '网络规划', enabled: false },
  { id: 'conflicts', name: '子网冲突检测', code: 'SUBNET', description: '检查地址规划中的子网重叠。', icon: '⊕', group: '网络规划', enabled: false },
  { id: 'lld', name: 'LLD 管理', code: 'LLD', description: '组织网络详细设计与交付文档。', icon: '▧', group: '网络规划', enabled: false },
  { id: 'elements', name: '网元资源', code: 'NE', description: '集中管理网元基础信息。', icon: '▦', group: '网络资源', enabled: false },
  { id: 'sites', name: '站点管理', code: 'SITE', description: '整理站点与网络资源归属。', icon: '⌂', group: '网络资源', enabled: false },
  { id: 'topology', name: '网络拓扑', code: 'TOPOLOGY', description: '呈现网络连接与资源关系。', icon: '◇', group: '网络资源', enabled: false },
  { id: 'checks', name: '配置检查', code: 'CHECK', description: '检查配置规范与一致性。', icon: '✓', group: '运维工具', enabled: false },
  { id: 'diff', name: '数据对比', code: 'DIFF', description: '跨来源的数据差异分析。', icon: '⇄', group: '运维工具', enabled: false },
  { id: 'batch', name: '批量配置', code: 'BATCH', description: '组织跨网元批量配置任务。', icon: '▥', group: '运维工具', enabled: false },
  { id: 'transfer', name: '数据导入导出', code: 'DATA', description: '系统级数据交换与备份。', icon: '⇅', group: '系统管理', enabled: false },
  { id: 'settings', name: '系统设置', code: 'SYSTEM', description: '管理工作台全局设置。', icon: '⚙', group: '系统管理', enabled: false }
]

export const moduleGroups = [...new Set(appModules.map(module => module.group))]
  .map(name => ({ name, modules: appModules.filter(module => module.group === name) }))
export const getModule = id => appModules.find(module => module.id === id)
