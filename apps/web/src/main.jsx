import React, {useEffect, useState} from 'react';
import {createRoot} from 'react-dom/client';
import {
  CreditCard, Edit3, Globe2, Leaf, LoaderCircle, LogOut, Plus, Search, ShieldCheck,
  Sparkles, Store, Trash2, Upload, UserRound, X
} from 'lucide-react';
import './styles.css';
import './enhancements.css';
import {normalizePredictions, readError} from './utils.js';

const API=(import.meta.env.VITE_API_URL||'http://localhost:8000').replace(/\/$/,'');
const AI_API=(import.meta.env.VITE_AI_API_URL||'http://localhost:8001').replace(/\/$/,'');

async function api(path,options={}){
  const headers={...(options.body instanceof FormData?{}:{'Content-Type':'application/json'}),...options.headers};
  return fetch(`${API}${path}`,{credentials:'include',...options,headers});
}

const emptyAuth={name:'',email:'',password:'',role:'customer'};
const emptyProduct={name:'',description:'',price:'',currency:'NGN',image_url:'',image_public_id:''};
const FALLBACK_IMAGE='/product-placeholder.svg';

function AuthModal({mode,setMode,onClose,onAuthenticated}){
  const [form,setForm]=useState(emptyAuth);
  const [status,setStatus]=useState('idle');
  const [error,setError]=useState('');
  const registering=mode==='register';

  function update(event){setForm(current=>({...current,[event.target.name]:event.target.value}))}

  async function submit(event){
    event.preventDefault(); setError('');
    if(registering&&form.name.trim().length<2){setError('Your name must contain at least two characters.');return}
    if(form.password.length<10){setError('Your password must contain at least 10 characters.');return}
    setStatus('loading');
    try{
      if(registering){
        const registration=await api('/api/v1/auth/register',{
          method:'POST',
          body:JSON.stringify({name:form.name.trim(),email:form.email.trim(),password:form.password,role:form.role})
        });
        if(!registration.ok)throw new Error(await readError(registration,'Registration failed.'));
      }
      const login=await api('/api/v1/auth/login',{
        method:'POST',
        body:JSON.stringify({email:form.email.trim(),password:form.password})
      });
      if(!login.ok)throw new Error(await readError(login,'Sign in failed.'));
      const profile=await api('/api/v1/auth/me');
      if(!profile.ok)throw new Error('Your session could not be verified.');
      onAuthenticated(await profile.json());
      setForm(emptyAuth); onClose();
    }catch(reason){setError(reason.message||'Authentication is temporarily unavailable.')}
    finally{setStatus('idle')}
  }

  return <div className="modal-backdrop" role="presentation" onMouseDown={event=>event.target===event.currentTarget&&onClose()}>
    <section className="modal" role="dialog" aria-modal="true" aria-labelledby="auth-title">
      <button className="icon-button close" onClick={onClose} aria-label="Close"><X/></button>
      <div className="modal-mark"><Leaf/></div>
      <span className="kicker">BloomAI account</span>
      <h2 id="auth-title">{registering?'Join the marketplace':'Welcome back'}</h2>
      <p>{registering?'Create a buyer or vendor profile in a few steps.':'Sign in to manage your marketplace activity.'}</p>
      <div className="tabs">
        <button className={!registering?'active':''} onClick={()=>{setMode('login');setError('')}}>Sign in</button>
        <button className={registering?'active':''} onClick={()=>{setMode('register');setError('')}}>Register</button>
      </div>
      <form className="stack-form" onSubmit={submit}>
        {registering&&<label>Full name<input name="name" value={form.name} onChange={update} minLength="2" maxLength="120" autoComplete="name" required/></label>}
        <label>Email address<input name="email" value={form.email} onChange={update} type="email" autoComplete="email" required/></label>
        <label>Password<input name="password" value={form.password} onChange={update} type="password" minLength="10" maxLength="128" autoComplete={registering?'new-password':'current-password'} required/><small>At least 10 characters</small></label>
        {registering&&<label>Account type<select name="role" value={form.role} onChange={update}><option value="customer">Customer</option><option value="vendor">Vendor</option></select></label>}
        {error&&<div className="form-error" role="alert">{error}</div>}
        <button className="primary form-submit" disabled={status==='loading'}>
          {status==='loading'?<><LoaderCircle className="spin"/>Please wait…</>:registering?'Create account':'Sign in'}
        </button>
      </form>
      <p className="session-note"><ShieldCheck/> Your session is stored in a secure HttpOnly cookie, not browser storage.</p>
    </section>
  </div>
}

