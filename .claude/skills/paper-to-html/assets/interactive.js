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
    wrap.querySelectorAll('.hotspot').forEach(h => {
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

  function init() {
    document.querySelectorAll('.step-walker').forEach(initStepWalker);
    document.querySelectorAll('.hotspot-wrap').forEach(initHotspotWrap);
    document.querySelectorAll('.quiz').forEach(initQuiz);
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
