import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import process from "node:process";

const sourceRoot = path.resolve("src");
const expectedOrder = ["template", "script", "style"];
const orderIndex = new Map(expectedOrder.map((tag, index) => [tag, index]));

async function findVueFiles(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const files = await Promise.all(
    entries.map((entry) => {
      const entryPath = path.join(directory, entry.name);
      return entry.isDirectory() ? findVueFiles(entryPath) : entryPath.endsWith(".vue") ? [entryPath] : [];
    }),
  );
  return files.flat();
}

const invalidFiles = [];

for (const file of await findVueFiles(sourceRoot)) {
  const content = await readFile(file, "utf8");
  const blocks = [...content.matchAll(/^<(template|script|style)\b/gm)].map((match) => match[1]);
  const isOrdered = blocks.every(
    (block, index) => index === 0 || orderIndex.get(blocks[index - 1]) <= orderIndex.get(block),
  );

  if (!isOrdered) {
    invalidFiles.push(`${path.relative(process.cwd(), file)} (${blocks.join(" → ")})`);
  }
}

if (invalidFiles.length > 0) {
  console.error("Vue 顶层区块必须按 template → script → style 排列：");
  invalidFiles.forEach((file) => console.error(`- ${file}`));
  process.exitCode = 1;
} else {
  console.log("Vue 顶层区块顺序检查通过：template → script → style");
}
