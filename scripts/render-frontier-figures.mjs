import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
import {createHash} from 'node:crypto';
const slug=process.argv[2];
if(!slug||!/^[a-z0-9-]+$/.test(slug))throw Error('Provide a paper slug');
const meta=JSON.parse(fs.readFileSync(`content/wam-frontier-20261023/${slug}.json`,'utf8'));
const dir=`assets/figures/${slug}`;
fs.mkdirSync(dir,{recursive:true});
const tmp=fs.mkdtempSync(path.join(os.tmpdir(),`${slug}-render-`));
for(const fig of meta.figures.filter(f=>f.crop)){
 const dpi=fig.dpi||Math.max(350,25*Math.ceil(800*(meta.previewDpi||85)/Math.min(...fig.crop.slice(2))/25)), full=path.join(tmp,`p-${fig.page}-${dpi}`);
 fig.dpi=dpi;
 if(!fs.existsSync(`${full}.png`))execFileSync('pdftoppm',['-r',String(dpi),'-f',String(fig.page),'-l',String(fig.page),'-singlefile','-png',meta.pdf,full],{stdio:'pipe'});
 const [x,y,w,h]=fig.crop.map(n=>String(Math.round(n*dpi/(meta.previewDpi||85))));
 execFileSync('sips',['--cropToHeightWidth',h,w,'--cropOffset',y,x,`${full}.png`,'--out',`${dir}/fig-${fig.n}.png`],{stdio:'pipe'});
}
fs.writeFileSync(`${dir}/source-manifest.json`,JSON.stringify({source:meta.source,pdf:meta.pdf,sha256:createHash('sha256').update(fs.readFileSync(meta.pdf)).digest('hex'),reviewed:'2026-10-23',previewDpi:meta.previewDpi||85,figures:meta.figures},null,2)+'\n');
console.log(`Rendered ${meta.figures.filter(f=>f.crop).length} original figures for ${slug}`);
