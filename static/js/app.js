function rangeVal(el,id,suffix){const o=document.getElementById(id);if(o)o.textContent=el.value+suffix;setTimeout(()=>document.querySelectorAll(".toast").forEach(x=>x.remove()),4500);}
