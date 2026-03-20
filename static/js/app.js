// ===== SHARED UTILITIES =====
const RATES = { INR:1, USD:83.5, EUR:90.2, GBP:105.8, JPY:0.56, AED:22.7, SGD:62.1 };
const SYMBOLS = { INR:'₹', USD:'$', EUR:'€', GBP:'£', JPY:'¥', AED:'د.إ', SGD:'S$' };
const CAT_COLORS = {
  Food:'#c0632a', Clothing:'#b5883a', Travel:'#4a7c6b', Books:'#6b5e9e',
  Entertainment:'#b54a6b', Health:'#3a7c5a', Other:'#8b7355'
};

function toINR(a,c){ return a*(RATES[c]||1); }
function fmt(a){ return '₹'+Number(a).toLocaleString('en-IN',{minimumFractionDigits:2,maximumFractionDigits:2}); }
function fmtOrig(a,c){ return (SYMBOLS[c]||'')+Number(a).toLocaleString('en-IN',{minimumFractionDigits:2,maximumFractionDigits:2}); }
function getCatColor(cat){ return CAT_COLORS[cat]||'#A67C52'; }

// Block future dates on all date inputs
function setMaxDateToday(){
  const today = new Date().toISOString().split('T')[0];
  document.querySelectorAll('input[type="date"]').forEach(el=>{
    // Only restrict transaction date input, not filter "from/to"
    if(el.id==='txnDate') el.max=today;
  });
}

function toggleCustom(){
  const cat=document.getElementById('txnCategory').value;
  const d=document.getElementById('customCatDiv');
  if(d) d.classList.toggle('d-none', cat!=='Other');
}

function updateINRPreview(){
  const amount=parseFloat(document.getElementById('txnAmount')?.value||0);
  const currency=document.getElementById('txnCurrency')?.value||'INR';
  const preview=document.getElementById('inrPreview');
  const eq=document.getElementById('inrEq');
  if(!preview||!eq) return;
  if(amount>0 && currency!=='INR'){
    preview.classList.remove('d-none');
    eq.textContent=fmt(toINR(amount,currency));
  } else { preview.classList.add('d-none'); }
}

document.addEventListener('DOMContentLoaded',()=>{
  document.getElementById('txnAmount')?.addEventListener('input',updateINRPreview);
  document.getElementById('txnCurrency')?.addEventListener('change',updateINRPreview);

  // Set today as default and max for transaction date
  const today=new Date().toISOString().split('T')[0];
  const d=document.getElementById('txnDate');
  if(d){ d.value=today; d.max=today; }

  // Date display
  const el=document.getElementById('currentDate');
  if(el) el.textContent=new Date().toLocaleDateString('en-IN',{weekday:'long',year:'numeric',month:'long',day:'numeric'});

  setMaxDateToday();
});

function openEditModal(txn){
  document.getElementById('modalTitle').textContent='Edit Expense ✏️';
  document.getElementById('editId').value=txn.id;
  document.getElementById('txnTitle').value=txn.title;
  document.getElementById('txnAmount').value=txn.amount;
  document.getElementById('txnCurrency').value=txn.currency;
  const today=new Date().toISOString().split('T')[0];
  document.getElementById('txnDate').value=txn.date;
  document.getElementById('txnDate').max=today;
  const knownCats=['Food','Clothing','Travel','Books','Entertainment','Health','Other'];
  const catSel=document.getElementById('txnCategory');
  if(knownCats.includes(txn.category)){
    catSel.value=txn.category;
    document.getElementById('customCatDiv').classList.toggle('d-none', txn.category!=='Other');
    if(txn.category==='Other') document.getElementById('customCat').value='';
  } else {
    catSel.value='Other';
    document.getElementById('customCatDiv').classList.remove('d-none');
    document.getElementById('customCat').value=txn.category;
  }
  updateINRPreview();
  new bootstrap.Modal(document.getElementById('addModal')).show();
}

function resetModal(){
  document.getElementById('modalTitle').textContent='Add Expense 💸';
  document.getElementById('editId').value='';
  document.getElementById('txnTitle').value='';
  document.getElementById('txnAmount').value='';
  document.getElementById('txnCurrency').value='INR';
  const today=new Date().toISOString().split('T')[0];
  document.getElementById('txnDate').value=today;
  document.getElementById('txnDate').max=today;
  document.getElementById('txnCategory').value='';
  document.getElementById('customCatDiv').classList.add('d-none');
  document.getElementById('customCat').value='';
  document.getElementById('formError').classList.add('d-none');
  document.getElementById('inrPreview').classList.add('d-none');
}