function VendorDashboard({user,editing,onSaved,onCancel,onSessionExpired}){
  const [form,setForm]=useState(emptyProduct); const [image,setImage]=useState(null); const [preview,setPreview]=useState('');
  const [status,setStatus]=useState('idle'); const [error,setError]=useState(''); const [message,setMessage]=useState('');
  function update(event){setForm(current=>({...current,[event.target.name]:event.target.value}))}
  useEffect(()=>{setForm(editing?{name:editing.name,description:editing.description,price:editing.price,currency:editing.currency,image_url:editing.image_url||'',image_public_id:editing.image_public_id||''}:emptyProduct);setImage(null);setPreview(editing?.image_url||'')},[editing]);

  async function submit(event){
    event.preventDefault();setError('');setMessage('');if(Number(form.price)<=0){setError('Enter a price greater than zero.');return}setStatus('loading');
    let media={image_url:form.image_url||null,image_public_id:form.image_public_id||null};
    if(image){const body=new FormData();body.append('image',image);const uploaded=await api('/api/v1/product-images',{method:'POST',body});if(!uploaded.ok){setError(await readError(uploaded,'Image upload failed.'));setStatus('idle');return}media=await uploaded.json()}
    const response=await api(editing?`/api/v1/products/${editing.id}`:'/api/v1/products',{method:editing?'PATCH':'POST',body:JSON.stringify({...form,...media,name:form.name.trim(),description:form.description.trim(),price:Number(form.price),currency:form.currency.toUpperCase()})});
    if(response.status===401){onSessionExpired();setStatus('idle');return}if(!response.ok){setError(await readError(response,'The product could not be saved.'));setStatus('idle');return}
    const product=await response.json();onSaved(product);setForm(emptyProduct);setImage(null);setPreview('');setMessage(editing?'Product updated successfully.':'Product published successfully.');setStatus('idle');
  }

  return <section className="vendor-panel" aria-labelledby="vendor-heading"><div className="vendor-copy"><span className="kicker">Vendor dashboard</span><h3 id="vendor-heading">{editing?'Edit botanical listing':'Publish a botanical listing'}</h3><p>Signed in as {user.name}. Product changes appear immediately.</p></div><form className="product-form" onSubmit={submit}>
    <label>Product name<input name="name" value={form.name} onChange={update} minLength="2" maxLength="160" required/></label><label>Price<div className="price-row"><select name="currency" value={form.currency} onChange={update}><option>NGN</option><option>USD</option><option>EUR</option><option>GBP</option><option>UGX</option></select><input name="price" value={form.price} onChange={update} type="number" min="0.01" step="0.01" required/></div></label>
    <label className="wide">Description<textarea name="description" value={form.description} onChange={update} maxLength="5000" rows="3"/></label>
    <label className="wide upload-control"><Upload/><span>{image?.name||(editing?.image_url?'Replace product image':'Choose a JPEG, PNG or WebP image')}</span><input className="visually-hidden" type="file" accept="image/jpeg,image/png,image/webp" onChange={event=>{const next=event.target.files?.[0]||null;setImage(next);if(next)setPreview(URL.createObjectURL(next))}}/></label>
    {preview&&<img className="product-preview wide" src={preview} alt="Product preview" onError={event=>{event.currentTarget.src=FALLBACK_IMAGE}}/>}{error&&<div className="form-error wide" role="alert">{error}</div>}{message&&<div className="form-success wide" role="status">{message}</div>}
    <div className="form-actions wide"><button className="primary product-submit" disabled={status==='loading'}>{status==='loading'?<><LoaderCircle className="spin"/>Saving…</>:<><Plus/>{editing?'Save changes':'Publish product'}</>}</button>{editing&&<button type="button" className="secondary" onClick={onCancel}>Cancel</button>}</div>
  </form></section>
}

