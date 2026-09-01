import './commerce.css';

const API=(import.meta.env.VITE_API_URL||'http://localhost:8000').replace(/\/$/,'');
const api=(path,options={})=>fetch(`${API}${path}`,{credentials:'include',headers:{...(options.body?{'Content-Type':'application/json'}:{}),...(options.headers||{})},...options});
const escapeHtml=value=>String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const money=(currency,value)=>`${escapeHtml(currency)} ${Number(value).toFixed(2)}`;
let user=null;
let products=[];

async function refresh(){
  const [profileResponse,productResponse]=await Promise.all([api('/api/v1/auth/me'),api('/api/v1/products')]);
  user=profileResponse.ok?await profileResponse.json():null;
  products=productResponse.ok?await productResponse.json():[];
  updateAvailability();
  renderInventoryManager();
  enhanceOrderCards();
}

function productForCard(card,index){
  const title=card.querySelector('h3')?.textContent?.trim();
  return products.find((item,i)=>i===index&&item.name===title)||products.find(item=>item.name===title);
}

function updateAvailability(){
  document.querySelectorAll('.grid article').forEach((card,index)=>{
    const product=productForCard(card,index);if(!product)return;
    const buy=[...card.querySelectorAll('button')].find(button=>button.textContent.includes('Buy securely')||button.dataset.availability);
    if(!buy)return;
    buy.dataset.availability='1';
    const soldOut=product.inventory_quantity===0;
    const unavailable=!product.is_active;
    if(soldOut||unavailable){
      buy.disabled=true;
      buy.textContent=soldOut?'Sold out':'Unavailable';
      buy.title=soldOut?'This product is out of stock':'This listing is temporarily unavailable';
    }
    let badge=card.querySelector('.inventory-badge');
    if(product.inventory_quantity!==null&&!badge){badge=document.createElement('small');badge.className='inventory-badge';card.querySelector('strong')?.insertAdjacentElement('afterend',badge)}
    if(badge)badge.textContent=product.inventory_quantity===null?'':`${product.inventory_quantity} in stock`;
  });
}

function renderInventoryManager(){
  document.getElementById('inventory-manager')?.remove();
  if(!user||user.role!=='vendor')return;
  const owned=products.filter(product=>product.vendor_id===user.id);
  const host=document.querySelector('#order-center')||document.querySelector('#vendor')||document.querySelector('#market');
  if(!host)return;
  const section=document.createElement('section');section.id='inventory-manager';section.className='inventory-manager';
  section.innerHTML=`<div class="section-heading"><div><span class="kicker">Inventory & availability</span><h2>Manage stock</h2></div></div><p class="commerce-help">Leave stock blank for an untracked listing. Set stock to 0 to mark it sold out, or switch availability off to pause checkout.</p><div class="inventory-list">${owned.length?owned.map(product=>`<form class="inventory-row" data-product="${product.id}"><div><strong>${escapeHtml(product.name)}</strong><small>${money(product.currency,product.price)}</small></div><label>Stock<input name="inventory_quantity" type="number" min="0" max="1000000" value="${product.inventory_quantity??''}" placeholder="Untracked"></label><label class="inventory-toggle"><input name="is_active" type="checkbox" ${product.is_active?'checked':''}> Available</label><button class="secondary">Save</button><span class="inventory-message" role="status"></span></form>`).join(''):'<p>No listings available.</p>'}</div>`;
  host.insertAdjacentElement('afterend',section);
  section.querySelectorAll('.inventory-row').forEach(form=>form.onsubmit=saveInventory);
}

async function saveInventory(event){
  event.preventDefault();const form=event.currentTarget;const message=form.querySelector('.inventory-message');const button=form.querySelector('button');button.disabled=true;message.textContent='Saving…';
  const raw=form.elements.inventory_quantity.value.trim();
  const payload={inventory_quantity:raw===''?null:Number(raw),is_active:form.elements.is_active.checked};
  const response=await api(`/api/v1/products/${form.dataset.product}`,{method:'PATCH',body:JSON.stringify(payload)});
  if(response.ok){const updated=await response.json();products=products.map(product=>product.id===updated.id?updated:product);message.textContent='Saved';updateAvailability()}
  else{const body=await response.json().catch(()=>({}));message.textContent=body.detail||'Could not save.'}
  button.disabled=false;
}

