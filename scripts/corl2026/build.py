"""Render source-grounded notes and portable HTML; no network dependencies.

Uses PyMuPDF + markdown-it-py. Source: notes/corl2026/reading/*.md.
Does not edit existing paper pages or shared theme assets.
"""
import base64, html, json, math, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
# The local ARM Python can use already-installed uv packages without installation.
cache = pathlib.Path('/Users/siyuanluo/.cache/uv/archive-v0')
if cache.exists():
    for p in cache.iterdir():
        if any((p / x).exists() for x in ['pymupdf', 'markdown_it', 'mdurl']):
            sys.path.insert(0, str(p))
import pymupdf
from markdown_it import MarkdownIt

COLLECTION = 'https://app.notion.com/p/41bbb2b96e9d816ba5c7c52aa669dc53'
TEMPLATE = 'https://app.notion.com/p/419bb2b96e9d818db8a0c35a6b165e6e'
SITE = 'https://www.siyuanluoembodied.xin'
DATA = [
 dict(slug='wb-wam',name='WB-WAM',tag='异构数据 · 物理动作',venue='TAG Workshop（沿用既有核验）',
  source='https://arxiv.org/abs/2609.34199v3',pdf='https://arxiv.org/pdf/2609.34199v3',
  brief='身体、根部与双手共享 72D 物理动作；任务对齐的人类中训帮助少样本迁移。',
  warning='73.75% 含额外人类数据；84% 主实验未用 PICO。',
  eval=['HumanoidArena 七任务均值 81.9%。','未见对象/场景缺少分层次数，不能算严格 OOD 下降。','五任务各 20 次，均值 84%；擦桌弱于 OpenWAM。'],
  steps=['异构预训练：按身体/手/视频的可用标签组织监督。','PICO 中训：GMR、约束 IK、手部重建对齐到机器人。','真机后训：各任务独立策略，加 FK 几何损失。','部署：身体经 SONIC，手部直接执行；不强制生成未来视频。'],
  quiz=['“机器人示范少 70%”可以推出什么？',['机器人示范数变少，同时额外用了任务对齐的人类数据。','总数据和总计算量都减少了 70%。','目标任务没有在任何训练阶段出现。'],'0','Table III 比较的是机器人示范量；PICO 有额外 22 小时数据与中训，且覆盖目标任务。']),
 dict(slug='long-wam',name='Long-WAM',tag='时间上下文 · 未来 latent',venue='主题关联阅读 · 录用归属待核实',
  source='https://arxiv.org/abs/2610.10528v1',pdf='https://arxiv.org/pdf/2610.10528v1',
  brief='机器人自回归视频先验，把长历史与部分未来 latent 接给动作专家。',
  warning='更长未必更好；最快时延与最高成功率来自不同配置。',
  eval=['LIBERO 均值 99.5%；RoboTwin 94.4%。','RoboCasa 未见组合 6.1%，加规划器 35%；额外预算需计入。','动态杯抓取 18–20/20；YAM 三任务各 16/20、16/20、17/20。'],
  steps=['先继续训练机器人自回归视频，学习过去到未来。','视频训练后，动作专家读取停止梯度的缓存。','测试只将未来 latent 部分去噪，不解码 RGB。','异步准备下个动作块，检查计算是否赶得上执行窗口。'],
  quiz=['可以把 81.8 ms 和 94.4% 写成同一个部署结果吗？',['可以，它们都出现在论文中。','不可以：81.8 ms 对应 V2/A2、92.5% SR。','不可以，因为模型没有进行真机实验。'],'1','Table 6 的最快配置减少视频和动作去噪步数；基础 94.4% 与 356 ms 同行。']),
 dict(slug='pantact',name='PanTact',tag='人类示范 · 接触接口',venue='Contact-Rich Workshop · Spotlight',
  source='https://contact-rich-loco-manipulation.github.io/papers/28-pantact.pdf',
  brief='采集身体接触，预测末端与接触目标，由控制器选择机器人表面。',
  warning='90.63% 含阶段部分得分；机器人端没有新增身体触觉闭环。',
  eval=['参考回放测跟踪误差；未给完整视觉任务仿真 SR。','扫物有见过/未见对象，但未分层报告成功率。','抓抱 17/20；搬箱推箱 WBIK 9/10、稀疏控制 6/10。'],
  steps=['人类采集：相机、追踪器和身体 FSR 接触贴片。','统一左夹爪参考系，屏蔽人体视觉区域。','策略预测两手、头部和 active 接触位置。','机器人选择合适身体表面，经 IK/SONIC 或稀疏 RL 执行。'],
  quiz=['扫物入柜的 90.63% 应如何解释？',['约 14.5 次完整成功，可以四舍五入为 15 次。','16 次实验的部分得分平均，不可换算二项成功数。','机器人用力传感反馈达到 90.63% 精度。'],'1','附录给扫物比例、关柜部分得分及最终乘积；没有完整成功计数，不能计算二项 Wilson 区间。']),
 dict(slug='workhorse',name='Workhorse',tag='五点参考 · 闭环偏差',venue='Contact-Rich Workshop · Spotlight',
  source='https://contact-rich-loco-manipulation.github.io/papers/30-workhorse.pdf',
  brief='五点人类轨迹加视觉规划，训练规划器和控制器容忍执行偏差。',
  warning='77%/64% 是仿真；五点接口成功更多，也可能跌倒更多。',
  eval=['三箱任务：无推 77/100，有推 64/100。','同任务受推下降 13 点；H2 需重训，不是零样本。','搬箱、接箱、14 kg 行李能力展示；未报告成组 SR。'],
  steps=['用五个 tracker 采集躯干、双腕、双脚与胸前视觉。','将人体视觉编辑成目标机器人，固定变换对齐五点。','5 Hz 规划器输出 1.16 秒五点参考。','50 Hz 控制器追踪；命令/历史增强处理执行失配。'],
  quiz=['哪项结论得到这份 PDF 的直接支持？',['真机三箱任务在 40 N 推力下成功率 64%。','H2 可以不用重新训练直接执行 G1 策略。','仿真中五点接口提高任务成功率，但受推跌倒也更多。'],'2','App.D 的仿真数据：五点 64 次成功/15 次跌倒；关节接口 42 次成功/4 次跌倒，每组 100 次。']),
 dict(slug='dataset-free-compliant',name='OCLO',tag='在线姿态 · 顺应控制',venue='Contact-Rich Workshop · Spotlight',
  source='https://contact-rich-loco-manipulation.github.io/papers/11-dataset-free-compliant-humanoid-loco-manipulation.pdf',
  brief='程序课程训练下肢，根据手目标在线生成身体姿态，接上顺应参考与 IK。',
  warning='无人体示范仍有仿真训练；真机任务主要由人遥操作。',
  eval=['Track prior 82.2%，加 CEM 77.8%；朝向误差同时改善。','扰动训练与评测有关联；没有严格分层对象 OOD。','每条件 10 次受力测试；九任务演示未给独立 SR。'],
  steps=['程序命令课程训练 15 关节下肢策略。','用外力估计更新顺应末端参考。','几何 prior 生成高度/pitch/roll；可选 CEM 用冻结策略细化。','手臂 IK 200 Hz、下肢 50 Hz 执行，遥操作提供手目标。'],
  quiz=['为什么不能说 CEM 全面优于解析 prior？',['因为 CEM 完全没有真实机器人部署。','因为它改善 Track 朝向误差，却降低了同任务成功率。','因为 prior 需要更多人体示范。'],'1','Table I：朝向误差 17.6°→11.5°，成功率 82.2%→77.8%；指标与代价应一起汇报。']),
 dict(slug='hulk',name='HULK',tag='负载物理 · 教师蒸馏',venue='Contact-Rich Workshop · Spotlight',
  source='https://contact-rich-loco-manipulation.github.io/papers/15-hulk.pdf',
  brief='力感知 MPC 与 CP-CBF 指导特权教师，蒸馏为只用本体状态的学生。',
  warning='300 kg 是滚轮车质量；5/6 来自 150 kg 的另一组固定负载测试。',
  eval=['仿真教师最大抗推：MPC 110 N，加入 CP-CBF 130 N。','从腕力到前臂负载有有限迁移，未见物体分层不足。','固定载荷四任务 5/6、4/4、4/4、4/4；小样本区间很宽。'],
  steps=['腕部受力教师：人体静态上肢目标与持续外力课程。','整物体教师：从已建立的抓握学习负载支撑。','MPC/CP-CBF 参与教师训练并提供物理目标。','DAgger 蒸馏到本体状态学生；部署不运行在线 CBF 滤波。'],
  quiz=['“300 kg、5/6”应该怎样写？',['在 300 kg 载荷下完整成功 5/6。','举起 300 kg，成功率约 83%。','150 kg 滚轮车固定测试成功 5/6；最大滚动质量另测 300 kg。'],'2','Table II 将 Succ 与 Max 分列；把它们拼接会制造不存在的实验。'])
]

