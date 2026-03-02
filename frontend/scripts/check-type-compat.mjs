#!/usr/bin/env node
/**
 * Type Compatibility Checker
 *
 * Compares hand-written frontend TypeScript types with OpenAPI-generated schemas
 * and reports mismatches (missing fields, type differences, nullability drift).
 *
 * Usage:
 *   node scripts/check-type-compat.mjs            # report mode (exit 0)
 *   node scripts/check-type-compat.mjs --strict    # exit 1 on errors/warnings
 *   node scripts/check-type-compat.mjs --json      # JSON output
 */

import { readFileSync, existsSync, readdirSync } from "node:fs";
import { resolve, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { TYPE_MAPPINGS } from "./type-compat-mapping.mjs";

const __dirname = dirname(fileURLToPath(import.meta.url));
const TYPES_DIR = resolve(__dirname, "../src/types");
const SCHEMAS_DIR = resolve(__dirname, "../src/types/generated/schemas");

const strict = process.argv.includes("--strict");
const jsonOutput = process.argv.includes("--json");

// ─── OpenAPI Schema Parser ──────────────────────────────────────────────────

function resolveOpenApiType(prop, allSchemas) {
  if (!prop) return { type: "unknown", nullable: false, isRef: false, isArray: false };

  // $ref
  if (prop.$ref) {
    const refName = prop.$ref.split("/").pop();
    return { type: refName, nullable: false, isRef: true, isArray: false };
  }

  // allOf — typically a single $ref (enum or nested schema)
  if (prop.allOf) {
    const refItem = prop.allOf.find((i) => i.$ref);
    if (refItem) {
      const refName = refItem.$ref.split("/").pop();
      return { type: refName, nullable: false, isRef: true, isArray: false };
    }
    return resolveOpenApiType(prop.allOf[0], allSchemas);
  }

  // anyOf — nullable pattern: [{type: X}, {type: "null"}]  or  [{$ref}, {type: "null"}]
  if (prop.anyOf) {
    const nonNull = prop.anyOf.filter((v) => v.type !== "null");
    const hasNull = prop.anyOf.some((v) => v.type === "null");
    if (nonNull.length === 1) {
      const resolved = resolveOpenApiType(nonNull[0], allSchemas);
      return { ...resolved, nullable: hasNull };
    }
    // Multiple non-null types — union
    const types = nonNull.map((v) => resolveOpenApiType(v, allSchemas).type);
    return { type: types.join(" | "), nullable: hasNull, isRef: false, isArray: false };
  }

  // array
  if (prop.type === "array") {
    const itemType = prop.items ? resolveOpenApiType(prop.items, allSchemas) : { type: "unknown" };
    return { type: `${itemType.type}[]`, nullable: false, isRef: false, isArray: true };
  }

  // object without further schema (generic dict)
  if (prop.type === "object" && prop.additionalProperties) {
    const valType = resolveOpenApiType(prop.additionalProperties, allSchemas);
    return { type: `Record<string, ${valType.type}>`, nullable: false, isRef: false, isArray: false };
  }
  if (prop.type === "object" && !prop.properties) {
    return { type: "object", nullable: false, isRef: false, isArray: false };
  }

  // primitive
  const typeMap = { integer: "number", number: "number", string: "string", boolean: "boolean" };
  const baseType = typeMap[prop.type] || prop.type || "unknown";

  // format hints
  let finalType = baseType;
  if (prop.format === "date-time") finalType = "string"; // date-time stays string in TS
  if (prop.format === "date") finalType = "string";
  if (prop.format === "uuid") finalType = "string";

  return { type: finalType, nullable: false, isRef: false, isArray: false };
}

function extractOpenApiFields(schemaName, allSchemas) {
  const schema = allSchemas[schemaName];
  if (!schema || !schema.properties) return null;

  const requiredSet = new Set(schema.required || []);
  const fields = {};

  for (const [name, prop] of Object.entries(schema.properties)) {
    const resolved = resolveOpenApiType(prop, allSchemas);
    fields[name] = {
      type: resolved.type,
      nullable: resolved.nullable,
      required: requiredSet.has(name),
      isRef: resolved.isRef,
      isArray: resolved.isArray,
    };
  }

  return fields;
}

// ─── TypeScript Parser ──────────────────────────────────────────────────────

function extractTsFields(filePath, interfaceName) {
  if (!existsSync(filePath)) return null;

  const content = readFileSync(filePath, "utf-8");
  const lines = content.split("\n");

  // Find interface start — handle `export interface X {` and `export interface X extends Y {`
  // Allow leading whitespace for indented declarations
  const startPattern = new RegExp(
    `^\\s*export\\s+(?:interface|type)\\s+${escapeRegex(interfaceName)}\\b[^{]*\\{`
  );

  let startIdx = -1;
  for (let i = 0; i < lines.length; i++) {
    if (startPattern.test(lines[i])) {
      startIdx = i;
      break;
    }
  }

  if (startIdx === -1) return null;

  // Track brace depth to find interface end
  let depth = 0;
  let bodyStart = -1;
  const bodyLines = [];

  for (let i = startIdx; i < lines.length; i++) {
    for (const ch of lines[i]) {
      if (ch === "{") {
        if (depth === 0) bodyStart = i;
        depth++;
      }
      if (ch === "}") depth--;
    }
    if (bodyStart >= 0 && i > bodyStart) {
      if (depth > 0) bodyLines.push(lines[i]);
    }
    if (depth === 0 && bodyStart >= 0) break;
  }

  const fields = {};

  for (const line of bodyLines) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("//") || trimmed.startsWith("/*")) continue;

    // Strip inline comments (// ...)
    const noComment = trimmed.replace(/\/\/.*$/, "").trim();
    if (!noComment) continue;

    // Match:  fieldName?: Type;  or  fieldName: Type;
    const match = noComment.match(/^(\w+)(\?)?:\s*(.+?);?\s*$/);
    if (!match) continue;

    const [, name, optMark, rawType] = match;
    const optional = optMark === "?";

    // Check for `| null`
    const nullable = /\|\s*null\b/.test(rawType);
    const cleanType = rawType
      .replace(/\|\s*null\b/g, "")
      .replace(/\s+/g, " ")
      .trim();

    // Normalize type for comparison
    const normalizedType = normalizeTsType(cleanType);

    fields[name] = { type: normalizedType, optional, nullable };
  }

  return fields;
}

