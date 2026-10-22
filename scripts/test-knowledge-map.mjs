import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const pagePath = path.join(root, 'papers/embodied-knowledge-map.html');
const html = fs.readFileSync(pagePath, 'utf8');
const manifest = JSON.parse(fs.readFileSync(path.join(root, 'assets/diagrams/knowledge-map-manifest.json'), 'utf8'));
const xml = fs.readFileSync(path.join(root, 'assets/diagrams/embodied-knowledge-map.drawio'), 'utf8');
const slugs = manifest.groups.flatMap(g => g.papers.map(p => p.slug));
assert.equal(new Set(slugs).size, manifest.noteCount, 'Unique primary assignments');
assert.equal((html.match(/data-note=/g) || []).length, manifest.noteCount, 'All notes linked');
assert(!html.includes('{{NOTE_COUNT}}') && !html.includes('<!-- MAP_SVG -->'), 'Template fully expanded');

let localLinks = 0;
for (const [, href] of html.matchAll(/\bhref="([^"]+)"/g)) {
  if (/^(https?:|mailto:|data:)/.test(href)) continue;
  const [relative, fragment] = href.split('#');
  const target = relative ? path.resolve(path.dirname(pagePath), relative) : pagePath;
  assert(fs.existsSync(target), `Missing link: ${href}`);
  if (fragment && target.endsWith('.html')) {
    const content = target === pagePath ? html : fs.readFileSync(target, 'utf8');
    assert(content.includes(`id="${fragment}"`) || content.includes(`id='${fragment}'`), `Missing anchor: ${href}`);
  }
  localLinks++;
}

const attrs = text => Object.fromEntries([...text.matchAll(/([\w-]+)="([^"]*)"/g)].map(m => [m[1], m[2]]));
const cells = new Map();
for (const match of xml.matchAll(/<mxCell\s+([^>]*?)(?:\/>|>([\s\S]*?)<\/mxCell>)/g)) {
  const a = attrs(match[1]);
  assert(!cells.has(a.id), `Duplicate cell: ${a.id}`);
  cells.set(a.id, { ...a, body: match[2] || '' });
}
let nestedCells = 0;
for (const cell of cells.values()) {
  if (cell.id === '0') continue;
  assert(cells.has(cell.parent), `Missing parent for ${cell.id}`);
  if (cell.edge === '1') {
    assert(/<mxGeometry[^>]*relative="1"[^>]*as="geometry"/.test(cell.body), `Edge geometry: ${cell.id}`);
  }
  if (cell.vertex !== '1') continue;
  const g = attrs(cell.body.match(/<mxGeometry\s+([^>]+)/)?.[1] || '');
  assert(Number(g.width) > 0 && Number(g.height) > 0, `Dimensions: ${cell.id}`);
  if (cell.parent === '1') continue;
  const parent = cells.get(cell.parent);
  const pg = attrs(parent.body.match(/<mxGeometry\s+([^>]+)/)?.[1] || '');
  assert(Number(g.x) >= 0 && Number(g.y) >= 0, `Negative child position: ${cell.id}`);
  assert(Number(g.x) + Number(g.width) <= Number(pg.width), `Child exceeds parent width: ${cell.id}`);
  assert(Number(g.y) + Number(g.height) <= Number(pg.height), `Child exceeds parent height: ${cell.id}`);
  nestedCells++;
}
console.log(JSON.stringify({ result: 'PASS', notes: manifest.noteCount, groups: manifest.groups.length, localLinks, drawioCells: cells.size, nestedCells }, null, 2));