async function submitTransaction(){
  const editId=document.getElementById('editId').value;
  const title=document.getElementById('txnTitle').value.trim();
  const amount=parseFloat(document.getElementById('txnAmount').value);
  const currency=document.getElementById('txnCurrency').value;
  const date=document.getElementById('txnDate').value;
  let category=document.getElementById('txnCategory').value;
  if(category==='Other') category=document.getElementById('customCat').value.trim();

  // Validate no future date
  const today=new Date().toISOString().split('T')[0];
  if(!title){ showFormError('Please enter a title for your expense.'); return; }
  if(!amount||amount<=0){ showFormError('Enter a valid amount (must be > 0).'); return; }
  if(!category){ showFormError('Please pick a category.'); return; }
  if(!date){ showFormError('Please select a date.'); return; }
  if(date>today){ showFormError("Can't add expenses for future dates!"); return; }

  const body={title,amount,currency,date,category};
  const url=editId?`/api/transactions/${editId}`:'/api/transactions';
  const method=editId?'PUT':'POST';
  try {
    const res=await fetch(url,{method,headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
    const data=await res.json();
    if(!res.ok){ showFormError(data.error||'Something went wrong. Try again!'); return; }
    bootstrap.Modal.getOrCreateInstance(document.getElementById('addModal')).hide();
    resetModal();
    if(typeof loadData==='function') loadData();
  } catch(e){ showFormError('Network error. Check your connection!'); }
}

function showFormError(msg){
  const el=document.getElementById('formError');
  el.textContent=msg; el.classList.remove('d-none');
}

function showWarning(monthly){
  const b=document.getElementById('warningBanner');
  if(!b) return;
  if(monthly>100000){
    b.className='alert warn-3 mb-4 py-2';
    b.innerHTML='🚨 <strong>Beyond Usual!</strong> Monthly expenses crossed ₹1,00,000! Seriously, time to review your spending.';
    b.classList.remove('d-none');
  } else if(monthly>50000){
    b.className='alert warn-2 mb-4 py-2';
    b.innerHTML='⚠️ <strong>Spending Above Limit!</strong> Monthly expenses crossed ₹50,000. Consider cutting back on non-essentials.';
    b.classList.remove('d-none');
  } else if(monthly>25000){
    b.className='alert warn-1 mb-4 py-2';
    b.innerHTML='💡 <strong>Heads Up!</strong> You\'ve spent over ₹25,000 this month. Keep an eye on your wallet!';
    b.classList.remove('d-none');
  } else { b.classList.add('d-none'); }
}

function exportCSV(){
  fetch('/api/transactions').then(r=>r.json()).then(data=>{
    const rows=[['#','Title','Category','Date','Amount','Currency','Amount (INR)']];
    data.transactions.forEach((t,i)=>rows.push([i+1,t.title,t.category,t.date,t.amount,t.currency,t.amount_inr]));
    const csv=rows.map(r=>r.map(c=>`"${c}"`).join(',')).join('\n');
    const a=document.createElement('a');
    a.href=URL.createObjectURL(new Blob([csv],{type:'text/csv'}));
    a.download='my_expenses.csv'; a.click();
  });
}

async function saveBudget(){
  const input=document.getElementById('budgetInput');
  const budget=parseFloat(input.value);
  if(!budget||budget<=0){ input.classList.add('is-invalid'); return; }
  input.classList.remove('is-invalid');
  try {
    const res=await fetch('/api/budget',{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({budget})});
    if(!res.ok) return;
    bootstrap.Modal.getOrCreateInstance(document.getElementById('budgetModal')).hide();
    if(typeof loadData==='function') loadData();
  } catch(e){ console.error('Budget save failed:',e); }
}

async function deleteTransaction(id){
  if(!confirm('Delete this expense? This cannot be undone.')) return;
  await fetch(`/api/transactions/${id}`,{method:'DELETE'});
  if(typeof loadData==='function') loadData();
}
