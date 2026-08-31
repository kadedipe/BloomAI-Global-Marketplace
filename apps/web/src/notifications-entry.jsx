import React,{useEffect,useRef,useState} from 'react';
import {Bell,CheckCheck,LoaderCircle} from 'lucide-react';
import {createRoot} from 'react-dom/client';
import './notifications.css';

const API=(import.meta.env.VITE_API_URL||'http://localhost:8000').replace(/\/$/,'');

async function api(path,options={}){
  const headers={'Content-Type':'application/json',...(options.headers||{})};
  return fetch(`${API}${path}`,{credentials:'include',...options,headers});
}

function relativeTime(value){
  const seconds=Math.max(0,Math.floor((Date.now()-new Date(value).getTime())/1000));
  if(seconds<60)return 'Just now';
  const minutes=Math.floor(seconds/60);if(minutes<60)return `${minutes}m ago`;
  const hours=Math.floor(minutes/60);if(hours<24)return `${hours}h ago`;
  const days=Math.floor(hours/24);if(days<7)return `${days}d ago`;
  return new Date(value).toLocaleDateString();
}

function NotificationCenter(){
  const [authorized,setAuthorized]=useState(false);
  const [open,setOpen]=useState(false);
  const [items,setItems]=useState([]);
  const [unread,setUnread]=useState(0);
  const [loading,setLoading]=useState(false);
  const [error,setError]=useState('');
  const wrapper=useRef(null);

  async function load({silent=false}={}){
    if(!silent)setLoading(true);
    try{
      const response=await api('/api/v1/notifications?limit=20');
      if(response.status===401){setAuthorized(false);setItems([]);setUnread(0);return}
      if(!response.ok)throw new Error('Notifications are temporarily unavailable.');
      const data=await response.json();
      setAuthorized(true);setItems(data.items||[]);setUnread(data.unread_count||0);setError('');
    }catch(reason){if(authorized)setError(reason.message||'Notifications are temporarily unavailable.')}
    finally{if(!silent)setLoading(false)}
  }

  useEffect(()=>{
    load({silent:true});
    const interval=window.setInterval(()=>load({silent:true}),30000);
    const onFocus=()=>load({silent:true});
    window.addEventListener('focus',onFocus);
    return()=>{window.clearInterval(interval);window.removeEventListener('focus',onFocus)};
  },[]);

  useEffect(()=>{
    function outside(event){if(open&&wrapper.current&&!wrapper.current.contains(event.target))setOpen(false)}
    document.addEventListener('mousedown',outside);
    return()=>document.removeEventListener('mousedown',outside);
  },[open]);

  async function markRead(item,navigate=true){
    if(!item.read_at){
      const response=await api(`/api/v1/notifications/${item.id}/read`,{method:'PATCH'});
      if(response.ok){
        const updated=await response.json();
        setItems(current=>current.map(value=>value.id===item.id?updated:value));
        setUnread(current=>Math.max(0,current-1));
      }
    }
    if(navigate&&item.link)window.location.assign(item.link);
  }

  async function markAll(){
    const response=await api('/api/v1/notifications/read-all',{method:'POST'});
    if(response.ok){
      const now=new Date().toISOString();
      setItems(current=>current.map(item=>({...item,read_at:item.read_at||now})));
      setUnread(0);
    }
  }

  if(!authorized)return null;
  const isAdmin=window.location.pathname.includes('admin');
  return <div className={`notification-center ${isAdmin?'notification-center-admin':''}`} ref={wrapper}>
    <button className="notification-bell" type="button" aria-label={`Notifications${unread?`, ${unread} unread`:''}`} aria-expanded={open} onClick={()=>{setOpen(value=>!value);if(!open)load()}}>
      <Bell/>{unread>0&&<span className="notification-badge">{unread>99?'99+':unread}</span>}
    </button>
    {open&&<section className="notification-popover" aria-label="Notifications">
      <div className="notification-head"><div><strong>Notifications</strong><small>{unread?`${unread} unread`:'You are all caught up'}</small></div>{unread>0&&<button type="button" onClick={markAll}><CheckCheck/>Mark all read</button>}</div>
      {loading&&items.length===0?<div className="notification-state"><LoaderCircle className="spin"/>Loading notifications…</div>:error?<div className="notification-state notification-error">{error}</div>:items.length===0?<div className="notification-state">No notifications yet.</div>:<div className="notification-list">{items.map(item=><button type="button" key={item.id} className={`notification-item ${item.read_at?'':'unread'}`} onClick={()=>markRead(item)}><span className="notification-dot"/><span className="notification-copy"><strong>{item.title}</strong><span>{item.message}</span><small>{relativeTime(item.created_at)}</small></span></button>)}</div>}
    </section>}
  </div>
}

const node=document.getElementById('notification-root');
if(node)createRoot(node).render(<NotificationCenter/>);
