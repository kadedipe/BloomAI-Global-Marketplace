import './profile-photo.css';

const API=(import.meta.env.VITE_API_URL||'http://localhost:8000').replace(/\/$/,'');
const ALLOWED=['image/jpeg','image/png','image/webp'];
const MAX_BYTES=5_000_000;
let currentUser=null;

async function api(path,options={}){
  const headers={...(options.body instanceof FormData?{}:{'Content-Type':'application/json'}),...(options.headers||{})};
  return fetch(`${API}${path}`,{credentials:'include',...options,headers});
}

function initials(name=''){
  return name.split(/\s+/).filter(Boolean).slice(0,2).map(part=>part[0]?.toUpperCase()).join('')||'U';
}

function renderChipAvatar(user){
  const chip=document.querySelector('.user-chip');
  if(!chip)return;
  const existing=chip.querySelector('[data-profile-avatar]');
  if(existing)existing.remove();
  const svg=chip.querySelector('svg');
  if(svg)svg.style.display='none';
  const avatar=document.createElement(user.avatar_url?'img':'span');
  avatar.dataset.profileAvatar='true';
  avatar.className='profile-avatar-chip';
  if(user.avatar_url){avatar.src=user.avatar_url;avatar.alt=`${user.name} profile photo`;}
  else{avatar.textContent=initials(user.name);avatar.setAttribute('aria-hidden','true');}
  chip.prepend(avatar);
}

function closeDialog(){document.querySelector('[data-profile-photo-dialog]')?.remove()}

function openDialog(){
  if(!currentUser||!['customer','vendor'].includes(currentUser.role))return;
  closeDialog();
  const backdrop=document.createElement('div');
  backdrop.className='profile-photo-backdrop';
  backdrop.dataset.profilePhotoDialog='true';
  const photo=currentUser.avatar_url
    ? `<img class="profile-photo-preview" src="${currentUser.avatar_url}" alt="Current profile photo">`
    : `<div class="profile-photo-placeholder" aria-hidden="true">${initials(currentUser.name)}</div>`;
  backdrop.innerHTML=`
    <section class="profile-photo-dialog" role="dialog" aria-modal="true" aria-labelledby="profile-photo-title">
      <button type="button" class="profile-photo-close" aria-label="Close">×</button>
      <span class="profile-photo-kicker">Account settings</span>
      <h2 id="profile-photo-title">Profile photo</h2>
      <p>Add a photo if you wish. It is optional and can be replaced or removed at any time.</p>
      <div class="profile-photo-current" data-current-photo>${photo}</div>
      <label class="profile-photo-picker">
        <span>${currentUser.avatar_url?'Choose a replacement':'Choose a photo'}</span>
        <small>JPEG, PNG or WebP · up to 5 MB</small>
        <input type="file" accept="image/jpeg,image/png,image/webp" data-photo-input>
      </label>
      <div class="profile-photo-status" data-photo-status aria-live="polite"></div>
      <div class="profile-photo-actions">
        ${currentUser.avatar_url?'<button type="button" class="profile-photo-remove" data-remove-photo>Remove photo</button>':''}
        <button type="button" class="profile-photo-save" data-save-photo disabled>Upload photo</button>
      </div>
    </section>`;

  const input=backdrop.querySelector('[data-photo-input]');
  const save=backdrop.querySelector('[data-save-photo]');
  const status=backdrop.querySelector('[data-photo-status]');
  const current=backdrop.querySelector('[data-current-photo]');
  let selected=null;

  const setStatus=(message,error=false)=>{status.textContent=message;status.className=`profile-photo-status${error?' error':''}`};
  const refreshPhoto=(user)=>{
    current.innerHTML=user.avatar_url
      ? `<img class="profile-photo-preview" src="${user.avatar_url}" alt="Current profile photo">`
      : `<div class="profile-photo-placeholder" aria-hidden="true">${initials(user.name)}</div>`;
    renderChipAvatar(user);
  };

  input.addEventListener('change',()=>{
    selected=input.files?.[0]||null;
    setStatus('');
    if(!selected){save.disabled=true;return;}
    if(!ALLOWED.includes(selected.type)){setStatus('Please choose a JPEG, PNG or WebP image.',true);selected=null;save.disabled=true;return;}
    if(selected.size>MAX_BYTES){setStatus('The photo must be 5 MB or smaller.',true);selected=null;save.disabled=true;return;}
    const previewUrl=URL.createObjectURL(selected);
    current.innerHTML=`<img class="profile-photo-preview" src="${previewUrl}" alt="Selected profile photo preview">`;
    save.disabled=false;
  });

  save.addEventListener('click',async()=>{
    if(!selected)return;
    save.disabled=true;setStatus('Uploading…');
    const body=new FormData();body.append('image',selected);
    try{
      const response=await api('/api/v1/notifications/profile-photo',{method:'POST',body});
      const data=await response.json().catch(()=>({}));
      if(!response.ok)throw new Error(data.detail||'Profile photo could not be uploaded.');
      currentUser=data;refreshPhoto(data);selected=null;input.value='';setStatus('Profile photo updated.');
    }catch(error){setStatus(error.message||'Profile photo could not be uploaded.',true);save.disabled=false;}
  });

  backdrop.querySelector('[data-remove-photo]')?.addEventListener('click',async(event)=>{
    event.currentTarget.disabled=true;setStatus('Removing…');
    try{
      const response=await api('/api/v1/notifications/profile-photo',{method:'DELETE'});
      const data=await response.json().catch(()=>({}));
      if(!response.ok)throw new Error(data.detail||'Profile photo could not be removed.');
      currentUser=data;refreshPhoto(data);setStatus('Profile photo removed.');event.currentTarget.remove();
    }catch(error){setStatus(error.message||'Profile photo could not be removed.',true);event.currentTarget.disabled=false;}
  });

  backdrop.querySelector('.profile-photo-close').addEventListener('click',closeDialog);
  backdrop.addEventListener('mousedown',event=>{if(event.target===backdrop)closeDialog()});
  backdrop.addEventListener('keydown',event=>{if(event.key==='Escape')closeDialog()});
  document.body.appendChild(backdrop);
  input.focus();
}

async function syncProfileSetting(){
  const actions=document.querySelector('.account-actions');
  const chip=document.querySelector('.user-chip');
  if(!actions||!chip)return false;
  try{
    const response=await api('/api/v1/auth/me');
    if(!response.ok)return false;
    const user=await response.json();
    if(!['customer','vendor'].includes(user.role))return false;
    currentUser=user;
    renderChipAvatar(user);
    if(!actions.querySelector('[data-profile-photo-button]')){
      const button=document.createElement('button');
      button.type='button';
      button.className='profile-photo-trigger';
      button.dataset.profilePhotoButton='true';
      button.textContent='Profile photo';
      button.addEventListener('click',openDialog);
      actions.insertBefore(button,actions.querySelector('.ghost'));
    }
    return true;
  }catch{return false;}
}

const observer=new MutationObserver(()=>{syncProfileSetting()});
observer.observe(document.documentElement,{childList:true,subtree:true});
syncProfileSetting();
