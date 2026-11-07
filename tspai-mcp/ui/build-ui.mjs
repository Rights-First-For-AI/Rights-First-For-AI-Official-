import { build } from "esbuild";
import { readFile, writeFile } from "node:fs/promises";
import { fileURLToPath } from "node:url";
const target = new URL("../bridge_chunked_widget.html", import.meta.url);
const result = await build({
  entryPoints: [fileURLToPath(new URL("./mcp-bootstrap.js", import.meta.url))],
  bundle: true, format: "iife", target: "es2020", minify: true,
  legalComments: "inline", write: false
});
const html = await readFile(target, "utf8");
const marker = /<script data-tspai-mcp-sdk>[\s\S]*?<\/script>/g;
if ([...html.matchAll(marker)].length !== 1) throw new Error("Expected exactly one SDK bundle marker");
const bundle = result.outputFiles[0].text.replaceAll("</script", "<\\/script");
await writeFile(target, html.replace(marker, () => "<script data-tspai-mcp-sdk>" + bundle + "</script>"), "utf8");
console.log("Rebuilt inline MCP Apps SDK. Regenerate release checksums before packaging.");