DATA.extend(json.loads((ROOT/'scripts/corl2026/focus-papers.json').read_text()))
DATA.extend(json.loads((ROOT/'scripts/corl2026/workshop-papers.json').read_text()))
publication_path = ROOT/'notes/corl2026/notion-publication.json'
if publication_path.exists():
    for d in DATA:
        pid=json.loads(publication_path.read_text()).get('papers',{}).get(d['slug'])
        if pid: d['notion']='https://app.notion.com/p/'+pid

CROPS = [
 ('wb-wam',3,(48,43,566,396),'2',300),
 ('long-wam',1,(49,377,548,763),'1',300),
 ('pantact',3,(47,44,566,197),'3',400),
 ('pantact',4,(309,46,566,221),'5',400),
 ('workhorse',2,(48,44,566,164),'2',500),
 ('dataset-free-compliant',3,(47,44,566,266),'2',300),
 ('hulk',2,(49,43,567,316),'1',300),
 ('ecomem',2,(147,67,455,214),'1',400),
 ('ecomem',4,(125,158,487,340),'3',400),
 ('memjepa',2,(127,264,484,420),'2',400),
 ('simple-agentic-memory',2,(108,69,503,263),'1',300),
 ('simple-agentic-memory',25,(108,257,504,458),'6',350),
 ('embodiedswe',2,(106,49,506,261),'1',300),
 ('embodiedswe',7,(108,73,504,352),'7',300),
 ('embodiedswe',9,(108,61,503,187),'10',500),
 ('roshi',4,(49,48,564,299),'2',300),
 ('forca',2,(48,47,566,205),'1',400),
 ('blind-dexterity',6,(49,48,566,287),'5',300),
 ('gated-memory',4,(107,47,505,168),'3',500),
 ('gated-memory',7,(108,194,504,293),'11',600),
 ('batch',3,(109,364,504,582),'2',400),
 ('batch',9,(109,67,504,254),'4',400),
 ('card',4,(58,71,554,278),'2',400),
 ('card',5,(318,294,553,389),'5',650)
]

