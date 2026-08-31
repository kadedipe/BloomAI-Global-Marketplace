import './admin-participant-editor.css';

const API=(import.meta.env.VITE_API_URL||'http://localhost:8000').replace(/\/$/,'');
const sizeOptions=['unclassified','individual','micro','small','mid_size','large','enterprise'];
const categoryOptions=['unclassified','individual_consumer','hobbyist_collector','florist_landscaper','professional_grower','botanical_garden','nursery_garden_center','farm_agriculture_business','small_business','mid_size_business','large_enterprise','government_agency','university','research_institution','nonprofit_ngo','conservation_organization','other'];
const pretty=value=>(value||'').replaceAll('_',' ').replace(/\b\w/g,m=>m.toUpperCase());

async function api(path,options={}){
  const headers={'Content-Type':'application/json',...(options.headers||{})};
  return fetch(`${API}${path}`,{credentials:'include',...options,headers});
}

function field(label,name,type='text',placeholder=''){
  const wrapper=document.createElement('label');
  wrapper.className='participant-editor-field';
  const text=document.createElement('span');
  text.textContent=label;
  const input=document.createElement('input');
  input.name=name;
  input.type=type;
  input.placeholder=placeholder;
  wrapper.append(text,input);
  return wrapper;
}

function selectField(label,name,options){
  const wrapper=document.createElement('label');
  wrapper.className='participant-editor-field';
  const text=document.createElement('span');
  text.textContent=label;
  const select=document.createElement('select');
  select.name=name;
  for(const option of options){
    const node=document.createElement('option');
    node.value=option;
    node.textContent=pretty(option);
    select.append(node);
  }
  wrapper.append(text,select);
  return wrapper;
}

function optional(value){
  const cleaned=String(value??'').trim();
  return cleaned||null;
}

async function findParticipant(email){
  const responses=await Promise.all([
    api('/api/v1/admin/participants?role=vendor&limit=500'),
    api('/api/v1/admin/participants?role=customer&limit=500'),
  ]);
  if(responses.some(response=>!response.ok))throw new Error('Participant details could not be loaded.');
  const payloads=await Promise.all(responses.map(response=>response.json()));
  return payloads.flatMap(payload=>payload.items||[]).find(person=>person.email===email);
}

