import './order-flow.css';

const API=(import.meta.env.VITE_API_URL||'http://localhost:8000').replace(/\/$/,'');
const api=(path,options={})=>fetch(`${API}${path}`,{credentials:'include',headers:{...(options.body?{'Content-Type':'application/json'}:{}),...(options.headers||{})},...options});
const money=(currency,value)=>`${currency} ${Number(value).toFixed(2)}`;
let products=[];
let user=null;

async function fetchCurrentUser(){
  try{
    const response=await api('/api/v1/auth/me');
    if(response.status===401){user=null;return null}
    if(!response.ok)return user;
    user=await response.json();
    return user;
  }catch{return user}
}

function openSignIn(){
  const button=[...document.querySelectorAll('.account-actions button')].find(item=>item.textContent.trim()==='Sign in');
  button?.click();
}

async function refreshContext(){
  const productResponse=await api('/api/v1/products');
  products=productResponse.ok?await productResponse.json():[];
  await fetchCurrentUser();
  installBuyHandlers();
  renderOrders();
}

function resolveProduct(card,index){
  const title=card.querySelector('h3')?.textContent?.trim();
  return products.find((item,i)=>i===index&&item.name===title)||products.find(item=>item.name===title);
}

function installBuyHandlers(){
  document.querySelectorAll('.grid article').forEach((card,index)=>{
    const button=[...card.querySelectorAll('button')].find(item=>item.textContent.includes('Buy securely'));
    if(!button||button.dataset.orderFlow)return;
    button.dataset.orderFlow='1';
    button.addEventListener('click',async event=>{
      event.preventDefault();
      event.stopImmediatePropagation();
      const authenticatedUser=await fetchCurrentUser();
      if(!authenticatedUser){openSignIn();return}
      const product=resolveProduct(card,index);
      if(product)openCheckout(product);
    },true);
  });
}

function openCheckout(product){
  const backdrop=document.createElement('div');backdrop.className='order-backdrop';
  backdrop.innerHTML=`<section class="order-dialog" role="dialog" aria-modal="true"><button class="order-close" aria-label="Close">×</button><span class="order-kicker">Secure checkout</span><h2>Order ${escapeHtml(product.name)}</h2><p>Complete delivery details before continuing to Paystack. Final pricing is calculated by BloomAI before payment.</p><form class="order-form"><label>Quantity<input name="quantity" type="number" min="1" max="20" value="1" required></label><label>Recipient name<input name="recipient_name" value="${escapeAttr(user.name||'')}" minlength="2" maxlength="120" required></label><label>Phone<input name="phone" minlength="5" maxlength="40" required></label><label class="wide">Delivery address<input name="address_line1" minlength="4" maxlength="240" required></label><label>City<input name="city" minlength="2" maxlength="120" required></label><label>Region / State<input name="region" maxlength="120"></label><label>Postal code<input name="postal_code" maxlength="32"></label><label>Country<input name="country" minlength="2" maxlength="120" required></label><label class="wide">Order note<textarea name="buyer_note" maxlength="1000" rows="3" placeholder="Optional delivery instructions"></textarea></label><div class="order-total wide"><div><span>Subtotal</span><strong data-quote="subtotal">${money(product.currency,product.price)}</strong></div><div><span>Shipping</span><strong data-quote="shipping">Calculating…</strong></div><div><span>Tax</span><strong data-quote="tax">Calculating…</strong></div><div class="order-grand-total"><span>Total</span><strong data-quote="total">${money(product.currency,product.price)}</strong></div></div><div class="order-status wide" role="status"></div><div class="order-actions wide"><button type="button" class="secondary order-cancel">Cancel</button><button class="primary order-submit">Continue to payment</button></div></form></section>`;
  document.body.appendChild(backdrop);
  const close=()=>backdrop.remove();backdrop.querySelector('.order-close').onclick=close;backdrop.querySelector('.order-cancel').onclick=close;
  const quantity=backdrop.querySelector('[name=quantity]');const country=backdrop.querySelector('[name=country]');
  let quoteTimer;
  const updateQuote=()=>{clearTimeout(quoteTimer);quoteTimer=setTimeout(async()=>{const qty=Math.max(1,Number(quantity.value)||1);try{const response=await api('/api/v1/orders/quote',{method:'POST',body:JSON.stringify({product_id:product.id,quantity:qty,country:country.value||''})});const quote=await response.json();if(response.status===401){user=null;close();openSignIn();return}if(!response.ok)throw new Error(quote.detail||'Pricing unavailable');backdrop.querySelector('[data-quote=subtotal]').textContent=money(quote.currency,quote.subtotal);backdrop.querySelector('[data-quote=shipping]').textContent=money(quote.currency,quote.shipping_amount);backdrop.querySelector('[data-quote=tax]').textContent=money(quote.currency,quote.tax_amount);backdrop.querySelector('[data-quote=total]').textContent=money(quote.currency,quote.total)}catch(error){if(backdrop.isConnected)backdrop.querySelector('[data-quote=total]').textContent=error.message}},120)};
  quantity.addEventListener('input',updateQuote);country.addEventListener('input',updateQuote);updateQuote();
  backdrop.querySelector('form').onsubmit=async event=>{event.preventDefault();const status=backdrop.querySelector('.order-status');const submit=backdrop.querySelector('.order-submit');submit.disabled=true;status.textContent='Creating your reserved order…';const data=Object.fromEntries(new FormData(event.currentTarget));data.product_id=product.id;data.quantity=Number(data.quantity);try{const response=await api('/api/v1/orders/checkout',{method:'POST',body:JSON.stringify(data)});const body=await response.json();if(response.status===401){user=null;close();openSignIn();return}if(!response.ok)throw new Error(body.detail||'Order could not be created.');window.location.assign(body.authorization_url)}catch(error){if(backdrop.isConnected){status.textContent=error.message;status.classList.add('error');submit.disabled=false}}};
}

