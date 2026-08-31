import './admin-test-notifications.css';

const API=(import.meta.env.VITE_API_URL||'http://localhost:8000').replace(/\/$/,'');
const roles=[
  ['customer','Customers'],
  ['vendor','Vendors'],
  ['admin','Administrators'],
];

function escapeText(value){return String(value??'')}

async function api(path,options={}){
  const headers={'Content-Type':'application/json',...(options.headers||{})};
  return fetch(`${API}${path}`,{credentials:'include',...options,headers});
}

function openDialog(){
  if(document.querySelector('[data-admin-notification-test]'))return;

  const backdrop=document.createElement('div');
  backdrop.className='notification-test-backdrop';
  backdrop.dataset.adminNotificationTest='true';
  backdrop.innerHTML=`
    <section class="notification-test-dialog" role="dialog" aria-modal="true" aria-labelledby="notification-test-title">
      <button class="notification-test-close" type="button" aria-label="Close">×</button>
      <span class="notification-test-kicker">Production-safe verification</span>
      <h2 id="notification-test-title">Send test notification</h2>
      <p>Send a notification without creating an order, payment, or analytics event.</p>
      <label>Recipient role
        <select data-role>
          ${roles.map(([value,label])=>`<option value="${value}">${label}</option>`).join('')}
        </select>
      </label>
      <div class="notification-test-note">Every account in the selected role will receive the same test notification.</div>
      <div class="notification-test-status" data-status aria-live="polite"></div>
      <div class="notification-test-actions">
        <button type="button" class="notification-test-cancel">Cancel</button>
        <button type="button" class="notification-test-send">Send test notification</button>
      </div>
    </section>`;

  const close=()=>backdrop.remove();
  backdrop.addEventListener('mousedown',event=>{if(event.target===backdrop)close()});
  backdrop.querySelector('.notification-test-close').addEventListener('click',close);
  backdrop.querySelector('.notification-test-cancel').addEventListener('click',close);
  backdrop.addEventListener('keydown',event=>{if(event.key==='Escape')close()});

  const send=backdrop.querySelector('.notification-test-send');
  const select=backdrop.querySelector('[data-role]');
  const status=backdrop.querySelector('[data-status]');
  send.addEventListener('click',async()=>{
    const targetRole=select.value;
    send.disabled=true;
    status.className='notification-test-status';
    status.textContent='Sending…';
    try{
      const response=await api('/api/v1/notifications/test',{
        method:'POST',
        body:JSON.stringify({target_role:targetRole}),
      });
      const body=await response.json().catch(()=>({}));
      if(!response.ok)throw new Error(body.detail||'The test notification could not be sent.');
      status.className='notification-test-status success';
      status.textContent=`Delivered to ${escapeText(body.delivered)} ${escapeText(body.target_role)} account${body.delivered===1?'':'s'}.`;
    }catch(error){
      status.className='notification-test-status error';
      status.textContent=error.message||'The test notification could not be sent.';
    }finally{
      send.disabled=false;
    }
  });

  document.body.appendChild(backdrop);
  select.focus();
}

export function installAdminNotificationTester(){
  const mount=()=>{
    const actions=document.querySelector('.header-actions');
    if(!actions||actions.querySelector('[data-notification-test-button]'))return false;
    const button=document.createElement('button');
    button.type='button';
    button.dataset.notificationTestButton='true';
    button.className='notification-test-trigger';
    button.textContent='Test notification';
    button.addEventListener('click',openDialog);
    actions.prepend(button);
    return true;
  };

  if(mount())return;
  const observer=new MutationObserver(()=>{if(mount())observer.disconnect()});
  observer.observe(document.documentElement,{childList:true,subtree:true});
}
