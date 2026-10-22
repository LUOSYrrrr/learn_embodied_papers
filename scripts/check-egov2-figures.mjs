import fs from 'node:fs';
import path from 'node:path';
import {execFileSync} from 'node:child_process';

const binary=process.env.EGOV2_BROWSE_BIN;
if(!binary) throw new Error('Set EGOV2_BROWSE_BIN to the gstack browse executable.');
const browse=(...args)=>execFileSync(binary,args,{encoding:'utf8',timeout:45000}).trim();
const js=source=>JSON.parse(browse('js',`({value:(${source})})`)).value;
const file='papers/egohumanoid-v2.html';
const html=fs.readFileSync(file,'utf8');
const missingFiles=[];
for(const [,href] of html.matchAll(/(?:href|src)="([^"#?]+)(?:[?#][^"]*)?"/g)){
  if(/^[a-z]+:/i.test(href))continue;
  if(!fs.existsSync(path.resolve(path.dirname(file),href)))missingFiles.push(href);
}
browse('goto',`file://${path.resolve(file)}`);
browse('js','document.querySelectorAll("img").forEach(i=>i.loading="eager")');
const report={date:'2026-10-23',file,missingFiles,layouts:[],keyboardAnchors:[]};
for(const width of [375,768,1440]){
  browse('viewport',`${width}x1000`);
  for(const theme of ['light','dark']){
    if(js('document.documentElement.dataset.theme')!==theme)browse('click','.theme-toggle');
    report.layouts.push(js('({width:innerWidth,theme:document.documentElement.dataset.theme,scrollWidth:document.documentElement.scrollWidth})'));
  }
}
report.media=js('({figures:document.querySelectorAll(".figure-reading").length,brokenImages:[...document.images].filter(i=>!i.complete||!i.naturalWidth).map(i=>i.src),duplicateIds:[...document.querySelectorAll("[id]")].map(e=>e.id).filter((id,i,a)=>a.indexOf(id)!==i),missingAnchors:[...document.querySelectorAll("a[href^=\\"#\\"]")].map(a=>a.hash.slice(1)).filter(id=>id&&!document.getElementById(id))})');
for(let n=1;n<=10;n++){
  browse('js',`document.querySelector('.figure-index a[href="#figure-${n}"]').focus()`);
  browse('press','Enter');
  report.keyboardAnchors.push({figure:n,hash:js('location.hash')});
}
browse('js','document.querySelector(".theme-toggle").focus()');
browse('press','Enter');
report.keyboardTheme=js('document.documentElement.dataset.theme')==='light';
report.print=js('(()=>{const before=[...document.querySelectorAll("details")].map(d=>d.open);window.dispatchEvent(new Event("beforeprint"));const expanded=[...document.querySelectorAll("details")].every(d=>d.open);window.dispatchEvent(new Event("afterprint"));return {expanded,restored:JSON.stringify(before)===JSON.stringify([...document.querySelectorAll("details")].map(d=>d.open))}})()');
report.passed=!missingFiles.length&&report.layouts.every(v=>v.width>=v.scrollWidth)&&report.media.figures===10&&!report.media.brokenImages.length&&!report.media.duplicateIds.length&&!report.media.missingAnchors.length&&report.keyboardAnchors.every(v=>v.hash===`#figure-${v.figure}`)&&report.keyboardTheme&&report.print.expanded&&report.print.restored;
fs.writeFileSync('assets/figures/egohumanoid-v2/validation.json',JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
if(!report.passed)process.exitCode=1;
