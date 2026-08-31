const API=(import.meta.env.VITE_API_URL||'http://localhost:8000').replace(/\/$/,'');

async function enterAdmin(){
  try{
    const response=await fetch(`${API}/api/v1/auth/me`,{credentials:'include'});
    if(!response.ok){
      window.location.replace('/admin-login.html');
      return;
    }
    const user=await response.json();
    if(user.role!=='admin'){
      await fetch(`${API}/api/v1/auth/logout`,{
        method:'POST',
        credentials:'include',
        headers:{'Content-Type':'application/json'},
      }).catch(()=>{});
      window.location.replace('/admin-login.html?reason=forbidden');
      return;
    }
    const [{installParticipantProfileEditor},{installAdminNotificationTester}]=await Promise.all([
      import('./admin-participant-editor.js'),
      import('./admin-test-notifications.js'),
      import('./admin.jsx'),
    ]);
    installParticipantProfileEditor();
    installAdminNotificationTester();
  }catch{
    window.location.replace('/admin-login.html?reason=unavailable');
  }
}

enterAdmin();