function orderId(card){
  const text=card.querySelector('small')?.textContent||'';
  const match=text.match(/#(\d+)/);return match?match[1]:null;
}

function enhanceOrderCards(){
  document.querySelectorAll('.order-card').forEach(card=>{
    if(card.dataset.commerce)return;const id=orderId(card);if(!id)return;card.dataset.commerce='1';
    const actions=card.querySelector('.order-card-actions')||document.createElement('div');actions.classList.add('order-card-actions');if(!actions.parentNode)card.appendChild(actions);
    const details=document.createElement('button');details.className='secondary';details.textContent='View details';details.onclick=()=>openOrderDetail(id);actions.appendChild(details);
    const pill=card.querySelector('.order-status-pill');if(pill?.classList.contains('paid')){
      if(card.closest('.purchases')){
        const receipt=document.createElement('button');receipt.className='secondary';receipt.textContent='Receipt';receipt.onclick=()=>printReceipt(id);actions.appendChild(receipt);
      }
      loadActions(card,id,Boolean(card.closest('.sales')));
    }
  });
}

async function loadActions(card,id,sellerView){
  const response=await api(`/api/v1/orders/${id}`);if(!response.ok)return;const order=await response.json();const actions=card.querySelector('.order-card-actions');
  const meta=document.createElement('p');meta.className='fulfillment-meta';meta.innerHTML=`Fulfillment: <strong>${escapeHtml(order.fulfillment_status)}</strong>${order.tracking_number?` · ${escapeHtml(order.carrier||'Carrier')} ${escapeHtml(order.tracking_number)}`:''}${order.refund_status!=='none'?`<br>Refund: <strong>${escapeHtml(order.refund_status)}</strong>`:''}`;actions.before(meta);
  if(sellerView){
    if(order.fulfillment_status==='unfulfilled')actions.appendChild(actionButton('Start processing',()=>fulfill(id,'processing')));
    if(['unfulfilled','processing'].includes(order.fulfillment_status))actions.appendChild(actionButton('Mark shipped',()=>ship(id)));
    if(order.fulfillment_status==='shipped')actions.appendChild(actionButton('Mark delivered',()=>fulfill(id,'delivered')));
    if(order.refund_status==='requested'){
      actions.appendChild(actionButton('Approve refund',()=>reviewRefund(id,'approved')));
      actions.appendChild(actionButton('Decline refund',()=>reviewRefund(id,'rejected'),'secondary'));
    }
  }else if(['none','rejected'].includes(order.refund_status)){
    actions.appendChild(actionButton('Request refund',()=>requestRefund(id),'secondary'));
  }
}

function actionButton(label,handler,className='primary'){const button=document.createElement('button');button.className=className;button.textContent=label;button.onclick=handler;return button}

async function fulfill(id,status,extra={}){
  const response=await api(`/api/v1/orders/${id}/fulfillment`,{method:'PATCH',body:JSON.stringify({status,...extra})});
  const body=await response.json().catch(()=>({}));if(!response.ok){alert(body.detail||'Fulfillment could not be updated.');return}await refreshOrdersAndCommerce();
}

function ship(id){
  const carrier=window.prompt('Carrier name');if(!carrier)return;
  const tracking_number=window.prompt('Tracking number');if(!tracking_number)return;
  fulfill(id,'shipped',{carrier,tracking_number});
}

async function requestRefund(id){
  const reason=window.prompt('Why are you requesting a refund?');if(!reason)return;
  const response=await api(`/api/v1/orders/${id}/refund-request`,{method:'POST',body:JSON.stringify({reason})});
  const body=await response.json().catch(()=>({}));if(!response.ok){alert(body.detail||'Refund request could not be submitted.');return}await refreshOrdersAndCommerce();
}

async function reviewRefund(id,decision){
  if(!window.confirm(`${decision==='approved'?'Approve':'Decline'} this refund request?`))return;
  const response=await api(`/api/v1/orders/${id}/refund-review`,{method:'PATCH',body:JSON.stringify({decision})});
  const body=await response.json().catch(()=>({}));if(!response.ok){alert(body.detail||'Refund review could not be saved.');return}await refreshOrdersAndCommerce();
}

async function refreshOrdersAndCommerce(){
  document.querySelector('.order-refresh')?.click();setTimeout(refresh,250);
}

async function openOrderDetail(id){
  const response=await api(`/api/v1/orders/${id}`);const body=await response.json().catch(()=>({}));if(!response.ok){alert(body.detail||'Order details are unavailable.');return}
  const backdrop=document.createElement('div');backdrop.className='commerce-backdrop';backdrop.innerHTML=`<section class="commerce-dialog" role="dialog" aria-modal="true"><button class="commerce-close" aria-label="Close">×</button><span class="kicker">Order #${body.id}</span><h2>${escapeHtml(body.product_name)}</h2><div class="commerce-detail-grid"><p><b>Payment</b><br>${escapeHtml(body.status)}</p><p><b>Fulfillment</b><br>${escapeHtml(body.fulfillment_status)}</p><p><b>Total</b><br>${money(body.currency,body.total)}</p><p><b>Quantity</b><br>${body.quantity}</p><p><b>Buyer</b><br>${escapeHtml(body.buyer_name)}</p><p><b>Vendor</b><br>${escapeHtml(body.vendor_name)}</p></div><h3>Delivery</h3><p>${escapeHtml(body.recipient_name||'')} · ${escapeHtml(body.phone||'')}</p><p>${escapeHtml([body.address_line1,body.city,body.region,body.postal_code,body.country].filter(Boolean).join(', '))}</p>${body.tracking_number?`<h3>Shipment</h3><p>${escapeHtml(body.carrier||'Carrier')}: <strong>${escapeHtml(body.tracking_number)}</strong></p>`:''}${body.refund_status!=='none'?`<h3>Refund</h3><p>Status: <strong>${escapeHtml(body.refund_status)}</strong></p><p>${escapeHtml(body.refund_reason||'')}</p>`:''}</section>`;document.body.appendChild(backdrop);const close=()=>backdrop.remove();backdrop.onclick=e=>e.target===backdrop&&close();backdrop.querySelector('.commerce-close').onclick=close;
}

async function printReceipt(id){
  const response=await api(`/api/v1/orders/${id}/receipt`);const receipt=await response.json().catch(()=>({}));if(!response.ok){alert(receipt.detail||'Receipt is unavailable.');return}
  const popup=window.open('','_blank','noopener,noreferrer,width=760,height=720');if(!popup)return;
  popup.document.write(`<!doctype html><title>${escapeHtml(receipt.receipt_number)}</title><style>body{font:16px system-ui;margin:48px;color:#173f30}h1{margin-bottom:4px}.row{display:flex;justify-content:space-between;border-bottom:1px solid #ddd;padding:10px 0}.muted{color:#667}button{padding:10px 16px;margin-top:24px}</style><h1>BloomAI receipt</h1><p class="muted">${escapeHtml(receipt.receipt_number)} · ${new Date(receipt.paid_at).toLocaleString()}</p><div class="row"><span>Product</span><b>${escapeHtml(receipt.product_name)}</b></div><div class="row"><span>Buyer</span><b>${escapeHtml(receipt.buyer_name)}</b></div><div class="row"><span>Vendor</span><b>${escapeHtml(receipt.vendor_name)}</b></div><div class="row"><span>Quantity</span><b>${receipt.quantity}</b></div><div class="row"><span>Unit price</span><b>${money(receipt.currency,receipt.unit_price)}</b></div><div class="row"><span>Total paid</span><b>${money(receipt.currency,receipt.total)}</b></div><p><b>Delivery</b><br>${escapeHtml(receipt.delivery_address)}</p><p class="muted">Payment reference: ${escapeHtml(receipt.reference)}</p><button onclick="window.print()">Print receipt</button>`);popup.document.close();
}

const observer=new MutationObserver(()=>{updateAvailability();enhanceOrderCards()});observer.observe(document.documentElement,{subtree:true,childList:true});
window.addEventListener('focus',refresh);setTimeout(refresh,450);
