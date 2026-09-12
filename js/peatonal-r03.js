(async()=>{
 const response=await fetch('/data/peatonal68.json');if(!response.ok)return;const data=await response.json();
 const en=document.documentElement.lang.startsWith('en');const t=(es,eng)=>en?eng:es;
 const units=new Map(data.units.map(u=>[u.id,u]));let selection=[];
 const eligible=id=>units.get(id)?.status==='available';
 const records=[...document.querySelectorAll('.unit-record')];
 const cta=document.querySelector('#context-cta a');
 function render(){
  const url=new URL(location.href);
  if(selection.length)url.searchParams.set('units',selection.join(','));else url.searchParams.delete('units');
  history.replaceState(null,'',url);
  document.querySelectorAll('.lang-switch a').forEach(a=>{const target=new URL(a.href);if(selection.length){target.searchParams.set('units',selection.join(','));target.hash='disponibilidad'}else{target.searchParams.delete('units');target.hash=location.hash}a.href=target.href});
  const area=selection.reduce((s,id)=>s+units.get(id).area,0);
  const label=selection.length>1?t(`Consultar configuración de ${area} m²`,`Enquire about the ${area} m² configuration`):selection.length===1?t(`Consultar Local ${selection[0]}`,`Enquire about Unit ${selection[0]}`):t('Consultar disponibilidad','Enquire about availability');
  const context=selection.length>1?`${selection.join('+')} (${area} m²)`:selection.length?`${selection[0]}`:t('disponibilidad','availability');
  const visit=document.getElementById('request-visit');if(visit)visit.href='https://wa.me/50766758127?text='+encodeURIComponent(t('Hola Darío, quisiera coordinar una visita a Peatonal 68: ','Hello Darío, I would like to arrange a viewing at Peatonal 68: ')+context);
  cta.textContent=label;cta.href='https://wa.me/50766758127?text='+encodeURIComponent(t('Hola Darío, consulta Peatonal 68 - ','Hello Darío, Peatonal 68 enquiry - ')+context);
  const contact=document.getElementById('context-contact');if(contact){contact.textContent=label;contact.href=cta.href}
  document.querySelectorAll('[data-select]').forEach(b=>b.setAttribute('aria-pressed',String(selection.includes(Number(b.dataset.select)))));
  document.querySelectorAll('[data-marker]').forEach(b=>b.dataset.selected=String(selection.includes(Number(b.dataset.marker))));
  document.querySelectorAll('[data-combo]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.combo===selection.join(','))));
  document.getElementById('selection-result').textContent=selection.length?`${t('Selección','Selection')}: ${selection.join(' + ')} · ${area} m²`:'';
  document.getElementById('clear-selection').hidden=!selection.length;yieldSticky();
 }
 function select(ids){if(!ids.every(eligible))return;if(ids.length>1&&!data.combinations.some(c=>c.join(',')===ids.join(',')))return;selection=ids;render();}
 document.querySelectorAll('[data-combo]').forEach(b=>b.addEventListener('click',()=>select(b.dataset.combo.split(',').map(Number))));
 document.querySelectorAll('[data-select]').forEach(b=>b.addEventListener('click',()=>{
  const id=Number(b.dataset.select);select([id]);document.querySelector('[data-filter="available"]').click();
  const record=document.getElementById('local-'+id);records.forEach(r=>r.open=r===record);
  const summary=record.querySelector('summary');summary.focus({preventScroll:true});record.scrollIntoView({behavior:'smooth',block:'start'});
  let back=record.querySelector('[data-return-selector]');if(!back){back=document.createElement('button');back.className='text-control';back.dataset.returnSelector='true';back.textContent=t('Volver al selector','Return to unit selector');record.querySelector('.unit-actions').append(back)}
  back.onclick=()=>{b.scrollIntoView({behavior:'smooth',block:'center'});b.focus({preventScroll:true})};
 }));
 document.getElementById('clear-selection').addEventListener('click',()=>{selection=[];render()});
 // Native details retain keyboard semantics; only one commercial unit opens.
 records.forEach(record=>record.querySelector('summary').addEventListener('click',()=>{
  const summary=record.querySelector('summary');const top=summary.getBoundingClientRect().top;const opening=!record.open;
  if(opening){records.forEach(other=>{if(other!==record)other.open=false});select([Number(record.dataset.unit)])}
  requestAnimationFrame(()=>{const delta=summary.getBoundingClientRect().top-top;if(Math.abs(delta)>1)window.scrollBy({top:delta,behavior:'instant'})});
 }));
 document.querySelectorAll('[data-filter]').forEach(b=>b.addEventListener('click',()=>{
  const available=b.dataset.filter==='available';document.querySelectorAll('[data-filter]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));
  document.querySelectorAll('.unit-record,.unit-reference').forEach(x=>x.hidden=(x.dataset.state==='available')!==available);
 }));
 function view(which){document.querySelectorAll('.facade-tabs [data-view]').forEach(b=>{const active=b.dataset.view===which;b.setAttribute('aria-selected',String(active));b.tabIndex=active?0:-1});document.getElementById('view-levels').hidden=which!=='levels';document.getElementById('view-photo').hidden=which!=='photo';}
 const tabs=[...document.querySelectorAll('.facade-tabs [data-view]')];tabs.forEach((b,i)=>{b.addEventListener('click',()=>view(b.dataset.view));b.addEventListener('keydown',e=>{if(!['ArrowLeft','ArrowRight','Home','End'].includes(e.key))return;e.preventDefault();const next=e.key==='Home'?0:e.key==='End'?1:1-i;tabs[next].click();tabs[next].focus()})});
 document.querySelectorAll('[data-locate]').forEach(b=>b.addEventListener('click',()=>{select([Number(b.dataset.locate)]);view('photo');document.querySelector('.facade-tabs').scrollIntoView({behavior:'smooth',block:'start'});tabs[1].focus({preventScroll:true})}));
 document.querySelectorAll('.facade-marker').forEach(el=>{const box=data.facade.hotspots[el.dataset.marker];if(box)Object.entries(box).forEach(([key,value])=>el.style[key]=value+'%')});
 const dialog=document.getElementById('unit-gallery');let gallery=[],photoIndex=0,galleryOpener;
 function paintGallery(){const photo=gallery[photoIndex];if(!photo)return;document.getElementById('gallery-image').src=photo.src;document.getElementById('gallery-image').alt=photo.alt[en?'en':'es'];document.getElementById('gallery-caption').textContent=photo.alt[en?'en':'es']+' · '+(photoIndex+1)+' / '+gallery.length;}
 document.querySelectorAll('[data-gallery]').forEach(button=>button.addEventListener('click',()=>{gallery=units.get(Number(button.dataset.gallery)).photos;photoIndex=0;galleryOpener=button;paintGallery();dialog.showModal()}));
 document.getElementById('gallery-close').addEventListener('click',()=>dialog.close());
 dialog.addEventListener('close',()=>galleryOpener?.focus({preventScroll:true}));
 document.getElementById('gallery-prev').addEventListener('click',()=>{photoIndex=(photoIndex+gallery.length-1)%gallery.length;paintGallery()});
 document.getElementById('gallery-next').addEventListener('click',()=>{photoIndex=(photoIndex+1)%gallery.length;paintGallery()});
 dialog.addEventListener('keydown',event=>{if(event.key==='ArrowRight')document.getElementById('gallery-next').click();if(event.key==='ArrowLeft')document.getElementById('gallery-prev').click()});
 document.querySelector('[data-filter="available"]').click();
 const initial=new URL(location.href).searchParams.get('units');
 if(initial)select(initial.split(',').map(Number));
 render();
 function yieldSticky(){const targets=[document.getElementById('context-contact')];if(selection.length===1)targets.push(document.querySelector('#local-'+selection[0]+' .unit-actions a'));document.getElementById('context-cta').hidden=targets.some(eq=>{if(!eq||!eq.getClientRects().length)return false;const rect=eq.getBoundingClientRect();return rect.top>=76&&rect.bottom<=innerHeight;});}
 addEventListener('scroll',yieldSticky,{passive:true});addEventListener('resize',yieldSticky);new IntersectionObserver(yieldSticky,{threshold:[0,1]}).observe(document.getElementById('context-contact'));yieldSticky();
})();