// ─── TS Type Alias Resolver ──────────────────────────────────────────────────

let _tsAliasCache = null;

/**
 * Scan all TS files in the types directory for `export type X = ...;` declarations
 * and return a map of alias name → resolved value string.
 */
function getTsAliases() {
  if (_tsAliasCache) return _tsAliasCache;
  _tsAliasCache = new Map();

  try {
    const files = readdirSync(TYPES_DIR).filter((f) => f.endsWith(".ts") && !f.endsWith(".d.ts"));
    for (const file of files) {
      try {
        const content = readFileSync(resolve(TYPES_DIR, file), "utf-8");
        // Match: export type FooBar = "a" | "b" | "c";
        const aliasRe = /^export\s+type\s+(\w+)\s*=\s*(.+?);?\s*$/gm;
        let m;
        while ((m = aliasRe.exec(content)) !== null) {
          const [, aliasName, aliasValue] = m;
          // Only store if it doesn't look like a generic/interface (no { })
          if (!aliasValue.includes("{")) {
            _tsAliasCache.set(aliasName, aliasValue.trim());
          }
        }
      } catch { /* skip unreadable files */ }
    }
  } catch { /* types dir not found */ }

  return _tsAliasCache;
}

/**
 * Check if a type alias resolves to a string literal union (e.g. "a" | "b").
 */
