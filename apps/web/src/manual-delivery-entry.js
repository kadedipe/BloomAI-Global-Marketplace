const API=(import.meta.env.VITE_API_URL||'http://localhost:8000').replace(/\/$/,'');
const api=(path,options={})=>fetch(`${API}${path}`,{credentials:'include',headers:{...(options.body?{'Content-Type':'application/json'}:{}),...(options.headers||{})},...options});

const METHODS={
  local_delivery:'Local delivery',
  vendor_delivery:'Vendor delivery',
  pickup:'Customer pickup',
  independent_courier:'Independent courier',
};

function orderId(card){
  const text=card.querySelector('small')?.textContent||'';
  const match=text.match(/#(\d+)/);
  return match?match[1]:null;
}

function chooseMethod(){
  const answer=window.prompt('No-tracking delivery method: local_delivery, vendor_delivery, pickup, or independent_courier','local_delivery');
  if(!answer)return null;
  const normalized=answer.trim().toLowerCase().replace(/[-\s]+/g,'_');
  if(!METHODS[normalized]){
    window.alert('Choose local_delivery, vendor_delivery, pickup, or independent_courier.');
    return null;
  }
  return normalized;
}

async function markWithoutTracking(id,button){
  const delivery_method=chooseMethod();
  if(!delivery_method)return;
  if(!window.confirm(`Mark order #${id} as shipped using ${METHODS[delivery_method]} with no tracking number?`))return;
  button.disabled=true;
  const response=await api(`/api/v1/orders/${id}/fulfillment`,{method:'PATCH',body:JSON.stringify({status:'shipped',delivery_method})});
  const body=await response.json().catch(()=>({}));
  if(!response.ok){
    window.alert(body.detail||'No-tracking fulfillment could not be updated.');
    button.disabled=false;
    return;
  }
  document.querySelector('.order-refresh')?.click();
  setTimeout(enhance,350);
}

async function enhanceCard(card){
  if(card.dataset.manualDelivery)return;
  const id=orderId(card);if(!id)return;
  card.dataset.manualDelivery='loading';
  const response=await api(`/api/v1/orders/${id}`);
  if(!response.ok){delete card.dataset.manualDelivery;return;}
  const order=await response.json();
  if(order.status!=='paid'||!['unfulfilled','processing'].includes(order.fulfillment_status)){
    card.dataset.manualDelivery='done';
    return;
  }
  const actions=card.querySelector('.order-card-actions');
  if(!actions){delete card.dataset.manualDelivery;return;}
  const button=document.createElement('button');
  button.className='secondary';
  button.textContent='No-tracking delivery';
  button.title='Use local delivery, vendor delivery, pickup, or an independent courier without inventing a tracking number.';
  button.onclick=()=>markWithoutTracking(id,button);
  actions.appendChild(button);
  card.dataset.manualDelivery='done';
}

function enhance(){
  document.querySelectorAll('.sales .order-card').forEach(card=>enhanceCard(card));
}

const observer=new MutationObserver(enhance);
observer.observe(document.documentElement,{subtree:true,childList:true});
window.addEventListener('focus',enhance);
setTimeout(enhance,700);
