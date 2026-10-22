// Crop original PDF tables including captions. Coordinates verified on 85-DPI previews.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
const pdf = 'pdfs/loco-manipulation/egohumanoid-v2.pdf';
const dir = 'assets/figures/egohumanoid-v2';
const crops = [
  [1,8,124,93,477,229], [2,8,124,331,477,184],
  [3,9,124,334,477,123], [4,9,124,468,477,171],
  [5,17,125,93,472,172], [6,18,124,92,477,140],
  [7,18,124,236,477,267], [8,19,124,93,477,212],
  [9,20,124,92,477,114], [10,20,124,578,477,102],
  [11,21,124,147,477,135], [12,21,124,400,477,274],
];
const temp = fs.mkdtempSync(path.join(os.tmpdir(), 'egov2-tables-'));
const dpi = 400;
for (const page of new Set(crops.map(c => c[1]))) {
  execFileSync('pdftoppm', ['-r', String(dpi), '-f', String(page), '-l', String(page), '-singlefile', '-png', pdf, `${temp}/page-${page}`]);
}
for (const [n,page,x,y,w,h] of crops) {
  const px = v => String(Math.round(v*dpi/85));
  execFileSync('sips', ['--cropToHeightWidth',px(h),px(w),'--cropOffset',px(y),px(x),`${temp}/page-${page}.png`,'--out',`${dir}/table-${n}.png`]);
}
fs.writeFileSync(`${dir}/table-manifest.json`,JSON.stringify({arxiv:'2609.37181v1',pdf,dpi,previewDpi:85,tables:crops.map(([table,page,...previewCrop])=>({table,page,previewCrop,file:`table-${table}.png`,anchor:`table-${table}`}))},null,2)+'\n');
console.log('Prepared all 12 original table crops.');
