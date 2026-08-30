import React, {useEffect, useState} from 'react';
import {createRoot} from 'react-dom/client';
import {
  Globe2, Leaf, LoaderCircle, LogOut, Plus, Search, ShieldCheck,
  Sparkles, Store, Upload, UserRound, X
} from 'lucide-react';
import './styles.css';

const API=(import.meta.env.VITE_API_URL||'http://localhost:8000').replace(/\/$/,'');
const AI_API=(import.meta.env.VITE_AI_API_URL||'http://localhost:8001').replace(/\/$/,'');

async function readError(response,fallback){
  try{
    const body=await response.json();
    if(Array.isArray(body.detail))return body.detail.map(item=>item.msg).join('. ');
    return body.detail||fallback;
  }catch{return fallback}
}

async function api(path,options={}){
  const headers={...(options.body instanceof FormData?{}:{'Content-Type':'application/json'}),...options.headers};
  return fetch(`${API}${path}`,{credentials:'include',...options,headers});
}

const emptyAuth={name:'',email:'',password:'',role:'customer'};
const emptyProduct={name:'',description:'',price:'',currency:'USD',image_url:''};

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

function VendorDashboard({user,onCreated,onSessionExpired}){
  const [form,setForm]=useState(emptyProduct);
  const [status,setStatus]=useState('idle');
  const [error,setError]=useState('');
  const [message,setMessage]=useState('');

  function update(event){setForm(current=>({...current,[event.target.name]:event.target.value}))}

  async function submit(event){
    event.preventDefault(); setError(''); setMessage('');
    if(Number(form.price)<=0){setError('Enter a price greater than zero.');return}
    if(form.image_url){
      try{const parsed=new URL(form.image_url);if(!['http:','https:'].includes(parsed.protocol))throw Error()}
      catch{setError('Image URL must be a valid HTTP or HTTPS address.');return}
    }
    setStatus('loading');
    const response=await api('/api/v1/products',{
      method:'POST',
      body:JSON.stringify({...form,name:form.name.trim(),description:form.description.trim(),price:Number(form.price),currency:form.currency.toUpperCase(),image_url:form.image_url.trim()||null})
    });
    if(response.status===401){onSessionExpired();setStatus('idle');return}
    if(!response.ok){setError(await readError(response,'The product could not be published.'));setStatus('idle');return}
    const product=await response.json();
    onCreated(product); setForm(emptyProduct); setMessage('Product published successfully.'); setStatus('idle');
  }

  return <section className="vendor-panel" aria-labelledby="vendor-heading">
    <div className="vendor-copy"><span className="kicker">Vendor dashboard</span><h3 id="vendor-heading">Publish a botanical listing</h3><p>Signed in as {user.name}. New products appear in the marketplace immediately.</p></div>
    <form className="product-form" onSubmit={submit}>
      <label>Product name<input name="name" value={form.name} onChange={update} minLength="2" maxLength="160" required/></label>
      <label>Price<div className="price-row"><select name="currency" value={form.currency} onChange={update}><option>USD</option><option>EUR</option><option>GBP</option><option>UGX</option><option>NGN</option></select><input name="price" value={form.price} onChange={update} type="number" min="0.01" step="0.01" required/></div></label>
      <label className="wide">Description<textarea name="description" value={form.description} onChange={update} maxLength="5000" rows="3"/></label>
      <label className="wide">Image URL <span>(optional)</span><input name="image_url" value={form.image_url} onChange={update} type="url" placeholder="https://…"/></label>
      {error&&<div className="form-error wide" role="alert">{error}</div>}
      {message&&<div className="form-success wide" role="status">{message}</div>}
      <button className="primary product-submit wide" disabled={status==='loading'}>{status==='loading'?<><LoaderCircle className="spin"/>Publishing…</>:<><Plus/>Publish product</>}</button>
    </form>
  </section>
}

function App(){
  const [products,setProducts]=useState([]); const [marketState,setMarketState]=useState('loading');
  const [user,setUser]=useState(null); const [sessionState,setSessionState]=useState('loading');
  const [authOpen,setAuthOpen]=useState(false); const [authMode,setAuthMode]=useState('login');
  const [image,setImage]=useState(null); const [aiState,setAiState]=useState('idle');
  const [predictions,setPredictions]=useState([]); const [aiError,setAiError]=useState('');

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
      const result=await response.json(); setPredictions(result.predictions||[]); setAiState('ready');
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
        {user&&['vendor','admin'].includes(user.role)&&<div id="vendor"><VendorDashboard user={user} onCreated={product=>{setProducts(current=>[product,...current]);setMarketState('ready')}} onSessionExpired={sessionExpired}/></div>}
        {user&&user.role==='customer'&&<div className="customer-note"><UserRound/><span>Signed in as a customer. Register a vendor account to publish products.</span></div>}
        <div className="grid">{marketState==='loading'&&<p>Loading the latest products…</p>}{marketState==='offline'&&<div className="notice">Marketplace service is unavailable. Please refresh shortly.</div>}{marketState==='ready'&&products.length===0&&<div className="empty"><Store size={42}/><h3>The first collection is taking root</h3><p>Sign in with a vendor account to publish the first product.</p></div>}{products.map(product=><article key={product.id}><div className="image">{product.image_url?<img src={product.image_url} alt={product.name}/>:<Leaf/>}</div><h3>{product.name}</h3><p>{product.description}</p><strong>{product.currency} {Number(product.price).toFixed(2)}</strong></article>)}</div>
      </section>
      <section id="ai" className="ai"><Sparkles/><div className="ai-content"><span className="kicker">BloomAI Vision</span><h2>Know what you grow.</h2><p>Upload a flower image for a top-five prediction from our independently tested 102-species MobileNetV3 model.</p><form className="classifier" onSubmit={identify}><label className="upload"><Upload/><span>{image?image.name:'Choose a JPEG, PNG, or WebP image'}</span><input type="file" accept="image/jpeg,image/png,image/webp" onChange={event=>{setImage(event.target.files?.[0]||null);setPredictions([]);setAiState('idle')}}/></label><button className="identify" disabled={!image||aiState==='loading'}>{aiState==='loading'?<><LoaderCircle className="spin"/>Identifying…</>:<>Identify flower<Sparkles size={17}/></>}</button></form>{aiError&&<div className="ai-error" role="alert">{aiError}</div>}{predictions.length>0&&<div className="predictions" aria-live="polite"><h3>Most likely matches</h3>{predictions.map((item,index)=><div className="prediction" key={item.category_id}><span><b>{index+1}</b>{item.name}</span><strong>{(item.confidence*100).toFixed(1)}%</strong></div>)}</div>}</div></section>
    </main>
    <footer><div className="brand"><Leaf/> BloomAI</div><p>Global botanical commerce, thoughtfully built.</p></footer>
    {authOpen&&<AuthModal mode={authMode} setMode={setAuthMode} onClose={()=>setAuthOpen(false)} onAuthenticated={profile=>{setUser(profile);setSessionState('ready')}}/>}
  </>;
}
createRoot(document.getElementById('root')).render(<App/>);
