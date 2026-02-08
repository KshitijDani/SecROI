import { copyFile, mkdir, readdir, stat } from "node:fs/promises";
import { join, resolve } from "node:path";

const projectRoot = resolve("..");
const sourceDir = join(projectRoot, "code_file_vulnerabilities");
const targetDir = resolve("public");
const targetFile = join(targetDir, "vulnerabilities.json");

async function getLatestReport() {
  let files;
  try {
    files = await readdir(sourceDir);
  } catch (error) {
    throw new Error(`Cannot read ${sourceDir}. Run the ETL pipeline first.`);
  }

  const candidates = files
    .filter((file) => file.startsWith("vulnerabilities_") && file.endsWith(".json"))
    .sort();

  if (!candidates.length) {
    throw new Error("No vulnerabilities_*.json files found.");
  }

  const latestName = candidates[candidates.length - 1];
  const latestPath = join(sourceDir, latestName);
  const stats = await stat(latestPath);
  return { latestPath, latestName, mtime: stats.mtime };
}

async function main() {
  await mkdir(targetDir, { recursive: true });
  const { latestPath, latestName, mtime } = await getLatestReport();
  await copyFile(latestPath, targetFile);
  console.log(`Copied ${latestName} (${mtime.toISOString()}) -> ${targetFile}`);
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