function ProductCard({product,user,onEdit,onDeleted}){
  const [busy,setBusy]=useState(false);const owns=user&&(user.role==='admin'||product.vendor_id===user.id);
  async function remove(){if(!window.confirm(`Delete ${product.name}? This cannot be undone.`))return;setBusy(true);const response=await api(`/api/v1/products/${product.id}`,{method:'DELETE'});if(response.ok)onDeleted(product.id);setBusy(false)}
  return <article><div className="image"><img src={product.image_url||FALLBACK_IMAGE} alt={product.name} loading="lazy" onError={event=>{event.currentTarget.onerror=null;event.currentTarget.src=FALLBACK_IMAGE}}/></div><h3>{product.name}</h3><p>{product.description}</p><strong>{product.currency} {Number(product.price).toFixed(2)}</strong><div className="card-actions">{owns?<><button className="secondary" onClick={()=>onEdit(product)}><Edit3/>Edit</button><button className="danger" disabled={busy} onClick={remove}><Trash2/>Delete</button></>:<button className="primary"><CreditCard/>Buy securely</button>}</div></article>
}

function App(){
  const [products,setProducts]=useState([]); const [marketState,setMarketState]=useState('loading');
  const [user,setUser]=useState(null); const [sessionState,setSessionState]=useState('loading');
  const [authOpen,setAuthOpen]=useState(false); const [authMode,setAuthMode]=useState('login');
  const [image,setImage]=useState(null); const [aiState,setAiState]=useState('idle');
  const [predictions,setPredictions]=useState([]); const [aiError,setAiError]=useState('');
  const [editing,setEditing]=useState(null); const [paymentMessage,setPaymentMessage]=useState('');

  async function loadProducts(){
    setMarketState('loading');
    try{const response=await api('/api/v1/products');if(!response.ok)throw Error();setProducts(await response.json());setMarketState('ready')}
    catch{setMarketState('offline')}
  }

  useEffect(()=>{
    loadProducts();
    api('/api/v1/auth/me').then(async response=>{
      if(response.ok)setUser(await response.json());
      setSessionState('ready');
    }).catch(()=>setSessionState('ready'));
  },[]);

  useEffect(()=>{const reference=new URLSearchParams(window.location.search).get('reference');if(!reference)return;api(`/api/v1/payments/${encodeURIComponent(reference)}/verify`).then(async response=>{if(response.ok){const order=await response.json();setPaymentMessage(order.status==='paid'?'Payment confirmed. Thank you for your order.':`Payment status: ${order.status}.`)}}).finally(()=>window.history.replaceState({},'',window.location.pathname+window.location.hash))},[]);

  async function logout(){
    await api('/api/v1/auth/logout',{method:'POST'});
    setUser(null); setSessionState('ready');
  }

  function sessionExpired(){setUser(null);setAuthMode('login');setAuthOpen(true)}

  async function identify(event){
    event.preventDefault(); if(!image)return;
    setAiState('loading'); setAiError(''); setPredictions([]);
    const body=new FormData(); body.append('image',image);
    try{
      const response=await fetch(`${AI_API}/api/v1/classify`,{method:'POST',body});
      if(!response.ok)throw new Error(await readError(response,'The AI service could not classify this image.'));
      const result=await response.json(); setPredictions(normalizePredictions(result.predictions)); setAiState('ready');
    }catch(error){setAiError(error.message||'The AI service is unavailable.');setAiState('error')}
  }

  return <>
    <nav>
      <a className="brand" href="#top"><Leaf/> BloomAI</a>
      <div className="links"><a href="#market">Marketplace</a><a href="#ai">AI Lab</a><a href={`${API}/docs`} target="_blank" rel="noreferrer">API</a></div>
      <div className="account-actions">
        {sessionState==='loading'?<LoaderCircle className="spin session-loader"/>:user?<><a className="user-chip" href="#vendor"><UserRound/>{user.name}</a><button className="ghost" onClick={logout}><LogOut/>Logout</button></>:<><button className="text-button" onClick={()=>{setAuthMode('register');setAuthOpen(true)}}>Register</button><button className="ghost" onClick={()=>{setAuthMode('login');setAuthOpen(true)}}>Sign in</button></>}
      </div>
    </nav>
    <main id="top">
      <section className="hero"><div className="eyebrow"><Sparkles size={16}/> Nature meets intelligent commerce</div><h1>Discover plants.<br/><em>Grow possibilities.</em></h1><p>The global marketplace connecting growers, researchers, florists and plant lovers—with responsible AI at its roots.</p><div className="actions"><a href="#market" className="primary">Explore marketplace <Search size={18}/></a><a href="#ai" className="secondary">Identify a flower</a></div><div className="trust"><span><Globe2/> Global vendors</span><span><ShieldCheck/> Verified marketplace</span><span><Sparkles/> AI-powered discovery</span></div></section>
      <section id="market" className="market">
        <div className="section-heading"><div><span className="kicker">Fresh from our community</span><h2>Explore the marketplace</h2></div>{!user&&<button className="secondary" onClick={()=>{setAuthMode('register');setAuthOpen(true)}}>Become a vendor</button>}</div>
        {paymentMessage&&<div className="form-success payment-message" role="status">{paymentMessage}</div>}
        {user&&['vendor','admin'].includes(user.role)&&<div id="vendor"><VendorDashboard user={user} editing={editing} onCancel={()=>setEditing(null)} onSaved={product=>{setProducts(current=>editing?current.map(item=>item.id===product.id?product:item):[product,...current]);setEditing(null);setMarketState('ready')}} onSessionExpired={sessionExpired}/></div>}
        {user&&user.role==='customer'&&<div className="customer-note"><UserRound/><span>Signed in as a customer. Register a vendor account to publish products.</span></div>}
        <div className="grid">{marketState==='loading'&&<p>Loading the latest products…</p>}{marketState==='offline'&&<div className="notice">Marketplace service is unavailable. Please refresh shortly.</div>}{marketState==='ready'&&products.length===0&&<div className="empty"><Store size={42}/><h3>The first collection is taking root</h3><p>Sign in with a vendor account to publish the first product.</p></div>}{products.map(product=><ProductCard key={product.id} product={product} user={user} onEdit={item=>{setEditing(item);window.location.hash='vendor'}} onDeleted={id=>setProducts(current=>current.filter(item=>item.id!==id))}/>)}</div>
      </section>
      <section id="ai" className="ai"><Sparkles/><div className="ai-content"><span className="kicker">BloomAI Vision</span><h2>Know what you grow.</h2><p>Upload a flower image for a top-five prediction from our independently tested 102-species MobileNetV3 model.</p><form className="classifier" onSubmit={identify}><label className="upload"><Upload/><span>{image?image.name:'Choose a JPEG, PNG, or WebP image'}</span><input type="file" accept="image/jpeg,image/png,image/webp" onChange={event=>{setImage(event.target.files?.[0]||null);setPredictions([]);setAiState('idle')}}/></label><button className="identify" disabled={!image||aiState==='loading'}>{aiState==='loading'?<><LoaderCircle className="spin"/>Identifying…</>:<>Identify flower<Sparkles size={17}/></>}</button></form>{aiError&&<div className="ai-error" role="alert">{aiError}</div>}{predictions.length>0&&<div className="predictions" aria-live="polite"><h3>Most likely matches</h3>{predictions.map((item,index)=><div className="prediction" key={item.category_id}><span><b>{index+1}</b>{item.name}</span><strong>{(item.confidence*100).toFixed(1)}%</strong></div>)}</div>}</div></section>
    </main>
    <footer><div className="brand"><Leaf/> BloomAI</div><p>Global botanical commerce, thoughtfully built.</p></footer>
    {authOpen&&<AuthModal mode={authMode} setMode={setAuthMode} onClose={()=>setAuthOpen(false)} onAuthenticated={profile=>{setUser(profile);setSessionState('ready')}}/>}
  </>;
}
createRoot(document.getElementById('root')).render(<App/>);