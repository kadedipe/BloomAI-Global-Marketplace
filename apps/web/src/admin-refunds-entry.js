import './commerce.css';

const API=(import.meta.env.VITE_API_URL||'http://localhost:8000').replace(/\/$/,'');
const api=(path,options={})=>fetch(`${API}${path}`,{credentials:'include',headers:{...(options.body?{'Content-Type':'application/json'}:{}),...(options.headers||{})},...options});
const escapeHtml=value=>String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const money=(currency,value)=>`${escapeHtml(currency)} ${Number(value||0).toLocaleString(undefined,{minimumFractionDigits:2,maximumFractionDigits:2})}`;

async function loadRefunds(){
  const response=await api('/api/v1/admin/commerce/refunds');
  if(response.status===401||response.status===403)return;
  if(!response.ok)return;
  renderRefunds((await response.json()).items||[]);
}

function renderRefunds(items){
  let panel=document.getElementById('admin-refund-queue');
  if(!panel){
    panel=document.createElement('section');
    panel.id='admin-refund-queue';
    panel.className='panel wide';
    const activity=document.getElementById('activity');
    (activity?.parentNode||document.querySelector('main'))?.insertBefore(panel,activity||null);
  }
  panel.innerHTML=`<div class="panel-head"><div><h3>Refund operations</h3><p>Administrator-only Paystack refund execution. Approved refunds can be processed once; provider reconciliation updates the final status.</p></div><button type="button" class="secondary" data-refund-refresh>Refresh refunds</button></div>${items.length?`<div class="table-wrap"><table><thead><tr><th>Order</th><th>Product</th><th>Buyer</th><th>Amount</th><th>Status</th><th>Reason</th><th>Action</th></tr></thead><tbody>${items.map(item=>`<tr><td>#${item.order_id}</td><td><b>${escapeHtml(item.product_name)}</b></td><td>${escapeHtml(item.buyer_name)}</td><td>${money(item.currency,item.amount)}</td><td><strong>${escapeHtml(item.refund_status)}</strong>${item.refund_provider_status?`<br><small>${escapeHtml(item.refund_provider_status)}</small>`:''}</td><td>${escapeHtml(item.refund_reason||'—')}</td><td>${item.can_execute?`<button type="button" class="primary" data-execute-refund="${item.order_id}">Execute refund</button>`:'—'}</td></tr>`).join('')}</tbody></table></div>`:'<p class="muted">No refund workflows yet.</p>'}`;
  panel.querySelector('[data-refund-refresh]')?.addEventListener('click',loadRefunds);
  panel.querySelectorAll('[data-execute-refund]').forEach(button=>button.addEventListener('click',()=>executeRefund(button)));
}

async function executeRefund(button){
  const orderId=button.dataset.executeRefund;
  if(!window.confirm(`Execute the approved Paystack refund for order #${orderId}? This sends a real request to the configured Paystack account.`))return;
  button.disabled=true;
  const original=button.textContent;
  button.textContent='Processing…';
  const response=await api(`/api/v1/orders/${orderId}/refund-execute`,{method:'POST'});
  const body=await response.json().catch(()=>({}));
  if(!response.ok){
    alert(body.detail||'Refund could not be executed.');
    button.disabled=false;
    button.textContent=original;
    return;
  }
  alert(`Refund for order #${orderId} is now ${body.refund_status}.`);
  await loadRefunds();
}

const observer=new MutationObserver(()=>{
  if(document.querySelector('.admin-shell')&&!document.getElementById('admin-refund-queue'))loadRefunds();
});
observer.observe(document.documentElement,{childList:true,subtree:true});
window.addEventListener('focus',loadRefunds);
setTimeout(loadRefunds,700);
