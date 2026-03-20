let allTransactions=[], sortKey='date', sortDir=-1;
let barChartObj=null, doughnutObj=null;

function formatDate(d){
  return new Date(d).toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'numeric'});
}

async function loadData(){
  const res=await fetch('/api/transactions');
  const data=await res.json();
  allTransactions=data.transactions||[];
  const now=new Date();
  const monthExp=allTransactions.filter(t=>new Date(t.date).getMonth()===now.getMonth()&&new Date(t.date).getFullYear()===now.getFullYear()).reduce((s,t)=>s+t.amount_inr,0);
  showWarning(monthExp);
  renderTable(); renderBarChart(); renderDoughnut();
  // Load anomaly detection from FastAPI
  mlLoadAnomalies(allTransactions);
}

function getFiltered(){
  const search=document.getElementById('searchInput').value.toLowerCase();
  const cat=document.getElementById('filterCategory').value;
  const from=document.getElementById('filterFrom').value;
  const to=document.getElementById('filterTo').value;
  return allTransactions.filter(t=>{
    if(search&&!t.title.toLowerCase().includes(search)&&!t.category.toLowerCase().includes(search)) return false;
    if(cat&&t.category!==cat) return false;
    if(from&&t.date<from) return false;
    if(to&&t.date>to) return false;
    return true;
  });
}

function filterTable(){ renderTable(); }
function clearFilters(){
  document.getElementById('searchInput').value='';
  document.getElementById('filterCategory').value='';
  document.getElementById('filterFrom').value='';
  document.getElementById('filterTo').value='';
  renderTable();
}

function sortTable(key){
  if(sortKey===key) sortDir*=-1; else {sortKey=key; sortDir=-1;}
  renderTable();
}

function renderTable(){
  const filtered=getFiltered().sort((a,b)=>{
    let av=a[sortKey],bv=b[sortKey];
    if(typeof av==='string'){av=av.toLowerCase();bv=bv.toLowerCase();}
    return av<bv?-sortDir:av>bv?sortDir:0;
  });
  document.getElementById('resultCount').textContent=`Showing ${filtered.length} of ${allTransactions.length} entries`;
  const tbody=document.getElementById('historyBody');
  if(!filtered.length){tbody.innerHTML='<tr><td colspan="7" class="text-center py-4 text-muted">No entries match your filters.</td></tr>';return;}
  tbody.innerHTML=filtered.map((t,i)=>`
    <tr>
      <td class="text-muted">${i+1}</td>
      <td class="fw-semibold">${t.title}</td>
      <td><span class="cat-badge cat-${t.category.toLowerCase().replace(/\s/g,'-')}">${t.category}</span></td>
      <td class="text-muted">${formatDate(t.date)}</td>
      <td class="fw-semibold" style="color:var(--brown-dark)">${fmt(t.amount_inr)}</td>
      <td class="text-muted small">${fmtOrig(t.amount,t.currency)}</td>
      <td>
        <button class="btn btn-sm btn-edit me-1" onclick='openEditModal(${JSON.stringify(t)})' title="Edit"><i class="bi bi-pencil-fill"></i></button>
        <button class="btn btn-sm btn-del" onclick="deleteTransaction(${t.id})" title="Delete"><i class="bi bi-trash-fill"></i></button>
      </td>
    </tr>`).join('');
}

function renderBarChart(){
  // Group by year-month key for proper sorting
  const monthly={};
  allTransactions.forEach(t=>{
    const d=new Date(t.date);
    // Use sortable key YYYY-MM for ordering, display as "Mar 2025"
    const sortableKey=`${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}`;
    monthly[sortableKey]=(monthly[sortableKey]||0)+t.amount_inr;
  });
  // Sort descending: most recent month first
  const sortedEntries=Object.entries(monthly).sort((a,b)=>b[0].localeCompare(a[0])).slice(0,12);
  // Reverse to show oldest→newest left→right
  sortedEntries.reverse();
  const labels=sortedEntries.map(([k])=>{const[y,m]=k.split('-');return new Date(y,m-1).toLocaleString('default',{month:'short',year:'numeric'});});
  const values=sortedEntries.map(([,v])=>v);

  if(barChartObj) barChartObj.destroy();
  const ctx=document.getElementById('barChart').getContext('2d');
  barChartObj=new Chart(ctx,{
    type:'bar',
    data:{labels,datasets:[{label:'Monthly Expenses (₹)',data:values,
      backgroundColor:'rgba(107,66,38,0.75)',borderRadius:8,borderSkipped:false,
      hoverBackgroundColor:'rgba(212,169,106,0.9)'}]},
    options:{responsive:true,plugins:{legend:{display:false}},
      scales:{
        x:{ticks:{font:{family:'DM Sans',size:10}},grid:{display:false}},
        y:{ticks:{font:{family:'DM Sans',size:10},callback:v=>'₹'+v.toLocaleString('en-IN')},grid:{color:'rgba(0,0,0,0.04)'}}
      }}
  });
}

function renderDoughnut(){
  const cats={};
  allTransactions.forEach(t=>{cats[t.category]=(cats[t.category]||0)+t.amount_inr;});
  // Sort by value descending
  const sorted=Object.entries(cats).sort((a,b)=>b[1]-a[1]);
  const labels=sorted.map(e=>e[0]), values=sorted.map(e=>e[1]);
  if(doughnutObj) doughnutObj.destroy();
  const ctx=document.getElementById('doughnutChart').getContext('2d');
  doughnutObj=new Chart(ctx,{
    type:'doughnut',
    data:{labels,datasets:[{data:values,backgroundColor:labels.map(getCatColor),borderWidth:2,borderColor:'#FFFDF8',hoverOffset:6}]},
    options:{responsive:true,cutout:'62%',plugins:{
      legend:{position:'bottom',labels:{font:{family:'DM Sans',size:11},padding:10,usePointStyle:true}},
      tooltip:{callbacks:{label:c=>` ${c.label}: ₹${Number(c.raw).toLocaleString('en-IN',{minimumFractionDigits:2})}`}}
    }}
  });
}

document.getElementById('addModal').addEventListener('show.bs.modal',function(e){if(!e.relatedTarget) return; resetModal();});
loadData();
