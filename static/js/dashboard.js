let pieChartObj=null, lineChartObj=null;

async function loadData(){
  const [txnRes,sumRes]=await Promise.all([fetch('/api/transactions/'),fetch('/api/summary/')]);
  const txnData=await txnRes.json();
  const summary=await sumRes.json();
  const transactions=txnData.transactions||[];
  const now=new Date();

  const monthTxns=transactions.filter(t=>{const d=new Date(t.date);return d.getMonth()===now.getMonth()&&d.getFullYear()===now.getFullYear();});
  const yearTxns=transactions.filter(t=>new Date(t.date).getFullYear()===now.getFullYear());
  const monthExp=monthTxns.reduce((s,t)=>s+t.amount_inr,0);
  const yearExp=yearTxns.reduce((s,t)=>s+t.amount_inr,0);
  const allTotal=transactions.reduce((s,t)=>s+t.amount_inr,0);

  document.getElementById('monthExpense').textContent=fmt(monthExp);
  document.getElementById('yearExpense').textContent=fmt(yearExp);
  document.getElementById('totalCount').textContent=transactions.length;
  document.getElementById('allTotal').textContent=fmt(allTotal);

  showWarning(monthExp);

  const budget=summary.budget||0;
  const budgetSection=document.getElementById('budgetSection');
  if(budget>0){
    budgetSection.classList.remove('d-none');
    const pct=Math.min((monthExp/budget)*100,100);
    const bar=document.getElementById('budgetBar');
    bar.style.width=pct+'%';
    bar.className='progress-bar'+(pct>75?' warn':'');
    document.getElementById('budgetLabel').textContent=`${fmt(monthExp)} / ${fmt(budget)}`;
    document.getElementById('budgetMsg').textContent=pct>=100?'⚠️ Budget exceeded! Time to cut back.':((100-pct).toFixed(1)+'% remaining this month');
    document.getElementById('budgetInput').value=budget;
  }

  // Last 5 — most recent first
  const last5=[...transactions].sort((a,b)=>new Date(b.date)-new Date(a.date)).slice(0,5);
  const tbody=document.getElementById('recentBody');
  if(!last5.length){
    tbody.innerHTML='<tr><td colspan="7" class="text-center py-4 text-muted">No expenses yet — add your first one! 👆</td></tr>';
  } else {
    tbody.innerHTML=last5.map((t,i)=>`
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

  renderPieChart(transactions);
  renderLineChart(transactions);

  // Load AI insights from FastAPI
  loadMLInsights(transactions, summary.budget || 50000);
}

// Format date nicely: "15 Mar 2025"
function formatDate(d){
  return new Date(d).toLocaleDateString('en-IN',{day:'numeric',month:'short',year:'numeric'});
}

function renderPieChart(transactions){
  const cats={};
  transactions.forEach(t=>{cats[t.category]=(cats[t.category]||0)+t.amount_inr;});
  // Sort by value descending
  const sorted=Object.entries(cats).sort((a,b)=>b[1]-a[1]);
  const labels=sorted.map(e=>e[0]), values=sorted.map(e=>e[1]);
  if(pieChartObj) pieChartObj.destroy();
  const ctx=document.getElementById('pieChart').getContext('2d');
  pieChartObj=new Chart(ctx,{
    type:'pie',
    data:{labels,datasets:[{data:values,backgroundColor:labels.map(getCatColor),borderWidth:2,borderColor:'#FFFDF8',hoverOffset:6}]},
    options:{responsive:true,plugins:{
      legend:{position:'bottom',labels:{font:{family:'DM Sans',size:11},padding:10,usePointStyle:true}},
      tooltip:{callbacks:{label:c=>` ${c.label}: ₹${Number(c.raw).toLocaleString('en-IN',{minimumFractionDigits:2})} (${((c.raw/values.reduce((a,b)=>a+b,0))*100).toFixed(1)}%)`}}
    }}
  });
}

function renderLineChart(transactions){
  // Sort by date ascending (oldest → newest = left → right)
  const byDate={};
  [...transactions].sort((a,b)=>new Date(a.date)-new Date(b.date))
    .forEach(t=>{byDate[t.date]=(byDate[t.date]||0)+t.amount_inr;});
  const labels=Object.keys(byDate).map(d=>formatDate(d));
  const values=Object.values(byDate);
  if(lineChartObj) lineChartObj.destroy();
  const ctx=document.getElementById('lineChart').getContext('2d');
  lineChartObj=new Chart(ctx,{
    type:'line',
    data:{labels,datasets:[{label:'Expenses (₹)',data:values,borderColor:'#6B4226',
      backgroundColor:'rgba(107,66,38,0.08)',fill:true,tension:0.4,pointRadius:5,
      pointBackgroundColor:'#D4A96A',pointBorderColor:'#6B4226',pointHoverRadius:7}]},
    options:{responsive:true,plugins:{legend:{display:false}},
      scales:{
        x:{ticks:{font:{family:'DM Sans',size:9},maxRotation:45},grid:{color:'rgba(0,0,0,0.04)'}},
        y:{ticks:{font:{family:'DM Sans',size:10},callback:v=>'₹'+v.toLocaleString('en-IN')},grid:{color:'rgba(0,0,0,0.04)'}}
      }}
  });
}

document.getElementById('addModal').addEventListener('show.bs.modal',function(e){ if(!e.relatedTarget) return; resetModal(); });
loadData();

// ── ML Integrations (called after loadData) ───────────────────
async function loadMLInsights(transactions, budget) {
  mlLoadSentiment(transactions, budget);
  mlLoadSummary(transactions, budget);
  mlLoadForecast(transactions);
}
