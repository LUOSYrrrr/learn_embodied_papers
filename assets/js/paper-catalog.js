(() => {
  const input = document.getElementById('paper-catalog-search');
  if (!input) return;
  const items = [...document.querySelectorAll('#paper-catalog-list > li')];
  const count = document.getElementById('paper-catalog-count');
  const empty = document.getElementById('paper-catalog-empty');
  input.addEventListener('input', () => {
    const terms = input.value.toLocaleLowerCase().trim().split(/\s+/).filter(Boolean);
    let visible = 0;
    for (const item of items) {
      const text = item.textContent.toLocaleLowerCase();
      item.hidden = !terms.every(term => text.includes(term));
      if (!item.hidden) visible++;
    }
    count.textContent = `显示 ${visible} / ${items.length} 个页面`;
    empty.hidden = visible !== 0;
  });
})();
