const API=(import.meta.env.VITE_API_URL||'http://localhost:8000').replace(/\/$/,'');

function el(tag,attrs={},text=''){
  const node=document.createElement(tag);
  Object.entries(attrs).forEach(([key,value])=>{
    if(key==='class')node.className=value;
    else if(key==='type')node.type=value;
    else node.setAttribute(key,value);
  });
  if(text)node.textContent=text;
  return node;
}

function supportError(err,fallback='BloomAI Support is temporarily unavailable. Please try again.'){
  if(err instanceof TypeError)return fallback;
  const message=String(err?.message||'').trim();
  return message&&message!=='Failed to fetch'?message:fallback;
}

const style=document.createElement('style');
style.textContent=`
.bloom-support-launch{position:fixed;right:22px;bottom:22px;z-index:9998;border:0;border-radius:999px;padding:13px 18px;background:#184c35;color:white;font-weight:700;box-shadow:0 12px 30px rgba(0,0,0,.2);cursor:pointer}
.bloom-support-panel{position:fixed;right:22px;bottom:82px;width:min(390px,calc(100vw - 28px));max-height:70vh;z-index:9999;background:white;border:1px solid #d8e3dc;border-radius:18px;box-shadow:0 18px 50px rgba(0,0,0,.22);display:none;overflow:hidden;font:14px/1.45 system-ui,sans-serif}
.bloom-support-panel.open{display:flex;flex-direction:column}.bloom-support-head{padding:16px 18px;background:#f2f8f4;display:flex;justify-content:space-between;gap:12px;align-items:center}.bloom-support-head strong{display:block;font-size:16px}.bloom-support-head small{color:#5c6d63}.bloom-support-close{border:0;background:transparent;font-size:22px;cursor:pointer}.bloom-support-log{padding:16px;overflow:auto;display:flex;flex-direction:column;gap:10px;min-height:180px}.bloom-support-msg{padding:10px 12px;border-radius:12px;white-space:pre-wrap}.bloom-support-msg.bot{background:#f4f6f5}.bloom-support-msg.user{background:#e7f3eb;align-self:flex-end;max-width:88%}.bloom-support-actions{padding:0 16px 10px}.bloom-support-escalate{border:1px solid #a33;background:white;color:#8c2323;border-radius:10px;padding:8px 10px;cursor:pointer}.bloom-support-form{display:flex;gap:8px;padding:12px;border-top:1px solid #e5ebe7}.bloom-support-form textarea{flex:1;resize:none;min-height:48px;border:1px solid #cfd9d2;border-radius:10px;padding:9px}.bloom-support-form button{border:0;border-radius:10px;background:#184c35;color:white;padding:0 14px;font-weight:700;cursor:pointer}.bloom-support-note{padding:0 16px 12px;color:#667085;font-size:12px}
`;
document.head.appendChild(style);

const launch=el('button',{class:'bloom-support-launch',type:'button','aria-label':'Open BloomAI Support'},'Support');
const panel=el('section',{class:'bloom-support-panel','aria-label':'BloomAI Support Assistant'});
const head=el('div',{class:'bloom-support-head'});
const headText=el('div');headText.append(el('strong',{},'BloomAI Support'),el('small',{},'AI-assisted customer & vendor help'));
const close=el('button',{class:'bloom-support-close',type:'button','aria-label':'Close support'},'×');head.append(headText,close);
const log=el('div',{class:'bloom-support-log'});
const actions=el('div',{class:'bloom-support-actions'});
const note=el('div',{class:'bloom-support-note'},'Never send passwords, OTPs, full card numbers or API keys. Critical issues can be escalated to an administrator.');
const form=el('form',{class:'bloom-support-form'});const input=el('textarea',{placeholder:'Describe your order, payment, refund, delivery or account issue…','aria-label':'Support message'});const send=el('button',{type:'submit'},'Send');form.append(input,send);
panel.append(head,log,actions,note,form);document.body.append(launch,panel);

let lastRequest=null;
function addMessage(kind,text){const msg=el('div',{class:`bloom-support-msg ${kind}`},text);log.append(msg);log.scrollTop=log.scrollHeight;}
function clearEscalate(){actions.innerHTML='';}
function showEscalate(payload){clearEscalate();const button=el('button',{class:'bloom-support-escalate',type:'button'},'Escalate to administrator');button.addEventListener('click',async()=>{
  button.disabled=true;button.textContent='Escalating…';
  try{
    const r=await fetch(`${API}/api/v1/support/escalate`,{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});
    if(!r.ok){const d=await r.json().catch(()=>({}));throw new Error(d.detail||'Escalation failed');}
    const data=await r.json();addMessage('bot',data.admins_notified?`Escalated. ${data.admins_notified} administrator notification(s) were created.`:'Escalated. A support record was created, but no administrator notification recipient was available.');clearEscalate();
  }catch(err){addMessage('bot',supportError(err,'Unable to reach BloomAI Support to escalate this issue. Please try again.'));button.disabled=false;button.textContent='Escalate to administrator';}
});actions.append(button);}

async function checkAccess(){
  try{const r=await fetch(`${API}/api/v1/auth/me`,{credentials:'include'});if(!r.ok)return null;const me=await r.json();return ['customer','vendor'].includes(me.role)?me:null;}catch{return null;}
}

launch.addEventListener('click',async()=>{
  panel.classList.toggle('open');
  if(panel.classList.contains('open')&&!log.childElementCount){const me=await checkAccess();if(!me)addMessage('bot','Please sign in as a BloomAI customer or vendor to use the support assistant.');else addMessage('bot',`Hi ${me.name}. I can help with orders, payments, refunds, delivery, listings and account issues. What happened?`);}
});
close.addEventListener('click',()=>panel.classList.remove('open'));
form.addEventListener('submit',async event=>{
  event.preventDefault();const message=input.value.trim();if(!message)return;input.value='';clearEscalate();addMessage('user',message);send.disabled=true;
  try{
    const r=await fetch(`${API}/api/v1/support/assistant`,{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({message})});
    if(!r.ok){const d=await r.json().catch(()=>({}));throw new Error(d.detail||'Support assistant is unavailable');}
    const data=await r.json();addMessage('bot',data.reply);lastRequest={message,category:data.category,order_id:data.order_id};if(data.escalation_recommended)showEscalate(lastRequest);else{const button=el('button',{class:'bloom-support-escalate',type:'button'},'Need human support?');button.addEventListener('click',()=>showEscalate(lastRequest));actions.append(button);}
  }catch(err){addMessage('bot',supportError(err));}
  finally{send.disabled=false;input.focus();}
});
