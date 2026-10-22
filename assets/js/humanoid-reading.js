// Teaching-only scalar weighted least squares. Not a robot simulator or GMR reimplementation.
(() => {
  'use strict';
  const lab=document.querySelector('[data-ik-lab]');
  if(lab){
    const inputs=Object.fromEntries(['hand','damping','limit'].map(k=>[k,lab.querySelector(`[name=${k}]`)]));
    function update(){
      const wh=+inputs.hand.value,lambda=+inputs.damping.value,cap=+inputs.limit.value;
      const raw=0.2*wh/(wh+1+lambda),q=Math.min(raw,cap);
      lab.querySelector('[data-lab-result]').textContent=`修正 Δq = ${q.toFixed(4)} rad；手部剩余误差 = ${(0.2-q).toFixed(4)}；保姿偏移 = ${q.toFixed(4)} rad${raw>cap?'（触及硬约束）':''}`;
      for(const [k,input]of Object.entries(inputs))lab.querySelector(`[data-value=${k}]`).textContent=input.value;
    }
    Object.values(inputs).forEach(input=>input.addEventListener('input',update));update();
  }
  let opened=[];
  window.addEventListener('beforeprint',()=>{opened=[...document.querySelectorAll('details:not([open])')];opened.forEach(d=>d.open=true)});
  window.addEventListener('afterprint',()=>{opened.forEach(d=>d.open=false);opened=[]});
})();
