// 交互组件：Step Walker / Image Hotspot / Quiz
(function () {

  // ── Step Walker ──
  function initStepWalker(root) {
    const steps = root.querySelectorAll('.sw-step');
    const dots = root.querySelectorAll('.sw-dot');
    const counter = root.querySelector('.sw-counter');
    const prev = root.querySelector('.sw-btn.prev');
    const next = root.querySelector('.sw-btn.next');
    let i = 0;
    function show(idx) {
      i = Math.max(0, Math.min(steps.length - 1, idx));
      steps.forEach((s, k) => s.classList.toggle('active', k === i));
      dots.forEach((d, k) => {
        d.classList.toggle('active', k === i);
        d.classList.toggle('done', k < i);
      });
      counter.textContent = (i + 1) + ' / ' + steps.length;
      prev.disabled = i === 0;
      next.disabled = i === steps.length - 1;
      // 若步骤里有关联的 hotspot，激活之
      const hsTarget = steps[i].dataset.hotspot;
      if (hsTarget && root.dataset.hotspotGroup) {
        const wrap = document.querySelector('.hotspot-wrap[data-hotspot-group="' + root.dataset.hotspotGroup + '"]');
        if (wrap) activateHotspot(wrap, hsTarget);
      }
    }
    prev.addEventListener('click', () => show(i - 1));
    next.addEventListener('click', () => show(i + 1));
    dots.forEach((d, k) => d.addEventListener('click', () => show(k)));
    show(0);
  }

  // ── Image Hotspot ──
  function findPanel(wrap) {
    // panel 在 .fig-block 之后作为兄弟元素
    let el = wrap.closest('.fig-block') || wrap;
    let sib = el.nextElementSibling;
    while (sib && !sib.classList.contains('hotspot-panel')) sib = sib.nextElementSibling;
    return sib;
  }
  function activateHotspot(wrap, id) {
    const hotspots = wrap.querySelectorAll('.hotspot');
    const panel = findPanel(wrap);
    hotspots.forEach(h => h.classList.toggle('active', h.dataset.id === id));
    const target = wrap.querySelector('.hotspot[data-id="' + id + '"]');
    if (target && panel) {
      panel.innerHTML =
        '<div class="hp-title">📍 ' + (target.dataset.title || ('点 ' + id)) + '</div>' +
        '<div>' + (target.dataset.body || '') + '</div>';
    }
  }
  function initHotspotWrap(wrap) {
    const panel = findPanel(wrap);
    if (panel && !panel.dataset.init) {
      panel.dataset.init = '1';
      panel.innerHTML = '<div class="hp-empty">点击图上绿色数字查看讲解，或下方逐步导览</div>';
    }
    wrap.querySelectorAll('.hotspot').forEach((h, i) => {
      if (!h.textContent.trim()) h.textContent = String(i + 1);
      h.addEventListener('click', () => activateHotspot(wrap, h.dataset.id));
    });
  }

  // ── Quiz ──
  function initQuiz(quiz) {
    const correct = quiz.dataset.correct;
    const explain = quiz.dataset.explain || '';
    const explainWrong = quiz.dataset.explainWrong || '';
    const opts = quiz.querySelectorAll('.q-opt');
    const fb = quiz.querySelector('.q-feedback');
    opts.forEach(o => {
      o.addEventListener('click', () => {
        if (quiz.dataset.answered) return;
        quiz.dataset.answered = '1';
        const isCorrect = o.dataset.k === correct;
        opts.forEach(x => {
          x.classList.add('answered');
          if (x.dataset.k === correct) x.classList.add('correct');
          else if (x === o) x.classList.add('wrong');
        });
        fb.classList.add('show', isCorrect ? 'correct' : 'wrong');
        fb.innerHTML = (isCorrect ? '✅ 答对了。' : '❌ 不对。正确答案是上面的绿色那个。<br>') + (isCorrect ? explain : (explainWrong || explain));
      });
    });
  }

  // ── Hotspot Edit Mode (?edit-hotspots=1) ──
  // 两种用法：
  //   1) 拖拽已有点：按住点圈直接拖 → 松手后坐标自动更新，汇总面板实时刷新
  //   2) 取新点坐标：点图上空白区域 → 右上角 toast 显示坐标，复制到剪贴板
  // 改完所有点后，点右下面板的 "Copy All" → 得到一个 data-id → style 映射，回 HTML 批量粘贴
  function initEditMode() {
    if (!/[?&]edit-hotspots=1/.test(location.search)) return;

    // 右上角 toast（单点取坐标用）
    const toast = document.createElement('div');
    toast.className = 'hs-edit-toast';
    toast.innerHTML =
      '🎯 <b>Hotspot edit mode</b><br>' +
      '• 拖拽圆点 = 调整坐标<br>' +
      '• 点空白处 = 取新坐标<br>' +
      '<small style="opacity:.7">右下角面板支持全部导出</small>';
    document.body.appendChild(toast);

    // 右下角汇总面板
    const panel = document.createElement('div');
    panel.className = 'hs-edit-panel';
    panel.innerHTML =
      '<div class="hs-edit-panel-head">' +
        '<b>🎯 All Hotspots</b>' +
        '<button class="hs-copy-btn" type="button">Copy All</button>' +
      '</div>' +
      '<pre class="hs-out"></pre>';
    document.body.appendChild(panel);
    const out = panel.querySelector('.hs-out');
    const copyBtn = panel.querySelector('.hs-copy-btn');

    function buildExport() {
      const groups = {};
      document.querySelectorAll('.hotspot-wrap').forEach(wrap => {
        const g = wrap.dataset.hotspotGroup || '(no-group)';
        if (!groups[g]) groups[g] = [];
        wrap.querySelectorAll('.hotspot').forEach(h => {
          groups[g].push({
            id: h.dataset.id || '',
            left: h.style.left || '',
            top: h.style.top || ''
          });
        });
      });
      // HTML 着色版本（面板里显示）
      let html = '';
      // 纯文本版本（复制用）
      let plain = '';
      for (const g in groups) {
        html  += '<span class="hs-group">── ' + g + ' ──</span>\n';
        plain += '── ' + g + ' ──\n';
        groups[g].forEach(h => {
          const coord = 'left:' + h.left + '; top:' + h.top + ';';
          html  += 'data-id="<span class="hs-id">' + h.id + '</span>" style="<span class="hs-coord">' + coord + '</span>"\n';
          plain += 'data-id="' + h.id + '" style="' + coord + '"\n';
        });
        html  += '\n';
        plain += '\n';
      }
      out.innerHTML = html;
      out.dataset.plain = plain;
    }

    copyBtn.addEventListener('click', () => {
      const text = out.dataset.plain || '';
      if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
          copyBtn.textContent = '✓ Copied';
          copyBtn.classList.add('copied');
          setTimeout(() => {
            copyBtn.textContent = 'Copy All';
            copyBtn.classList.remove('copied');
          }, 1500);
        }).catch(() => {});
      }
    });

    // 每个 wrap 挂 drag + click 双行为
    document.querySelectorAll('.hotspot-wrap').forEach(wrap => {
      wrap.classList.add('edit-mode');

      // 阻止已有 click 激活逻辑（initHotspotWrap 里注册的）
      wrap.querySelectorAll('.hotspot').forEach(hs => {
        hs.addEventListener('click', e => { e.stopPropagation(); e.preventDefault(); }, true);
      });

      // toast 用 marker
      const marker = document.createElement('div');
      marker.className = 'hs-edit-marker';
      marker.style.display = 'none';
      wrap.appendChild(marker);

      // drag 逻辑（mousedown 在 hotspot 上启动）
      let dragging = null;
      wrap.querySelectorAll('.hotspot').forEach(hs => {
        hs.addEventListener('mousedown', e => {
          e.preventDefault();
          e.stopPropagation();
          dragging = hs;
          hs.classList.add('dragging');
        });
      });

      function onMove(e) {
        if (!dragging || !wrap.contains(dragging)) return;
        const rect = wrap.getBoundingClientRect();
        const x = ((e.clientX - rect.left) / rect.width) * 100;
        const y = ((e.clientY - rect.top)  / rect.height) * 100;
        const clampedX = Math.max(0, Math.min(100, x));
        const clampedY = Math.max(0, Math.min(100, y));
        dragging.style.left = clampedX.toFixed(1) + '%';
        dragging.style.top  = clampedY.toFixed(1) + '%';
        buildExport();
      }
      function onUp() {
        if (dragging) {
          dragging.classList.remove('dragging');
          dragging = null;
          buildExport();
        }
      }
      document.addEventListener('mousemove', onMove);
      document.addEventListener('mouseup', onUp);

      // 点空白（非 hotspot）= 取新坐标到 toast
      wrap.addEventListener('click', e => {
        if (e.target.classList.contains('hotspot')) return;
        const rect = wrap.getBoundingClientRect();
        const x = ((e.clientX - rect.left) / rect.width) * 100;
        const y = ((e.clientY - rect.top)  / rect.height) * 100;
        const coord = 'left:' + x.toFixed(1) + '%; top:' + y.toFixed(1) + '%;';
        marker.style.left = x + '%';
        marker.style.top  = y + '%';
        marker.style.display = 'block';
        const group = wrap.dataset.hotspotGroup || '(no-group)';
        toast.innerHTML =
          '🎯 <b>' + group + '</b> · 新坐标<br>' +
          '<span style="color:#7ee">' + coord + '</span><br>' +
          '<small style="opacity:.7">已复制到剪贴板</small>';
        if (navigator.clipboard) navigator.clipboard.writeText(coord).catch(() => {});
      });
    });

    buildExport();
  }

  function init() {
    document.querySelectorAll('.step-walker').forEach(initStepWalker);
    document.querySelectorAll('.hotspot-wrap').forEach(initHotspotWrap);
    document.querySelectorAll('.quiz').forEach(initQuiz);
    initEditMode();
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
