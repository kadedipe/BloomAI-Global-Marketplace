import React,{useEffect,useState} from 'react';
import {createRoot} from 'react-dom/client';
import {Leaf,LockKeyhole,ShieldCheck} from 'lucide-react';
import './admin-login.css';

const API=(import.meta.env.VITE_API_URL||'http://localhost:8000').replace(/\/$/,'');

async function request(path,options={}){
  return fetch(`${API}${path}`,{
    credentials:'include',
    headers:{'Content-Type':'application/json',...(options.headers||{})},
    ...options,
  });
}

function AdminLogin(){
  const [email,setEmail]=useState('');
  const [password,setPassword]=useState('');
  const [message,setMessage]=useState('');
  const [loading,setLoading]=useState(false);

  useEffect(()=>{
    let active=true;
    request('/api/v1/auth/me').then(async response=>{
      if(!response.ok)return;
      const user=await response.json();
      if(active&&user.role==='admin')window.location.replace('/admin.html');
    }).catch(()=>{});
    return()=>{active=false};
  },[]);

  async function submit(event){
    event.preventDefault();
    setLoading(true);
    setMessage('');
    try{
      const login=await request('/api/v1/auth/login',{
        method:'POST',
        body:JSON.stringify({email,password}),
      });
      if(!login.ok){
        setMessage(login.status===401?'Invalid administrator email or password.':'Administrator sign-in failed.');
        return;
      }

      const profile=await request('/api/v1/auth/me');
      if(!profile.ok){
        setMessage('The session could not be verified after sign-in.');
        return;
      }
      const user=await profile.json();
      if(user.role!=='admin'){
        await request('/api/v1/auth/logout',{method:'POST'});
        setMessage('This account is not authorized for BloomAI administration.');
        return;
      }
      window.location.replace('/admin.html');
    }catch{
      setMessage('BloomAI could not reach the authentication service.');
    }finally{
      setLoading(false);
    }
  }

  return <main className="admin-login-shell">
    <section className="admin-login-card">
      <div className="admin-login-brand"><Leaf/><span>BloomAI</span></div>
      <div className="admin-login-icon"><ShieldCheck/></div>
      <span className="admin-login-eyebrow">Protected administration</span>
      <h1>Administrator sign in</h1>
      <p>Use a provisioned BloomAI administrator account. Public registration cannot create administrator privileges.</p>
      <form onSubmit={submit}>
        <label>Email<input type="email" autoComplete="username" value={email} onChange={event=>setEmail(event.target.value)} required /></label>
        <label>Password<input type="password" autoComplete="current-password" value={password} onChange={event=>setPassword(event.target.value)} required /></label>
        {message&&<div className="admin-login-error" role="alert">{message}</div>}
        <button type="submit" disabled={loading}><LockKeyhole/>{loading?'Verifying…':'Sign in to Admin'}</button>
      </form>
      <a href="/">Return to marketplace</a>
    </section>
  </main>;
}

createRoot(document.getElementById('root')).render(<AdminLogin/>);
