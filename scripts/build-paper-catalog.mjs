import fs from 'node:fs';
import path from 'node:path';

const walk = dir => fs.readdirSync(dir, {withFileTypes: true}).flatMap(entry =>
  entry.isDirectory() ? walk(path.join(dir, entry.name)) : [path.join(dir, entry.name)]);
const escape = value => value.replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;').replaceAll('"', '&quot;');
const decode = value => value.replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"');
const pages = walk('papers').filter(file => file.endsWith('.html') && path.basename(file) !== '_template.html').map(file => {
  const html = fs.readFileSync(file, 'utf8');
  const title = decode(html.match(/<title>([\s\S]*?)<\/title>/i)?.[1]?.trim() || path.basename(file, '.html'));
  return {file, title};
}).sort((a, b) => a.title.localeCompare(b.title, 'zh-CN', {numeric: true}));
const block = `<!-- PAPER-CATALOG:START -->
    <section class="paper-catalog" id="all-readings" aria-labelledby="all-readings-title">
      <div class="hero-tag">// COMPLETE READING INDEX</div>
      <h2 id="all-readings-title">全部 ${pages.length} 个解读页面</h2>
      <p>包括论文精读、专题路线、源码与数据分析；不把页面数量等同于论文数量或精读完成度。上方分类导航保留，完整入口以这里为准。</p>
      <label for="paper-catalog-search">按论文名、关键词或文件名搜索</label>
      <input id="paper-catalog-search" type="search" placeholder="例如 SONIC、EgoHumanoid、WAM、RL" autocomplete="off" aria-controls="paper-catalog-list">
      <p class="catalog-count" id="paper-catalog-count" role="status" aria-live="polite">显示 ${pages.length} / ${pages.length} 个页面</p>
      <ul id="paper-catalog-list">
${pages.map(page => `        <li><a href="${escape(page.file)}"><span>${escape(page.title)}</span><small>${escape(page.file)}</small></a></li>`).join('\n')}
      </ul>
      <p id="paper-catalog-empty" hidden>没有匹配页面。试试英文简称，或清空搜索。</p>
      <noscript><p>搜索需要 JavaScript；全部页面链接已完整显示，可使用浏览器的页面查找。</p></noscript>
    </section>
    <!-- PAPER-CATALOG:END -->`;
let index = fs.readFileSync('index.html', 'utf8');
const pattern = /<!-- PAPER-CATALOG:START -->[\s\S]*?<!-- PAPER-CATALOG:END -->/;
if (pattern.test(index)) index = index.replace(pattern, block);
else index = index.replace('    <div id="about"', `${block}\n\n    <div id="about"`);
index = index.replace(/<div class="intro-cell-num">\d+<\/div>\s*<div class="intro-cell-label">(?:已精读|解读页面)<\/div>/,
  `<div class="intro-cell-num">${pages.length}</div>\n        <div class="intro-cell-label">解读页面</div>`);
fs.writeFileSync('index.html', index);
console.log(`Indexed ${pages.length} pages; all links are static HTML (no JavaScript required).`);