function isStringUnionAlias(typeName) {
  const aliases = getTsAliases();
  const value = aliases.get(typeName);
  if (!value) return false;
  // String literal union: all parts are quoted strings
  const parts = value.split("|").map((p) => p.trim());
  return parts.every((p) => /^["']/.test(p));
}

function normalizeTsType(raw) {
  // Remove trailing semicolons and extra whitespace
  let t = raw.replace(/;$/, "").trim();

  // Common TS → OpenAPI type normalizations
  if (t === "number") return "number";
  if (t === "string") return "string";
  if (t === "boolean") return "boolean";

  // Array patterns: Type[] or Array<Type>
  const arrMatch = t.match(/^(.+)\[\]$/) || t.match(/^Array<(.+)>$/);
  if (arrMatch) return `${normalizeTsType(arrMatch[1])}[]`;

  // Record/dict patterns
  const recordMatch = t.match(/^Record<string,\s*(.+)>$/);
  if (recordMatch) return `Record<string, ${normalizeTsType(recordMatch[1])}>`;

  return t;
}

function escapeRegex(str) {
  return str.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

// ─── Comparator ─────────────────────────────────────────────────────────────

function compareTypes(manualFields, generatedFields) {
  const issues = [];

  // Fields in generated (API) but not in manual (frontend)
  for (const [name, genField] of Object.entries(generatedFields)) {
    if (!manualFields[name]) {
      const severity = genField.required ? "warning" : "info";
      issues.push({
        severity,
        kind: "missing_in_manual",
        field: name,
        detail: `API: ${genField.type}${genField.nullable ? " | null" : ""}, ${genField.required ? "required" : "optional"}`,
      });
    }
  }

  // Fields in manual (frontend) but not in generated (API)
  for (const [name, manField] of Object.entries(manualFields)) {
    if (!generatedFields[name]) {
      issues.push({
        severity: "info",
        kind: "missing_in_generated",
        field: name,
        detail: `manual: ${manField.type}${manField.nullable ? " | null" : ""}`,
      });
    }
  }

  // Fields in both — compare types and nullability
  for (const [name, manField] of Object.entries(manualFields)) {
    const genField = generatedFields[name];
    if (!genField) continue;

    // Type mismatch (normalize for comparison)
    if (!typesCompatible(manField.type, genField.type)) {
      issues.push({
        severity: "error",
        kind: "type_mismatch",
        field: name,
        detail: `manual: ${manField.type}, API: ${genField.type}`,
      });
    }

    // Nullability mismatch
    if (genField.nullable && !manField.nullable && !manField.optional) {
      issues.push({
        severity: "warning",
        kind: "nullability_mismatch",
        field: name,
        detail: `API is nullable, manual is not (and not optional)`,
      });
    }
  }

  return issues;
}

// Cache for resolved enum base types (schema name → base type like "string")
let _resolvedEnums = null;

function getResolvedEnums() {
  if (_resolvedEnums) return _resolvedEnums;
  _resolvedEnums = new Map();

  try {
    const files = readdirSync(SCHEMAS_DIR).filter((f) => f.endsWith(".json"));
    for (const file of files) {
      try {
        const raw = JSON.parse(readFileSync(resolve(SCHEMAS_DIR, file), "utf-8"));
        const schemas = raw.components?.schemas || {};
        for (const [name, schema] of Object.entries(schemas)) {
          if (schema.enum && schema.type) {
            const typeMap = { integer: "number", number: "number", string: "string", boolean: "boolean" };
            _resolvedEnums.set(name, typeMap[schema.type] || schema.type);
          }
        }
      } catch { /* skip unparseable files */ }
    }
  } catch { /* schemas dir not found */ }
  return _resolvedEnums;
}

function typesCompatible(manualType, generatedType) {
  // Exact match
  if (manualType === generatedType) return true;

  // Normalize both to lower for loose comparison
  const m = manualType.toLowerCase();
  const g = generatedType.toLowerCase();
  if (m === g) return true;

  // "string" matches any string-based enum or string-format
  if (m === "string" && (g === "string" || g.includes("string"))) return true;
  if (g === "string" && (m === "string" || m.includes("string"))) return true;

  // number matches integer
  if ((m === "number" && g === "number") || (m === "number" && g === "integer")) return true;

  // Ref types — generated uses schema names, manual uses imported type names
  // Just compare case-insensitively
  if (m.replace(/\[\]$/, "") === g.replace(/\[\]$/, "")) return true;

  // Array comparison
  const mArr = manualType.match(/^(.+)\[\]$/);
  const gArr = generatedType.match(/^(.+)\[\]$/);
  if (mArr && gArr) return typesCompatible(mArr[1], gArr[1]);

  // Generic object/record types are loosely compatible
  if (m.startsWith("record<") && g.startsWith("record<")) return true;
  if ((m === "object" || m.startsWith("record<")) && (g === "object" || g.startsWith("record<"))) {
    return true;
  }

  // Check if generated type is an enum ref whose base type matches the manual type
  const enums = getResolvedEnums();
  const gBase = generatedType.replace(/\[\]$/, "");
  const mBase = manualType.replace(/\[\]$/, "");
  if (enums.has(gBase)) {
    const baseType = enums.get(gBase);
    if (m.replace(/\[\]$/, "") === baseType) return true;
    // Manual union literals like "a" | "b" are string-based
    if (baseType === "string" && (m.includes('"') || m.includes("'"))) return true;
  }

  // Manual type is a string literal union (e.g. "active" | "canceled") — compatible with string
  if ((m.includes('"') || m.includes("'")) && g === "string") return true;

  // Check if manual type is a TS type alias that resolves to a string literal union
  // (e.g., WorkspaceRole = "owner" | "full" | "read")
  if (isStringUnionAlias(manualType)) {
    // Compatible with string, string enums, or other string-based types
    if (g === "string") return true;
    // Also compatible with API enum refs that are string-based
    if (enums.has(gBase) && enums.get(gBase) === "string") return true;
  }

  // Check if both sides are known type mappings (e.g., Category[] ↔ CategoryOut[])
  const isArrayM = mBase !== manualType;
  const isArrayG = gBase !== generatedType;
  if (isArrayM === isArrayG) {
    const isMapped = TYPE_MAPPINGS.some(
      (mp) => mp.manual === mBase && mp.generated === gBase
    );
    if (isMapped) return true;
  }

  return false;
}

// ─── Main ───────────────────────────────────────────────────────────────────

function main() {
  const results = [];
  let totalChecked = 0;
  let totalErrors = 0;
  let totalWarnings = 0;
  let totalInfo = 0;
  let skipped = 0;

  for (const mapping of TYPE_MAPPINGS) {
    const schemaPath = resolve(SCHEMAS_DIR, `${mapping.service}.json`);
    const tsPath = resolve(TYPES_DIR, mapping.manualFile);

    // Load OpenAPI schema
    if (!existsSync(schemaPath)) {
      skipped++;
      results.push({
        mapping,
        issues: [],
        error: `Schema file not found: ${mapping.service}.json`,
      });
      continue;
    }

    let allSchemas;
    try {
      const raw = JSON.parse(readFileSync(schemaPath, "utf-8"));
      allSchemas = raw.components?.schemas || {};
    } catch {
      skipped++;
      results.push({ mapping, issues: [], error: `Failed to parse ${mapping.service}.json` });
      continue;
    }

    const generatedFields = extractOpenApiFields(mapping.generated, allSchemas);
    if (!generatedFields) {
      skipped++;
      results.push({
        mapping,
        issues: [],
        error: `Schema "${mapping.generated}" not found in ${mapping.service}.json`,
      });
      continue;
    }

    const manualFields = extractTsFields(tsPath, mapping.manual);
    if (!manualFields) {
      skipped++;
      results.push({
        mapping,
        issues: [],
        error: `Interface "${mapping.manual}" not found in ${mapping.manualFile}`,
      });
      continue;
    }

    const issues = compareTypes(manualFields, generatedFields);
    totalChecked++;

    for (const issue of issues) {
      if (issue.severity === "error") totalErrors++;
      else if (issue.severity === "warning") totalWarnings++;
      else totalInfo++;
    }

    results.push({ mapping, issues, error: null });
  }

  // ─── Output ─────────────────────────────────────────────────────────────

  if (jsonOutput) {
    const output = {
      summary: {
        types_checked: totalChecked,
        skipped,
        total_issues: totalErrors + totalWarnings + totalInfo,
        errors: totalErrors,
        warnings: totalWarnings,
        info: totalInfo,
      },
      results: results.map((r) => ({
        manual: r.mapping.manual,
        manualFile: r.mapping.manualFile,
        generated: r.mapping.generated,
        service: r.mapping.service,
        error: r.error,
        issues: r.issues,
      })),
    };
    process.stdout.write(JSON.stringify(output, null, 2) + "\n");
  } else {
    printReport(results, totalChecked, skipped, totalErrors, totalWarnings, totalInfo);
  }

  if (strict && (totalErrors > 0 || totalWarnings > 0)) {
    process.exit(1);
  }
}

function printReport(results, totalChecked, skipped, totalErrors, totalWarnings, totalInfo) {
  console.log("\n=== Type Compatibility Report ===\n");

  const severityIcon = { error: "\u2718 ERROR", warning: "\u26A0 WARN ", info: "\u2139 INFO " };

  for (const { mapping, issues, error } of results) {
    if (error) {
      console.log(`${mapping.manual} (${mapping.manualFile}) \u2014 SKIPPED: ${error}`);
      console.log();
      continue;
    }

    if (issues.length === 0) continue; // Only print types with issues

    const label = mapping.manual === mapping.generated
      ? mapping.manual
      : `${mapping.manual} \u2194 ${mapping.generated}`;

    console.log(`${label} (${mapping.manualFile}) \u2194 ${mapping.service}.json`);

    for (const issue of issues) {
      const icon = severityIcon[issue.severity];
      console.log(`  ${icon}  ${padRight(issue.kind, 22)} ${padRight(issue.field, 24)} (${issue.detail})`);
    }
    console.log();
  }

  console.log("--- Summary ---");
  console.log(
    `Types checked: ${totalChecked} | Skipped: ${skipped} | ` +
    `Issues: ${totalErrors + totalWarnings + totalInfo} | ` +
    `Errors: ${totalErrors} | Warnings: ${totalWarnings} | Info: ${totalInfo}`
  );

  if (totalErrors > 0) {
    console.log("\nType errors found! These may cause runtime crashes.");
  }
  if (totalWarnings > 0) {
    console.log("Warnings indicate potential issues (missing fields, nullability drift).");
  }
  console.log();
}

function padRight(str, len) {
  return str.length >= len ? str : str + " ".repeat(len - str.length);
}

main();
