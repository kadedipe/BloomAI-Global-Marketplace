import React, {useEffect, useState} from 'react';
import {createRoot} from 'react-dom/client';
import {Leaf, Search, Sparkles, Store, ShieldCheck, Globe2} from 'lucide-react';
import './styles.css';

const API=(import.meta.env.VITE_API_URL||'http://localhost:8000').replace(/\/$/,'');
function App(){
 const [products,setProducts]=useState([]); const [state,setState]=useState('loading');
 useEffect(()=>{fetch(`${API}/api/v1/products`).then(r=>{if(!r.ok)throw Error();return r.json()}).then(x=>{setProducts(x);setState('ready')}).catch(()=>setState('offline'))},[]);
 return <><nav><a className="brand"><Leaf/> BloomAI</a><div className="links"><a href="#market">Marketplace</a><a href="#ai">AI Lab</a><a href={`${API}/docs`}>API</a></div><button className="ghost">Sign in</button></nav>
 <main><section className="hero"><div className="eyebrow"><Sparkles size={16}/> Nature meets intelligent commerce</div><h1>Discover plants.<br/><em>Grow possibilities.</em></h1><p>The global marketplace connecting growers, researchers, florists and plant lovers—with responsible AI at its roots.</p><div className="actions"><a href="#market" className="primary">Explore marketplace <Search size={18}/></a><a href="#ai" className="secondary">Identify a flower</a></div><div className="trust"><span><Globe2/> Global vendors</span><span><ShieldCheck/> Verified marketplace</span><span><Sparkles/> AI-powered discovery</span></div></section>
 <section id="market" className="market"><div><span className="kicker">Fresh from our community</span><h2>Explore the marketplace</h2></div><div className="grid">{state==='loading'&&<p>Loading the latest products…</p>}{state==='offline'&&<div className="notice">Marketplace service is starting. Please refresh shortly.</div>}{state==='ready'&&products.length===0&&<div className="empty"><Store size={42}/><h3>The first collection is taking root</h3><p>Vendor listings will appear here. Create a vendor account through the API to add the first product.</p></div>}{products.map(p=><article key={p.id}><div className="image">{p.image_url?<img src={p.image_url} alt=""/>:<Leaf/>}</div><h3>{p.name}</h3><p>{p.description}</p><strong>{p.currency} {Number(p.price).toFixed(2)}</strong></article>)}</div></section>
 <section id="ai" className="ai"><Sparkles/><div><span className="kicker">BloomAI Vision</span><h2>Know what you grow.</h2><p>Upload a flower image and connect it to knowledge, care guidance and trusted sellers. Model deployment is isolated in its own service for safe, independent scaling.</p></div></section></main><footer><div className="brand"><Leaf/> BloomAI</div><p>Global botanical commerce, thoughtfully built.</p></footer></>
}
createRoot(document.getElementById('root')).render(<App/>);