function openEditor(person){
  document.querySelector('.participant-editor-backdrop')?.remove();

  const backdrop=document.createElement('div');
  backdrop.className='participant-editor-backdrop';
  backdrop.setAttribute('role','presentation');

  const dialog=document.createElement('section');
  dialog.className='participant-editor-dialog';
  dialog.setAttribute('role','dialog');
  dialog.setAttribute('aria-modal','true');
  dialog.setAttribute('aria-labelledby','participant-editor-title');

  const header=document.createElement('div');
  header.className='participant-editor-head';
  const heading=document.createElement('div');
  const title=document.createElement('h2');
  title.id='participant-editor-title';
  title.textContent='Edit participant profile';
  const identity=document.createElement('p');
  identity.textContent=`${person.name} · ${pretty(person.role)} · ${person.email}`;
  heading.append(title,identity);
  const close=document.createElement('button');
  close.type='button';
  close.className='participant-editor-close';
  close.setAttribute('aria-label','Close profile editor');
  close.textContent='×';
  header.append(heading,close);

  const note=document.createElement('p');
  note.className='participant-editor-note';
  note.textContent='Use verified participant information. Leave location and coordinate fields blank when they are not known.';

  const form=document.createElement('form');
  form.className='participant-editor-form';

  const organizationName=field('Organization name','organization_name');
  const organizationSize=selectField('Organization size','organization_size',sizeOptions);
  const category=selectField('Category','category',categoryOptions);
  const industry=field('Industry / sector','industry');
  const country=field('Country','country');
  const address=field('Street / address line','address_line1');
  const city=field('City','city');
  const region=field('State / province / region','region');
  const postal=field('Postal code','postal_code');
  const latitude=field('Latitude','latitude','number','-90 to 90');
  latitude.querySelector('input').step='any';
  latitude.querySelector('input').min='-90';
  latitude.querySelector('input').max='90';
  const longitude=field('Longitude','longitude','number','-180 to 180');
  longitude.querySelector('input').step='any';
  longitude.querySelector('input').min='-180';
  longitude.querySelector('input').max='180';
  const source=field('Geocoding source','geocoding_source','text','verified source');

  form.append(organizationName,organizationSize,category,industry,country,address,city,region,postal,latitude,longitude,source);

  const status=document.createElement('p');
  status.className='participant-editor-status';
  status.setAttribute('aria-live','polite');

  const actions=document.createElement('div');
  actions.className='participant-editor-actions';
  const cancel=document.createElement('button');
  cancel.type='button';
  cancel.className='participant-editor-cancel';
  cancel.textContent='Cancel';
  const save=document.createElement('button');
  save.type='submit';
  save.className='participant-editor-save';
  save.textContent='Save profile';
  actions.append(cancel,save);
  form.append(status,actions);

  dialog.append(header,note,form);
  backdrop.append(dialog);
  document.body.append(backdrop);

  const defaultSize=person.organization_size==='unclassified'?'individual':person.organization_size;
  const defaultCategory=person.category==='unclassified'
    ?(person.role==='vendor'?'small_business':'individual_consumer')
    :person.category;

  const values={
    organization_name:person.organization_name||'',
    organization_size:defaultSize,
    category:defaultCategory,
    industry:person.industry||'',
    country:person.country||'',
    address_line1:person.address_line1||'',
    city:person.city||'',
    region:person.region||'',
    postal_code:person.postal_code||'',
    latitude:person.latitude??'',
    longitude:person.longitude??'',
    geocoding_source:person.geocoding_source||'',
  };
  for(const [name,value] of Object.entries(values))form.elements[name].value=value;

  const dismiss=()=>backdrop.remove();
  close.addEventListener('click',dismiss);
  cancel.addEventListener('click',dismiss);
  backdrop.addEventListener('click',event=>{if(event.target===backdrop)dismiss();});

  form.addEventListener('submit',async event=>{
    event.preventDefault();
    status.className='participant-editor-status';
    status.textContent='';
    const latText=form.elements.latitude.value.trim();
    const lonText=form.elements.longitude.value.trim();
    if(Boolean(latText)!==Boolean(lonText)){
      status.textContent='Latitude and longitude must be provided together.';
      return;
    }
    const latitudeValue=latText===''?null:Number(latText);
    const longitudeValue=lonText===''?null:Number(lonText);
    if(latitudeValue!==null&&(!Number.isFinite(latitudeValue)||latitudeValue<-90||latitudeValue>90)){
      status.textContent='Latitude must be between -90 and 90.';
      return;
    }
    if(longitudeValue!==null&&(!Number.isFinite(longitudeValue)||longitudeValue<-180||longitudeValue>180)){
      status.textContent='Longitude must be between -180 and 180.';
      return;
    }

    const payload={
      organization_name:optional(form.elements.organization_name.value),
      organization_size:form.elements.organization_size.value,
      category:form.elements.category.value,
      industry:optional(form.elements.industry.value),
      country:optional(form.elements.country.value),
      address_line1:optional(form.elements.address_line1.value),
      city:optional(form.elements.city.value),
      region:optional(form.elements.region.value),
      postal_code:optional(form.elements.postal_code.value),
      latitude:latitudeValue,
      longitude:longitudeValue,
      geocoding_source:latitudeValue===null?null:optional(form.elements.geocoding_source.value),
    };

    save.disabled=true;
    save.textContent='Saving…';
    try{
      const response=await api(`/api/v1/admin/participants/${person.user_id}/segment`,{
        method:'PATCH',
        body:JSON.stringify(payload),
      });
      if(!response.ok){
        const detail=await response.json().catch(()=>null);
        throw new Error(detail?.detail||'Could not update this participant.');
      }
      status.className='participant-editor-status success';
      status.textContent='Profile saved. Refreshing marketplace analytics…';
      window.setTimeout(()=>window.location.reload(),350);
    }catch(error){
      status.textContent=error.message;
      save.disabled=false;
      save.textContent='Save profile';
    }
  });

  form.elements.organization_name.focus();
}

export function installParticipantProfileEditor(){
  document.addEventListener('click',async event=>{
    const button=event.target.closest('button.segment');
    if(!button||button.textContent.trim()!=='Edit profile')return;
    event.preventDefault();
    event.stopPropagation();
    event.stopImmediatePropagation();

    const row=button.closest('tr');
    const email=row?.querySelector('td:first-child small')?.textContent?.trim();
    if(!email){
      window.alert('Participant identity could not be resolved.');
      return;
    }

    button.disabled=true;
    const previous=button.textContent;
    button.textContent='Loading…';
    try{
      const person=await findParticipant(email);
      if(!person)throw new Error('Participant could not be found.');
      openEditor(person);
    }catch(error){
      window.alert(error.message);
    }finally{
      button.disabled=false;
      button.textContent=previous;
    }
  },true);
}
