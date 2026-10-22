// Reproduce paper figure crops from the local, version-pinned PDFs (no downloads).
import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { spawnSync } from 'node:child_process';
const sources = {
  gmr: ['pdfs/loco-manipulation/gmr.pdf', '2510.02252v1', 9, '2025-10-02'],
  sonic: ['pdfs/sonic.pdf', '2511.07820v3', 37, '2026-05-21'],
  'egohumanoid-v2': ['pdfs/loco-manipulation/egohumanoid-v2.pdf', '2609.37181v1', 24, '2026-09-29'],
  koda: ['pdfs/loco-manipulation/koda.pdf', '2610.21152v1', 33, '2026-10-15'],
  'fast-wam': ['pdfs/world-model/fastwam.pdf', '2603.16666v2', 13, '2026-03-23'],
  vpp2: ['pdfs/world-model/vpp2.pdf', '2610.10270v2', 21, '2026-10-08'],
};
// Crop coordinates measured on the 85 DPI PDF previews, not hotspot coordinates.
const crops = [
  ['gmr', 4, 'fig-2', 368, 276, 293, 188, 400],
  ['gmr', 7, 'fig-3', 61, 73, 293, 410, 300],
  ['gmr', 7, 'fig-4', 61, 492, 294, 211, 400],
  ['egohumanoid-v2', 5, 'fig-3', 125, 96, 474, 315, 300],
  ['sonic', 14, 'fig-7', 70, 95, 562, 272, 300],
];
for (const [slug, page, name, x,y,w,h,dpi] of crops) {
  const dir = `assets/figures/${slug}`;
  mkdirSync(dir, {recursive:true});
  const px = n => String(Math.round(n*dpi/85));
  const r=spawnSync('pdftoppm',['-r',String(dpi),'-f',String(page),'-l',String(page),'-singlefile','-png','-x',px(x),'-y',px(y),'-W',px(w),'-H',px(h),sources[slug][0],`${dir}/${name}`],{stdio:'inherit'});
  if(r.status!==0) throw new Error(`Render failed: ${slug}/${name}`);
}
mkdirSync('assets/figures/humanoid-reading', {recursive:true});
const manifest={reviewed:'2026-10-22', scope:'Full local PDF text, references, captions and embedded appendices read. External supplementary videos not audited. No claim of latest-version coverage.', sources:Object.fromEntries(Object.entries(sources).map(([s,[path,arxiv,pages,date]])=>[s,{path,arxiv,pages,date,sha256:createHash('sha256').update(readFileSync(path)).digest('hex')}])) ,crops:crops.map(([slug,page,file,x,y,w,h,dpi])=>({slug,page,file:`${file}.png`,dpi,previewDpi:85,previewCrop:[x,y,w,h]}))};
writeFileSync('assets/figures/humanoid-reading/source-manifest.json',JSON.stringify(manifest,null,2)+'\n');
console.log('Rendered 5 original figure crops; recorded 6 source PDF hashes.');
