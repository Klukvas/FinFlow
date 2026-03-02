import { createHash } from "crypto";
import { existsSync, readdirSync, readFileSync, writeFileSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const schemasDir = join(__dirname, "..", "src", "types", "generated", "schemas");
const outPath = join(__dirname, "..", "src", "types", "generated", "MANIFEST.json");

if (!existsSync(schemasDir)) {
  console.error(`ERROR: schemas directory not found: ${schemasDir}`);
  process.exit(1);
}

const files = readdirSync(schemasDir).filter((f) => f.endsWith(".json"));

if (files.length === 0) {
  console.error("ERROR: No .json schema files found in schemas directory.");
  process.exit(1);
}

const schemas = files.reduce((acc, file) => {
  const content = readFileSync(join(schemasDir, file));
  const hash = createHash("sha256").update(content).digest("hex");
  return { ...acc, [file.replace(".json", "")]: hash };
}, {});

const manifest = { schemas };

writeFileSync(outPath, JSON.stringify(manifest, null, 2) + "\n");
console.log(`Manifest written with ${Object.keys(schemas).length} schema hashes.`);
