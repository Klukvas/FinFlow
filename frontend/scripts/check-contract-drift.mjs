import { createHash } from "crypto";
import { readFileSync, existsSync } from "fs";
import { join, dirname } from "path";
import { fileURLToPath } from "url";

const __dirname = dirname(fileURLToPath(import.meta.url));
const generatedDir = join(__dirname, "..", "src", "types", "generated");
const manifestPath = join(generatedDir, "MANIFEST.json");

if (!existsSync(manifestPath)) {
  console.error("ERROR: MANIFEST.json not found. Run `yarn generate:types` first.");
  process.exit(2);
}

const manifest = JSON.parse(readFileSync(manifestPath, "utf8"));
const schemaCount = Object.keys(manifest.schemas).length;
let drifted = false;
let checked = 0;
let skipped = 0;

for (const [service, expectedHash] of Object.entries(manifest.schemas)) {
  const schemaPath = join(generatedDir, "schemas", `${service}.json`);

  if (!existsSync(schemaPath)) {
    console.warn(`SKIP: ${service} — schema file missing`);
    skipped++;
    continue;
  }

  const content = readFileSync(schemaPath);
  const actualHash = createHash("sha256").update(content).digest("hex");
  checked++;

  if (actualHash !== expectedHash) {
    console.error(`DRIFT: ${service} — schema changed since last generation`);
    console.error(`  expected: ${expectedHash}`);
    console.error(`  actual:   ${actualHash}`);
    drifted = true;
  }
}

console.log(`\nChecked ${checked}/${schemaCount} schemas, skipped ${skipped}.`);

// Fail if too many schemas were skipped (missing from disk)
const MAX_SKIPS = 2;
if (skipped > MAX_SKIPS) {
  console.error(
    `\nERROR: ${skipped} schemas missing (max allowed: ${MAX_SKIPS}).`
  );
  console.error("Ensure all services are running and re-collect schemas.");
  process.exit(2);
}

if (drifted) {
  console.error(
    "\nAPI contract drift detected! Backend schemas have changed."
  );
  console.error(
    "Run `yarn generate:types` locally and commit the updated files."
  );
  process.exit(1);
}

console.log("All schemas match. No contract drift detected.");