async function renderOrders(){
  document.getElementById('order-center')?.remove();if(!user)return;
  const section=document.createElement('section');section.id='order-center';section.className='order-center';section.innerHTML=`<div class="section-heading"><div><span class="kicker">Marketplace activity</span><h2>${user.role==='vendor'?'Orders & sales':'My orders'}</h2></div><button class="secondary order-refresh">Refresh orders</button></div><div class="order-columns"><div><h3>Purchases</h3><div class="order-list purchases">Loading…</div></div>${user.role==='vendor'?'<div><h3>Sales</h3><div class="order-list sales">Loading…</div></div>':''}</div>`;
  document.querySelector('#market')?.appendChild(section);section.querySelector('.order-refresh').onclick=renderOrders;
  const mine=await api('/api/v1/orders');
  if(mine.status===401){user=null;section.remove();return}
  section.querySelector('.purchases').innerHTML=mine.ok?renderOrderCards(await mine.json(),true):'Unable to load orders.';
  if(user.role==='vendor'){const sales=await api('/api/v1/orders/sales');if(sales.status===401){user=null;section.remove();return}section.querySelector('.sales').innerHTML=sales.ok?renderOrderCards(await sales.json(),false):'Unable to load sales.'}
  section.querySelectorAll('[data-cancel]').forEach(button=>button.onclick=async()=>{const response=await api(`/api/v1/orders/${button.dataset.cancel}/cancel`,{method:'PATCH'});if(response.status===401){user=null;openSignIn();return}if(!response.ok){const body=await response.json();alert(body.detail||'Order could not be cancelled.')}renderOrders()});
  section.querySelectorAll('[data-pay]').forEach(button=>button.onclick=async()=>{const response=await api(`/api/v1/orders/${button.dataset.pay}/pay`,{method:'POST'});const body=await response.json();if(response.status===401){user=null;openSignIn();return}if(response.ok)window.location.assign(body.authorization_url);else alert(body.detail||'Payment could not start.')});
}

function renderOrderCards(items,buyerView){if(!items.length)return '<p class="order-empty">No orders yet.</p>';return items.map(order=>`<article class="order-card"><div><strong>${escapeHtml(order.product_name)}</strong><small>#${order.id} · ${new Date(order.created_at).toLocaleString()}</small></div><span class="order-status-pill ${order.status}">${order.status}</span><p>${order.quantity} × ${money(order.currency,order.unit_price)} · <strong>${money(order.currency,order.total)}</strong></p><p>${buyerView?`Vendor: ${escapeHtml(order.vendor_name)}`:`Customer: ${escapeHtml(order.buyer_name)}`}</p>${order.city||order.country?`<p>Delivery: ${escapeHtml([order.city,order.region,order.country].filter(Boolean).join(', '))}</p>`:''}${buyerView&&['pending','failed'].includes(order.status)?`<div class="order-card-actions"><button class="primary" data-pay="${order.id}">Pay now</button>${order.status==='pending'?`<button class="secondary" data-cancel="${order.id}">Cancel</button>`:''}</div>`:''}</article>`).join('')}
const escapeHtml=value=>String(value??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const escapeAttr=escapeHtml;

const observer=new MutationObserver(()=>installBuyHandlers());observer.observe(document.documentElement,{subtree:true,childList:true});
window.addEventListener('focus',refreshContext);setTimeout(refreshContext,250);
