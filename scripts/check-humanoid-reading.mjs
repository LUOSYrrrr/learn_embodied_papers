import fs from 'node:fs';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
const slugs=['humanoid-data-to-wam','gmr','sonic','egohumanoid-v2','koda','fast-wam','vpp2'];
const files=['index.html',...slugs.map(s=>`papers/${s}.html`)];
const problems=[];
for(const file of files){
  const html=fs.readFileSync(file,'utf8').replace(/<script\b[\s\S]*?<\/script>/g,'');
  const ids=[...html.matchAll(/(?<![\w-])id="([^"]+)"/g)].map(m=>m[1]);
  for(const id of new Set(ids))if(ids.filter(v=>v===id).length>1)problems.push({file,kind:'duplicate-id',id});
  for(const m of html.matchAll(/(?:href|src)="([^"?#]*)(?:\?[^"#]*)?(?:#([^"]*))?"/g)){
    const [url,hash]=m.slice(1);if(/^(https?:|data:|javascript:|mailto:)/.test(url))continue;
    const target=url?path.resolve(path.dirname(file),decodeURI(url)):path.resolve(file);
    if(!fs.existsSync(target)){problems.push({file,kind:'missing-path',url});continue;}
    if(hash&&target.endsWith('.html')&&!fs.readFileSync(target,'utf8').includes(`id="${hash}"`))problems.push({file,kind:'missing-anchor',url,hash});
  }
}
const report={date:'2026-10-23',pages:files,staticProblems:problems,browser:[]};
const binary=process.env.HUMANOID_BROWSE_BIN;
if(binary){
  const browse=(...args)=>execFileSync(binary,args,{encoding:'utf8',timeout:45000});
  for(const slug of slugs){
    browse('goto',`file://${path.resolve('papers',slug+'.html')}`);
    browse('js',`document.querySelectorAll('img').forEach(i=>i.loading='eager')`);
    const widths=[];
    for(const width of [375,768,1440]){
      browse('viewport',`${width}x900`);
      widths.push(JSON.parse(browse('js','({width:innerWidth,scrollWidth:document.documentElement.scrollWidth})')));
    }
    const media=JSON.parse(browse('js',`({brokenImages:[...document.images].filter(i=>!i.complete||!i.naturalWidth).map(i=>i.getAttribute('src')),duplicateIds:[...document.querySelectorAll('[id]')].map(e=>e.id).filter((id,i,a)=>a.indexOf(id)!==i),missingAnchors:[...document.querySelectorAll('a[href^="#"]')].map(a=>a.hash.slice(1)).filter(id=>id&&!document.getElementById(id))})`));
    report.browser.push({slug,...media,widths});
  }
}
fs.writeFileSync('assets/figures/humanoid-reading/validation.json',JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(report,null,2));
if(problems.length||report.browser.some(p=>p.brokenImages.length||p.duplicateIds.length||p.missingAnchors.length||p.widths.some(w=>w.scrollWidth>w.width)))process.exitCode=1;
