'use strict';
(function(){
  const el=id=>document.getElementById(id);let ciReady=false,coReady=false;
  
  // Photo zone clicks
  el('photo-zone')?.addEventListener('click',async()=>{
    try{
      const cam=new CameraCapture('ci-video','ci-canvas');
      el('photo-zone').style.display='none';
      el('ci-video-container').style.display='block';
      el('ci-btn-capture').style.display='block';
      await cam.start();
      el('ci-btn-capture').onclick=async()=>{
        const jpeg=await cam.capture();
        await cam.stop();
        el('ci-video-container').style.display='none';
        el('ci-selfie-preview').style.display='block';
        el('ci-selfie-img').src=jpeg;
        el('ci-btn-capture').style.display='none';
        el('ci-btn-retake').style.display='block';
        uploadCheckIn(jpeg);
      };
    }catch(e){alert('Camera error: '+e.message);}
  });
  
  el('co-photo-zone')?.addEventListener('click',async()=>{
    try{
      const cam=new CameraCapture('co-video','co-canvas');
      el('co-photo-zone').style.display='none';
      el('co-video-container').style.display='block';
      el('co-btn-capture').style.display='block';
      await cam.start();
      el('co-btn-capture').onclick=async()=>{
        const jpeg=await cam.capture();
        await cam.stop();
        el('co-video-container').style.display='none';
        el('co-selfie-preview').style.display='block';
        el('co-selfie-img').src=jpeg;
        el('co-btn-capture').style.display='none';
        el('co-btn-retake').style.display='block';
        uploadCheckOut(jpeg);
      };
    }catch(e){alert('Camera error: '+e.message);}
  });
  
  // Retake buttons
  el('ci-btn-retake')?.addEventListener('click',()=>{
    el('ci-selfie-preview').style.display='none';
    el('photo-zone').style.display='block';
    ciReady=false;
  });
  el('co-btn-retake')?.addEventListener('click',()=>{
    el('co-selfie-preview').style.display='none';
    el('co-photo-zone').style.display='block';
    coReady=false;
  });
  
  // Upload check-in
  async function uploadCheckIn(jpeg){
    try{
      const csrf=document.querySelector('meta[name="csrf-token"]')?.getAttribute('content')||'';
      const res=await fetch('/attendance/capture-selfie',{
        method:'POST',
        headers:{'Content-Type':'application/json','X-CSRFToken':csrf},
        body:JSON.stringify({selfie:jpeg,type:'checkin'})
      });
      const d=await res.json();
      if(!res.ok||!d.success){alert('Upload failed: '+(d.message||'Error'));return;}
      ciReady=true;
      el('ci-photo-badge').className='badge bg-success-subtle text-success small';
      el('ci-photo-badge').innerHTML='<i class="bi bi-check-circle me-1"></i>✓ Captured';
      el('ci-text').textContent='Check In Now';
      el('btn-checkin').disabled=false;
      alert('✓ Photo uploaded! Button enabled.');
    }catch(e){alert('Upload error: '+e.message);}
  }
  
  // Upload check-out
  async function uploadCheckOut(jpeg){
    try{
      const csrf=document.querySelector('meta[name="csrf-token"]')?.getAttribute('content')||'';
      const res=await fetch('/attendance/capture-selfie',{
        method:'POST',
        headers:{'Content-Type':'application/json','X-CSRFToken':csrf},
        body:JSON.stringify({selfie:jpeg,type:'checkout'})
      });
      const d=await res.json();
      if(!res.ok||!d.success){alert('Upload failed: '+(d.message||'Error'));return;}
      coReady=true;
      el('co-photo-badge').className='badge bg-success-subtle text-success small';
      el('co-photo-badge').innerHTML='<i class="bi bi-check-circle me-1"></i>✓ Captured';
      el('co-text').textContent='Check Out Now';
      el('btn-checkout').disabled=false;
      alert('✓ Photo uploaded! Button enabled.');
    }catch(e){alert('Upload error: '+e.message);}
  }
  
  // Check-in button
  el('btn-checkin')?.addEventListener('click',()=>{
    if(!ciReady){alert('Upload photo first');return;}
    const csrf=document.querySelector('meta[name="csrf-token"]')?.getAttribute('content')||'';
    const form=new FormData();
    form.append('latitude',window.lat||0);
    form.append('longitude',window.lon||0);
    form.append('accuracy',window.acc||0);
    el('btn-checkin').disabled=true;
    fetch('/attendance/checkin',{method:'POST',headers:{'X-CSRFToken':csrf},body:form})
    .then(r=>r.json()).then(d=>{
      if(d.success){alert('✅ Check-in OK');location.reload();}
      else{alert('❌ '+d.message);el('btn-checkin').disabled=false;}
    }).catch(e=>{alert('❌ '+e.message);el('btn-checkin').disabled=false;});
  });
  
  // Check-out button
  el('btn-checkout')?.addEventListener('click',()=>{
    if(!coReady){alert('Upload photo first');return;}
    const csrf=document.querySelector('meta[name="csrf-token"]')?.getAttribute('content')||'';
    const form=new FormData();
    form.append('latitude',window.lat||0);
    form.append('longitude',window.lon||0);
    form.append('accuracy',window.acc||0);
    el('btn-checkout').disabled=true;
    fetch('/attendance/checkout',{method:'POST',headers:{'X-CSRFToken':csrf},body:form})
    .then(r=>r.json()).then(d=>{
      if(d.success){alert('✅ Check-out OK');location.reload();}
      else{alert('❌ '+d.message);el('btn-checkout').disabled=false;}
    }).catch(e=>{alert('❌ '+e.message);el('btn-checkout').disabled=false;});
  });
})();
