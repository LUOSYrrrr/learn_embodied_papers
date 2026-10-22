// Original-paper crops. Coordinates measured on 85-DPI PDF previews.
// This is PDF rendering, not a redraw of the paper's evidence.
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
const pdf='pdfs/loco-manipulation/egohumanoid-v2.pdf';
const dir='assets/figures/egohumanoid-v2';
const crops=[
  [1,1,127,275,470,291,350],
  [2,3,360,583,239,225,500],
  [3,5,125,96,474,315,300],
  [4,6,127,96,470,302,300],
  [5,7,127,98,470,245,350],
  [6,9,127,92,470,232,350],
  [7,20,127,299,470,224,350],
  [8,22,127,209,470,540,300],
  [9,23,127,209,470,540,300],
  [10,24,127,209,470,540,300],
];
fs.mkdirSync(dir,{recursive:true});
const renderDir=fs.mkdtempSync(path.join(os.tmpdir(),'egov2-render-'));
for(const [figure,page,x,y,w,h,dpi] of crops){
  const px=n=>String(Math.round(n*dpi/85));
  const fullPage=path.join(renderDir,`page-${page}`);
  // Render the entire page first: direct pdftoppm ROI rendering clips some
  // embedded-form labels in Figures 9–10 even when their coordinates fit.
  execFileSync('pdftoppm',['-r',String(dpi),'-f',String(page),'-l',String(page),'-singlefile','-png',pdf,fullPage],{stdio:'inherit'});
  execFileSync('sips',['--cropToHeightWidth',px(h),px(w),'--cropOffset',px(y),px(x),`${fullPage}.png`,'--out',`${dir}/fig-${figure}.png`],{stdio:'pipe'});
}
const manifest={
  reviewed:'2026-10-23',arxiv:'2609.37181v1',pdf,pages:24,
  sha256:createHash('sha256').update(fs.readFileSync(pdf)).digest('hex'),
  scope:'Figures 1–10: original image and caption, main text and embedded appendices. External supplementary videos not audited.',
  figures:crops.map(([figure,page,x,y,w,h,dpi])=>({figure,page,dpi,file:`fig-${figure}.png`,previewDpi:85,previewCrop:[x,y,w,h],explanationAnchor:`figure-${figure}`})),
};
fs.writeFileSync(`${dir}/figure-manifest.json`,JSON.stringify(manifest,null,2)+'\n');
console.log('Rendered and indexed all 10 EgoHumanoid-V2 figures.');
