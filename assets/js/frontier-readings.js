(() => {
 'use strict';
 let previouslyClosed=[];
 window.addEventListener('beforeprint',()=>{previouslyClosed=[...document.querySelectorAll('details:not([open])')];previouslyClosed.forEach(d=>d.open=true);});
 window.addEventListener('afterprint',()=>{previouslyClosed.forEach(d=>d.open=false);previouslyClosed=[];});
})();
