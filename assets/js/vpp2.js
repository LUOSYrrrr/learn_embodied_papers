/* Page-local progressive enhancement. The paper remains readable without JS. */
(function () {
  'use strict';
  function initMath() {
    if (window.renderMathInElement) window.renderMathInElement(document.querySelector('main'), {
      delimiters: [{left:'$$',right:'$$',display:true},{left:'$',right:'$',display:false}],
      throwOnError:false, strict:false
    });
  }
  initMath();
  let started = false;
  function loadComponents() {
    if (started) return;
    started = true;
    const script = document.createElement('script');
    script.src = '../assets/js/interactive.js';
    script.onload = function () {
      const first = document.querySelector('.hotspot');
      if (first && !location.search.includes('edit-hotspots=1')) first.click();
      document.querySelectorAll('.step-walker').forEach(function (root) {
        root.addEventListener('keydown', function (event) {
          const dots = Array.from(root.querySelectorAll('.sw-dot'));
          const current = Array.from(root.querySelectorAll('.sw-step')).findIndex(s => s.classList.contains('active'));
          let next = null;
          if (event.key === 'ArrowRight') next = Math.min(dots.length - 1, current + 1);
          if (event.key === 'ArrowLeft') next = Math.max(0, current - 1);
          if (event.key === 'Home') next = 0;
          if (event.key === 'End') next = dots.length - 1;
          if (next !== null) { event.preventDefault(); dots[next].click(); }
        });
      });
    };
    document.head.appendChild(script);
  }
  if (location.search.includes('edit-hotspots=1') || !('IntersectionObserver' in window)) loadComponents();
  else {
    const observer = new IntersectionObserver(function (entries) {
      if (entries.some(entry => entry.isIntersecting)) { loadComponents(); observer.disconnect(); }
    }, {rootMargin:'600px'});
    document.querySelectorAll('.fig-interactive,.tab-switcher,.quiz,[data-symbol]').forEach(el => observer.observe(el));
  }
  let closed = [];
  window.addEventListener('beforeprint', function () {
    closed = Array.from(document.querySelectorAll('details:not([open])'));
    closed.forEach(el => {el.open = true;});
  });
  window.addEventListener('afterprint', function () {closed.forEach(el => {el.open = false;}); closed = [];});
})();