def wilson(k,n):
    z=1.95996398454; p=k/n
    center=(p+z*z/(2*n))/(1+z*z/n)
    d=z*math.sqrt(p*(1-p)/n+z*z/(4*n*n))/(1+z*z/n)
    return f'{100*p:.1f}%（{100*(center-d):.1f}–{100*(center+d):.1f}%）'

def preprocess(text):
    return re.sub(r'\{\{ci:(\d+)/(\d+)\}\}',lambda m:wilson(int(m[1]),int(m[2])),text)

md=MarkdownIt('commonmark',{'html':True}).enable('table')
CSS=(ROOT/'scripts/corl2026/style.css').read_text()
JS=(ROOT/'scripts/corl2026/interactive.js').read_text()

def shell(title,content,sidebar='',portable=False):
    back=COLLECTION if portable else 'corl2026.html'
    home=SITE+'/' if portable else '../index.html'
    workshops=SITE+'/papers/corl2026-workshops.html' if portable else 'corl2026-workshops.html'
    theme_init="try{document.documentElement.dataset.theme=localStorage.getItem('theme')||localStorage.getItem('corl2026-theme')||'light'}catch{}"
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="color-scheme" content="light dark"><title>{html.escape(title)} · CoRL 阅读室</title><script>{theme_init}</script><style>{CSS}</style></head><body><a class="skip" href="#main">跳到正文</a><header class="top"><a href="{home}" class="brand">~/paper-notes <span>CoRL 2026</span></a><nav aria-label="阅读导航与工具"><a class="collection-link" href="{back}">专题</a><a href="{workshops}">Workshop 选题</a><button id="theme" type="button" aria-label="切换深浅主题" hidden>切换主题</button><button id="print" type="button" hidden>打印 / PDF</button></nav></header><div class="layout">{sidebar}<main id="main">{content}</main></div><footer>原文事实与阅读者推断分开标注 · 整理日期 2026-11-17 · <a href="{home}">返回论文网站</a> · <a href="{workshops}">继续选题</a></footer><script>{JS}</script></body></html>'''

def render_paper(d, portable=False):
    raw=preprocess((ROOT/f'notes/corl2026/reading/{d["slug"]}.md').read_text())
    body=md.render(raw)
    title=re.search(r'<h1>(.*?)</h1>',body)[1]
    body=re.sub(r'<h1>.*?</h1>','',body,count=1)
    headings=[]
    def head(m):
        i=f'section-{len(headings)+1}'; headings.append((i,m[1])); return f'<h2 id="{i}">{m[1]}</h2>'
    body=re.sub(r'<h2>(.*?)</h2>',head,body)
    # Reuse the skill's reading/evidence roles without changing the source prose.
    body=re.sub(r'(<h2 id="section-[1-5]"[^>]*>[^<]*</h2>)\s*<p>(?!<img\b)(.*?)</p>',
                r'\1<div class="cn-read"><div class="cn-label">这一节解决什么</div><p>\2</p></div>',body,flags=re.S)
    bridges={
      'wb-wam':{3:'有了共享动作语义，下一步要追踪标签怎样进入训练：先看异构监督，再看人类数据对齐，最后看机器人后训练与执行。这样才能区分数据表示的贡献与额外数据的贡献；跨任务泛化仍要由后面的实验确认。',4:'前面的流程能处理多类数据，但是否有效要回到各自的实验配置。下面把主实验、人类数据中训和动作表示消融分开；84% 与 73.75% 不能拼成同一配置的结果。'},
      'long-wam':{3:'历史有用仍不等于策略能直接使用它。下面区分视频预训练、动作专家读取缓存、未来 latent 部分去噪与异步执行；未来特征与真实未来图像不是同一种输入。',4:'历史、未来特征和异步执行各自解决不同问题。下面分别检查时间上下文、预测预算与系统时延的证据；最快配置并不同时拥有最高成功率。'},
      'pantact':{3:'接触目标能描述身体与物体的关系，仍需解释怎样采到、怎样表示、怎样由机器人实现。下面沿这条信息链拆开接口；人类采集时有触觉，不意味着机器人部署时有同样的触觉反馈。',4:'方法区分了接触意图与具体控制器，实验也必须分别核对。下面分仿真回放、对象变化和真机任务讨论；部分得分不能替代完整成功率。'},
      'workhorse':{3:'五点参考为身体留下自由度，却也会带来计划与执行的偏差。下面沿采集、视觉规划、控制训练与闭环执行解释增强在哪里起作用；真机可靠性还不能由接口设计直接推出。',4:'增强训练是否让系统更稳，要同时看成功与跌倒。下面分开仿真受推、跨本体适配和真机展示；高成功率并不保证所有失败类型都减少。'},
      'dataset-free-compliant':{3:'姿态可达与受力顺应需要在同一控制链上配合。下面从手目标、顺应参考、姿态选择走到下肢与手臂执行；这里提供的是控制能力，不是视觉任务决策。',4:'在线选姿态的收益可能体现在误差，也可能体现在成功率，两者不能互相替代。下面分别检查仿真任务、扰动条件与真机遥操作；CEM 的效果需和额外计算一起看。'},
      'hulk':{3:'物理规划只给出训练目标，还需要教师把目标变成动作，再让学生在实际可用观测下执行。下面追踪这三层的输入与损失；部署时没有在线 CBF 过滤的保护。',4:'前面的教师与学生使用不同信息，不能共用一套性能叙述。下面把仿真抗推、固定负载成功次数和最大负载扫描拆开，避免将 300 kg 与另一条件的 5/6 拼接。'},
      'ecomem':{3:'共享概念词汇还不能直接驱动动作。下面看 Writer 怎样把一次完整事件写入记录，Reader 怎样编码，策略又何时重新观察；固定 Writer 不等于整套系统免训练。'},
      'memjepa':{3:'遮住输入的训练目标确定以后，还要保证规划中的想象不会污染真实记忆。下面分开真实状态更新和候选动作的分支 rollout；循环隐状态的存在并不能保证它在所有遮挡下都可靠。'},
      'simple-agentic-memory':{3:'身份可以来自历史，位置却可能已经改变。下面追踪指令编译、工具写入、条件读取和当前画面重定位；新增层冻结权重，不代表底层模型从未训练。'},
      'embodiedswe':{3:'找到可运行程序只是起点，验证器和数据生成器还要限制它怎样影响训练。下面沿求解、验证、扩增到视觉策略的路径检查信息权限；能读完整仿真状态的老师不能与只看图像的学生混为一谈。'}
    }
    for number,guide in bridges.get(d['slug'],{}).items():
        pattern=rf'(<h2 id="section-{number}"[^>]*>.*?</h2>)(?!\s*<div class="cn-read")'
        body=re.sub(pattern,lambda m:m[1]+f'<div class="cn-read"><div class="cn-label">这一节解决什么</div><p>{guide}</p></div>',body,count=1)
    body=body.replace('<blockquote>','<blockquote class="core-insight">',1)
    body=re.sub(r'<table>', '<div class="eval-table-wrap" tabindex="0" role="region" aria-label="证据表，可横向滚动"><table class="eval-table">',body).replace('</table>','</table></div>')
    body=body.replace('<img ', '<img loading="lazy" decoding="async" ')
    # Source notes live two directories below root; generated pages live in papers/.
    body=body.replace('../../../assets/','../assets/')
    def figure(m):
        src=re.search(r'src="([^"]+)"',m[1])[1]
        return f'<figure><a href="{src}" target="_blank" rel="noopener">{m[1]}</a><figcaption>{m[2]} · 点击查看原尺寸</figcaption></figure>'
    body=re.sub(r'<p>(<img [^>]+alt="([^"]*)"[^>]*>)</p>',figure,body)
    body=re.sub(r'<p>(\[推断[^<]*?)(</p>)',r'<p class="inference evidence-note" data-evidence="inference">\1\2',body)
    for term,desc in [('Flow matching','学习噪声到数据的连续速度场；噪声时间不同于机器人执行时间。'),('DAgger','在学生实际访问的状态上查询教师，减少只学教师轨迹带来的分布差。')]:
        body=body.replace(term,f'<abbr title="{desc}">{term}</abbr>',1)
    # Show all stages without JavaScript; navigation only highlights a selected one.
    steps=''.join(f'<li data-step="{i}"><span class="step-no">0{i+1}</span>{html.escape(s)}</li>' for i,s in enumerate(d['steps']))
    walker=f'<section class="walker" aria-label="训练到执行逐步读"><h2 id="walk">训练到执行：逐步读</h2><p>按顺序检查信息怎样流动；每一步都保留在页面中。按钮或左右方向键切换，Home / End 跳到首尾。</p><div class="step-controls" tabindex="0" role="group" aria-label="步骤导航" hidden><button data-prev type="button">上一步</button><output aria-live="polite">1 / 4</output><button data-next type="button">下一步</button></div><ol>{steps}</ol></section>'
    question,options,correct,explain=d['quiz']
    quiz=f'<section class="quiz" data-answer="{correct}"><h2 id="quiz">理解检查</h2><fieldset><legend>{question}</legend>'+''.join(f'<label><input type="radio" name="answer" value="{i}"> {html.escape(x)}</label>' for i,x in enumerate(options))+f'</fieldset><button data-check type="button" hidden>检查答案</button><p class="feedback" aria-live="polite"></p><details><summary>展开答案与依据</summary><p>{html.escape(options[int(correct)])}</p><p>{explain}</p></details></section>'
    overview='<section class="eval-overview" aria-label="评测结论总览">'+''.join(f'<article class="eval-card"><span>{label}</span><p>{s}</p></article>' for label,s in zip(['仿真','ID / OOD','真机','证据边界'],d['eval']+[d['warning']]))+'</section>'
    # Keep the opening summary before the three evaluation cards.
    at=body.index('</blockquote>')+len('</blockquote>')
    body=body[:at]+overview+body[at:]
    insertion=body.find('<h2 id="section-4"')
    body=body[:insertion]+walker+body[insertion:] if insertion!=-1 else body+walker
    links=''.join(f'<a href="#{i}">{txt}</a>' for i,txt in headings)
    side=f'<aside class="sidebar"><details open><summary>{d["name"]} · 章节</summary><nav aria-label="章节导航"><a href="#overview">简短说明与评测</a>{links}<a href="#walk">训练到执行</a><a href="#quiz">理解检查</a></nav></details><p class="side-note">原文 / 推断 / 待验证<br>PDF 全文与附录核读<br>不以演示替代成功率</p></aside>'
    collection_link=COLLECTION if portable else 'corl2026.html'
    content=f'<div class="eyebrow">{d["venue"]}</div><h1 id="overview">{title}</h1><p class="tagline">{d["tag"]}</p><div class="source-links"><a href="{d["source"]}">原始论文 ↗</a><a href="{d.get("pdf",d["source"])}">PDF ↗</a><a href="{collection_link}">CoRL 五方向专题</a></div><article class="paper-body">{body}</article>{quiz}'
    if portable:
        def embed(m):
            path=ROOT/m[0].removeprefix('../')
            if d['slug']=='embodiedswe':
                # Preserve full-resolution PNG crops on the site; use high-quality
                # JPEG copies inside the photo-heavy portable document only.
                data=pymupdf.Pixmap(str(path)).tobytes('jpeg',jpg_quality=92)
                return 'data:image/jpeg;base64,'+base64.b64encode(data).decode()
            return 'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()
        content=re.sub(r'\.\./assets/[^" >]+\.png',embed,content)
        content=content.replace('target="_blank" rel="noopener"','download="paper-figure.png"')
        content=content.replace('点击查看原尺寸','点击查看原尺寸（无脚本时下载）')
        if d['slug']=='embodiedswe': content=content.replace('download="paper-figure.png"','download="paper-figure.jpg"')
    return shell(d['name'],content,side,portable)

def build_collection(portable=False):
    cards=''
    for i,d in enumerate(DATA):
        href=d.get('notion',COLLECTION) if portable else f'corl2026-{d["slug"]}.html'
        cards+=f'<article class="paper-card"><span class="card-num">{i+1:02}</span><div class="eyebrow">{d["venue"]}</div><h2><a href="{href}">{d["name"]} ↗</a></h2><p>{d["brief"]}</p><p class="boundary">{d["warning"]}</p><small>{d["tag"]} · 全文核读完成</small></article>'
    catalog='https://www.corl.org/program/accepted-papers' if portable else 'corl2026-catalog.html'
    content=f'''<div class="eyebrow">NOTES ON EMBODIED INTELLIGENCE / 2026.11</div><h1>CoRL 阅读室<br><span class="muted">世界模型、Agentic、Memory<br>人形与接触控制</span></h1><p class="lede">每篇先用一小段讲明白，再沿着问题、思路、方法、实验、后续实验展开。按<a href="{TEMPLATE}">五块证据链模板</a>保留原图和评测边界。</p><div class="stats"><div><strong>{len(DATA)}</strong>本专题全文核读与 HTML</div><div><strong>687</strong>主会论文仅建目录</div><div><strong>01</strong>既有 AW-0 精读接入</div></div><aside class="scope"><strong>这批覆盖哪里？</strong><p>覆盖用户指定的五个重点方向：已有十篇之外，本轮完成 H2R 的 BATCH、RoSHI、CARD，Learn@Deploy 的 FORCA、Gated Memory Policy，以及 Beneath the Policy 的 Blind Dexterity。Memory 三篇来自官方 Workshop；EmbodiedSWE 为 Agentic Workshop Best Paper。四篇接触论文为 Workshop Spotlight；WB-WAM 的 TAG Workshop 身份沿用既有核验，本次未复核；Long-WAM 为主题关联阅读，录用归属待核实。主会目录的 687 篇尚未逐篇精读。</p><a href="{catalog}">打开主会 687 篇可检索目录 →</a></aside><section><h2>一条可以串起来的阅读路线</h2><p>先用 WB-WAM 理解异构监督，再用 Long-WAM 理解时间。接下来，PanTact 选择“接触什么”，Workhorse 处理“跟不上计划”，OCLO 在线调整姿态，HULK 学会负载下的物理支撑。接口相邻，实验协议并不相同。新补的三篇记忆论文对照显式记录、隐状态与结构化读取；EmbodiedSWE 则把编码 Agent 变成离线数据老师。</p></section><section class="scope"><h2>Agentic 与 WAM 的交叉：AW-0</h2><p>沿用既有完整精读，本次只核验 Agentic Workshop Best Paper 归属。默认代码作为生成条件；hybrid 才执行技能，真机 71.1 为阶段分数。</p><p><a href="https://www.siyuanluoembodied.xin/papers/agentic-wam.html">已有 HTML 精读 →</a> · <a href="https://app.notion.com/p/419bb2b96e9d81249316ce9097d31d58">已有 Notion 正文 →</a></p></section><div class="cards">{cards}</div><section><h2>读结果时，检查这四件事</h2><div class="principles"><p><strong>数据账本</strong><br>人类示范、机器人示范、预训练与更新步数一起看。</p><p><strong>训练 / 部署</strong><br>未来视频、力输入、MPC 或教师，哪些在部署时仍然存在？</p><p><strong>同一协议</strong><br>仿真、真机、最大负载、固定负载成功率不能拼接。</p><p><strong>证据强度</strong><br>完整成功、部分得分、定性演示分开；小样本显示区间。</p></div></section><p class="source-links"><a href="{COLLECTION}">打开 Notion 专题 ↗</a><a href="https://contact-rich-loco-manipulation.github.io/program/index.html">Workshop 官方议程 ↗</a></p>'''
    content=content.replace(f'按<a href="{TEMPLATE}">五块证据链模板</a>','按五块证据链')
    content=content.replace('<div class="cards">', '<aside class="scope"><strong>还有哪些 Workshop 值得写？</strong><p>H2R、Learn@Deploy、Beneath the Policy，以及结构化物理智能与生成到动作。本轮九篇中六篇已完成全文精读，VETO、UMI 控制器选择与 Beyond Fixed Delays 三篇待获取全文。</p><a href="corl2026-workshops.html">查看 Workshop 论文与阅读状态 →</a></aside><div class="cards">',1)
    if not portable:
        content=content.replace('https://www.siyuanluoembodied.xin/papers/agentic-wam.html','agentic-wam.html')
        content=content.replace(f'<a href="{COLLECTION}">打开 Notion 专题 ↗</a>', '<a href="../index.html#all-readings">返回全站论文目录</a>')
    return shell('CoRL 2026 · 五个方向精读与主会目录',content,portable=portable)

def build_workshops():
    items=json.loads((ROOT/'scripts/corl2026/workshops.json').read_text())
    cards=[]
    for i,d in enumerate(items,1):
        papers=''.join('<li><strong>'+ (f'<a href="{html.escape(p["url"])}">{html.escape(p["name"])}</a>' if p.get('url') else html.escape(p['name'])) + '</strong> · '+html.escape(p['status'])+'</li>' for p in d['papers'])
        cards.append(f'<article class="paper-card"><span class="card-num">0{i}</span><div class="eyebrow">{html.escape(d["theme"])}</div><h2>{html.escape(d["name"])}</h2><p>{html.escape(d["question"])}</p><p class="boundary">{html.escape(d["why"])}</p><ul class="candidate-list">{papers}</ul><p class="evidence-note" data-evidence="paper">{html.escape(d["evidence"])}</p><a href="{d["url"]}">官方议程与论文入口 ↗</a></article>')
    content='<div class="eyebrow">CoRL 2026 / Workshop 阅读进度</div><h1>从哪里继续读？<br><span class="muted">五场 Workshop，三条优先路线</span></h1><p class="lede">优先顺序是本网站的阅读建议：先补人类数据的转换，再看部署中的适应，最后审计策略下面的控制接口。</p><aside class="scope"><strong>当前阅读状态</strong><p>本轮指定九篇已完成六篇：BATCH、RoSHI、CARD、FORCA、Gated Memory Policy、Blind Dexterity。VETO 尚未找到公开全文；UMI 控制器选择与 Beyond Fixed Delays 的 OpenReview PDF 下载返回 403，作者/公开索引未找到替代全文。三篇仅保留题目、展示类型与来源，不提供方法或性能结论。SPIN 与 G2A 的其他入口仍为报告/选题导航。</p><a href="corl2026.html">返回十六篇已完成精读与既有 AW-0 →</a></aside><div class="cards">'+''.join(cards)+'</div><section><h2>建议从这三组开始</h2><ol><li><strong>BATCH / RoSHI / CARD：</strong>读完 WB-WAM 后，进一步核对跨本体对齐与采集链路。先问监督信号如何得到，再问增加数据是否有效。</li><li><strong>FORCA / VETO / Gated Memory Policy：</strong>接在 AW-0、EmbodiedSWE 与 Memory 三篇之后；分别检查物理反馈、动作验证与部署适应。</li><li><strong>Blind Dexterity / UMI 控制器选择 / 推理延迟：</strong>接在 Workhorse、OCLO、HULK 之后；检验收益究竟来自策略，还是控制器、观测与时间尺度。</li></ol><p class="evidence-note" data-evidence="inference">这里提出的是阅读问题与排序，不是论文结论或跨论文排名。相同论文出现在多个 Workshop 时只计一次；Workhorse 的第二个 Workshop 入口不增加精读篇数。</p></section>'
    return shell('CoRL 2026 · Workshop 选题与候选论文',content)

def build_catalog(portable=False):
    entries=json.loads((ROOT/'notes/corl2026/sources/main-conference-manifest.json').read_text())
    rows=''
    for i,e in enumerate(entries):
        ctx='\n'.join(e.get('sessions',[])+[e.get('context','')])
        kind=e['kind']
        rows+=f'<tr data-kind="{kind.lower()}"><td>{i+1:03}</td><td><a href="{html.escape(e["url"])}">{html.escape(e["title"])}</a><details><summary>官方会议信息</summary><p>{html.escape(ctx)}</p></details></td><td>{kind}</td><td>仅目录</td></tr>'
    filters='<div class="filters" hidden><label>搜索标题 / 会议信息<input id="search" type="search" placeholder="如 world model、humanoid、memory" autocomplete="off"></label><label>展示类型<select id="kind"><option value="">全部</option><option value="oral">Oral</option><option value="spotlight">Spotlight</option><option value="poster">Poster</option></select></label><button id="reset" type="button">清空筛选</button><output id="count" aria-live="polite">687 / 687 篇</output></div>'
    content=f'<div class="eyebrow">OFFICIAL MAIN-CONFERENCE INDEX</div><h1>CoRL 2026 · 687 篇主会目录</h1><p class="lede">这是官方标题与会议展示信息的索引，尚未逐篇通读，不含由标题猜测的方法结论。</p><p>来源：<a href="https://www.corl.org/program/accepted-papers">CoRL 官方 Accepted Papers</a>，2026-11-17 获取；按 OpenReview 链接去重。源页另列 21 个 Oral、72 个 Spotlight，它们也属于海报列表，不重复计篇数。</p><p class="scope">十六篇精读与既有 AW-0 精读入口见<a href="{COLLECTION if portable else "corl2026.html"}">阅读室</a>；它们的 Workshop / 关联阅读身份与本页主会目录分开记录。</p>{filters}<p id="empty" hidden>没有匹配结果，请换一个关键词或清空筛选。</p><div class="eval-table-wrap"><table id="catalog"><thead><tr><th>序号</th><th>论文 · 原始链接</th><th>展示类型</th><th>阅读状态</th></tr></thead><tbody>{rows}</tbody></table></div><noscript><p>JavaScript 未开启，下面仍可阅读全部 687 项，也可用浏览器页面查找。</p></noscript>'
    return shell('CoRL 2026 · 687 篇主会目录',content,portable=portable)

def main():
    (ROOT/'notes/corl2026/exports').mkdir(parents=True,exist_ok=True)
    for slug,page,box,num,dpi in CROPS:
        out=ROOT/f'assets/figures/corl2026/{slug}-fig-{num}.png'
        if not out.exists() or '--recrop' in sys.argv:
            doc=pymupdf.open(ROOT/f'pdfs/corl2026/{slug}.pdf')
            doc[page-1].get_pixmap(dpi=dpi,clip=pymupdf.Rect(*box),alpha=False).save(out)
            print('crop',out.name)
    for d in DATA:
        slug=d['slug']
        (ROOT/f'papers/corl2026-{slug}.html').write_text(render_paper(d))
        (ROOT/f'notes/corl2026/exports/{slug}.html').write_text(render_paper(d,True))
        (ROOT/f'notes/corl2026/exports/{slug}.md').write_text(preprocess((ROOT/f'notes/corl2026/reading/{slug}.md').read_text()))
    (ROOT/'papers/corl2026.html').write_text(build_collection())
    (ROOT/'papers/corl2026-catalog.html').write_text(build_catalog())
    (ROOT/'papers/corl2026-workshops.html').write_text(build_workshops())
    (ROOT/'notes/corl2026/exports/main-conference-catalog.html').write_text(build_catalog(True))
    (ROOT/'notes/corl2026/metadata.json').write_text(json.dumps(DATA,ensure_ascii=False,indent=2))
    print(f'Built {len(DATA)} paper pages, collection, catalog, workshop guide and portable exports.')

if __name__=='__main__': main()
