const API=(import.meta.env.VITE_API_URL||'http://localhost:8000').replace(/\/$/,'');

const style=document.createElement('style');
style.textContent=`
#support-cases-admin{max-width:1180px;margin:28px auto;padding:0 20px;font:14px/1.45 system-ui,sans-serif}#support-cases-admin h2{margin:0 0 6px}#support-cases-admin .muted{color:#667085}.support-case-toolbar{display:flex;gap:8px;align-items:center;margin:14px 0}.support-case-toolbar select,.support-case-toolbar button,.support-case-card textarea,.support-case-card select,.support-case-card button{border:1px solid #cfd9d2;border-radius:8px;padding:8px;background:white}.support-case-list{display:grid;gap:12px}.support-case-card{border:1px solid #d8e3dc;border-radius:14px;padding:14px;background:#fff}.support-case-meta{display:flex;gap:10px;flex-wrap:wrap;color:#667085;font-size:12px}.support-case-message{padding:8px 10px;background:#f4f6f5;border-radius:8px;margin-top:8px;white-space:pre-wrap}.support-case-message.admin{background:#e7f3eb}.support-case-actions{display:flex;gap:8px;flex-wrap:wrap;margin-top:10px}.support-case-card textarea{width:100%;box-sizing:border-box;min-height:70px;margin-top:10px}.support-case-card button{cursor:pointer}.support-case-card button.primary{background:#184c35;color:#fff;border-color:#184c35}
`;
document.head.appendChild(style);

const section=document.createElement('section');section.id='support-cases-admin';
section.innerHTML=`<h2>Support inbox</h2><div class="muted">Persistent customer and vendor support cases with notification-driven follow-up.</div><div class="support-case-toolbar"><select id="support-case-filter"><option value="">All statuses</option><option value="open">Open</option><option value="in_progress">In progress</option><option value="waiting_on_user">Waiting on user</option><option value="resolved">Resolved</option><option value="closed">Closed</option></select><button id="support-case-refresh" type="button">Refresh</button></div><div id="support-case-list" class="support-case-list"></div>`;
document.body.append(section);

const list=section.querySelector('#support-case-list');
const filter=section.querySelector('#support-case-filter');
const refresh=section.querySelector('#support-case-refresh');

async function api(path,options={}){
  const response=await fetch(`${API}/api/v1${path}`,{credentials:'include',...options,headers:{'Content-Type':'application/json',...(options.headers||{})}});
  if(!response.ok){const data=await response.json().catch(()=>({}));throw new Error(data.detail||`Request failed (${response.status})`);}
  return response.json();
}

function escapeText(value){const div=document.createElement('div');div.textContent=String(value??'');return div.innerHTML;}

function renderCase(item){
  const card=document.createElement('article');card.className='support-case-card';card.id=`support-case-${item.id}`;
  const messages=(item.messages||[]).map(message=>`<div class="support-case-message ${message.author_role==='admin'?'admin':''}"><strong>${escapeText(message.author_role)}</strong> · ${new Date(message.created_at).toLocaleString()}<br>${escapeText(message.body)}</div>`).join('');
  card.innerHTML=`<strong>Case #${item.id} · ${escapeText(item.subject)}</strong><div class="support-case-meta"><span>${escapeText(item.user_name)} (${escapeText(item.user_email)})</span><span>Category: ${escapeText(item.category)}</span><span>Priority: ${escapeText(item.priority)}</span><span>Status: ${escapeText(item.status)}</span>${item.order_id?`<span>Order #${item.order_id}</span>`:''}</div>${messages}<textarea maxlength="4000" placeholder="Reply to this support case"></textarea><div class="support-case-actions"><button class="primary" data-action="reply" type="button">Reply</button><button data-action="assign" type="button">Assign to me</button><select data-action="status"><option value="open">Open</option><option value="in_progress">In progress</option><option value="waiting_on_user">Waiting on user</option><option value="resolved">Resolved</option><option value="closed">Closed</option></select><button data-action="update" type="button">Update status</button></div>`;
  card.querySelector('[data-action="status"]').value=item.status;
  card.querySelector('[data-action="reply"]').addEventListener('click',async()=>{
    const textarea=card.querySelector('textarea');const message=textarea.value.trim();if(!message)return;
    try{await api(`/admin/support/cases/${item.id}/reply`,{method:'POST',body:JSON.stringify({message})});textarea.value='';await load();}catch(err){alert(err.message);}
  });
  card.querySelector('[data-action="assign"]').addEventListener('click',async()=>{try{await api(`/admin/support/cases/${item.id}`,{method:'PATCH',body:JSON.stringify({assign_to_me:true})});await load();}catch(err){alert(err.message);}});
  card.querySelector('[data-action="update"]').addEventListener('click',async()=>{const statusValue=card.querySelector('[data-action="status"]').value;try{await api(`/admin/support/cases/${item.id}`,{method:'PATCH',body:JSON.stringify({status:statusValue})});await load();}catch(err){alert(err.message);}});
  return card;
}

async function load(){
  list.textContent='Loading support cases…';
  try{const suffix=filter.value?`?status=${encodeURIComponent(filter.value)}`:'';const data=await api(`/admin/support/cases${suffix}`);list.innerHTML='';if(!data.items?.length){list.textContent='No support cases match this filter.';return;}data.items.forEach(item=>list.append(renderCase(item)));if(location.hash.startsWith('#support-case-'))document.querySelector(location.hash)?.scrollIntoView({behavior:'smooth'});}catch(err){list.textContent=err.message;}
}

refresh.addEventListener('click',load);filter.addEventListener('change',load);load();
