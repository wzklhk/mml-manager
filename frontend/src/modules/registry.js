import { mmlMenu } from "./mml/menu";
import { mmlRoutes } from "./mml/routes";

/**
 * @typedef {Object} AppModule
 * @property {string} id
 * @property {string} name Translation key
 * @property {string} code
 * @property {string} description Translation key
 * @property {string} icon
 * @property {string} group Translation key
 * @property {boolean} enabled
 * @property {string} [path]
 * @property {Array<{id: string, title: string, path?: string, enabled: boolean}>} [menu]
 * @property {import('vue-router').RouteRecordRaw[]} [routes]
 */

/** @type {AppModule[]} */
export const appModules = [
  {
    id: "mml",
    name: "workspace.modules.mml.name",
    code: "MML",
    description: "workspace.modules.mml.description",
    icon: "≡",
    group: "workspace.groups.configuration",
    enabled: true,
    path: "/mml",
    menu: mmlMenu,
    routes: mmlRoutes,
  },
  {
    id: "templates",
    name: "workspace.modules.templates.name",
    code: "TEMPLATE",
    description: "workspace.modules.templates.description",
    icon: "▤",
    group: "workspace.groups.configuration",
    enabled: false,
  },
  {
    id: "generator",
    name: "workspace.modules.generator.name",
    code: "CONFIG",
    description: "workspace.modules.generator.description",
    icon: "⌘",
    group: "workspace.groups.configuration",
    enabled: false,
  },
  {
    id: "ipam",
    name: "workspace.modules.ipam.name",
    code: "IPAM",
    description: "workspace.modules.ipam.description",
    icon: "⊞",
    group: "workspace.groups.planning",
    enabled: false,
  },
  {
    id: "conflicts",
    name: "workspace.modules.conflicts.name",
    code: "SUBNET",
    description: "workspace.modules.conflicts.description",
    icon: "⊕",
    group: "workspace.groups.planning",
    enabled: false,
  },
  {
    id: "lld",
    name: "workspace.modules.lld.name",
    code: "LLD",
    description: "workspace.modules.lld.description",
    icon: "▧",
    group: "workspace.groups.planning",
    enabled: false,
  },
  {
    id: "elements",
    name: "workspace.modules.elements.name",
    code: "NE",
    description: "workspace.modules.elements.description",
    icon: "▦",
    group: "workspace.groups.resources",
    enabled: false,
  },
  {
    id: "sites",
    name: "workspace.modules.sites.name",
    code: "SITE",
    description: "workspace.modules.sites.description",
    icon: "⌂",
    group: "workspace.groups.resources",
    enabled: false,
  },
  {
    id: "topology",
    name: "workspace.modules.topology.name",
    code: "TOPOLOGY",
    description: "workspace.modules.topology.description",
    icon: "◇",
    group: "workspace.groups.resources",
    enabled: false,
  },
  {
    id: "checks",
    name: "workspace.modules.checks.name",
    code: "CHECK",
    description: "workspace.modules.checks.description",
    icon: "✓",
    group: "workspace.groups.operations",
    enabled: false,
  },
  {
    id: "diff",
    name: "workspace.modules.diff.name",
    code: "DIFF",
    description: "workspace.modules.diff.description",
    icon: "⇄",
    group: "workspace.groups.operations",
    enabled: false,
  },
  {
    id: "batch",
    name: "workspace.modules.batch.name",
    code: "BATCH",
    description: "workspace.modules.batch.description",
    icon: "▥",
    group: "workspace.groups.operations",
    enabled: false,
  },
  {
    id: "transfer",
    name: "workspace.modules.transfer.name",
    code: "DATA",
    description: "workspace.modules.transfer.description",
    icon: "⇅",
    group: "workspace.groups.system",
    enabled: false,
  },
  {
    id: "settings",
    name: "workspace.modules.settings.name",
    code: "SYSTEM",
    description: "workspace.modules.settings.description",
    icon: "⚙",
    group: "workspace.groups.system",
    enabled: false,
  },
];

export const moduleGroups = [...new Set(appModules.map((module) => module.group))].map((name) => ({
  name,
  modules: appModules.filter((module) => module.group === name),
}));
export const getModule = (id) => appModules.find((module) => module.id === id);
