// 主题切换：暗色 / 亮色
(function () {
  // 1. 启动时立刻应用，避免闪烁（应放在 <head> 中尽早执行）
  var saved = localStorage.getItem('theme');
  if (saved === 'light' || saved === 'dark') {
    document.documentElement.setAttribute('data-theme', saved);
  }

  // 2. DOM 就绪后插入按钮
  function inject() {
    var nav = document.querySelector('.nav-links');
    if (!nav || nav.querySelector('.theme-toggle')) return;
    var btn = document.createElement('button');
    btn.className = 'theme-toggle';
    btn.title = '切换主题 / Toggle theme';
    btn.setAttribute('aria-label', '切换主题');
    btn.innerHTML = '<span class="icon-sun">☀</span><span class="icon-moon">☾</span>';
    btn.addEventListener('click', function () {
      var cur = document.documentElement.getAttribute('data-theme') === 'light' ? 'light' : 'dark';
      var next = cur === 'light' ? 'dark' : 'light';
      document.documentElement.setAttribute('data-theme', next);
      localStorage.setItem('theme', next);
    });
    nav.appendChild(btn);
  }
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', inject);
  } else {
    inject();
  }
})();
