const $ = (id) => document.getElementById(id);
const DEFAULT_API = "http://127.0.0.1:8000";
let apiBase = localStorage.getItem("nexrun_api") || DEFAULT_API;
$("apiBase").value = apiBase.replace(/\/$/,"");

function setStatus(text){$("connection").textContent=text}
function endpoint(path){return apiBase.replace(/\/$/,"")+path}
async function request(path, options={}){
  const r=await fetch(endpoint(path),{...options,headers:{"Content-Type":"application/json",...(options.headers||{})}});
  if(!r.ok){let msg="Request failed ("+r.status+")";try{const j=await r.json();msg=j.detail||msg}catch{}throw new Error(msg)}
  return r.json();
}
async function checkHealth(){
  try{const h=await request("/health");setStatus("Connected · "+h.status);return true}
  catch(e){setStatus("Not connected");return false}
}
$("saveUrl").onclick=async()=>{apiBase=$("apiBase").value.trim().replace(/\/$/,"");localStorage.setItem("nexrun_api",apiBase);await checkHealth()};
$("health").onclick=checkHealth;
$("refresh").onclick=loadTasks;

$("run").onclick=async()=>{
  const prompt=$("prompt").value.trim();if(!prompt){alert("First type a task.");return}
  $("run").disabled=true;$("run").textContent="Sending…";
  try{
    const data=await request("/tasks",{method:"POST",body:JSON.stringify({prompt,agent:$("agent").value})});
    $("prompt").value="";await loadTasks();pollTask(data.id);
  }catch(e){alert(e.message)}
  finally{$("run").disabled=false;$("run").textContent="Run task ↗"}
};
async function loadTasks(){
  try{
    const data=await request("/tasks");const host=$("tasks");
    if(!data.tasks.length){host.innerHTML='<p class="hint">No tasks yet.</p>';return}
    host.innerHTML="";
    data.tasks.forEach(t=>{
      const el=document.createElement("div");el.className="task";
      const top=document.createElement("div");top.className="tasktop";
      const state=document.createElement("span");state.textContent=(t.status||"").toUpperCase();
      const date=document.createElement("span");date.textContent=t.created_at||"";
      top.append(state,date);
      const p=document.createElement("div");p.style.marginTop="8px";p.textContent=t.prompt;
      const b=document.createElement("button");b.className="btn";b.style.marginTop="9px";b.textContent="View result";
      b.onclick=()=>showTask(t.id);
      el.append(top,p,b);host.append(el);
    });
  }catch(e){$("tasks").innerHTML='<p class="hint">Cannot load tasks: '+escapeHtml(e.message)+'</p>'}
}
function escapeHtml(s){return String(s).replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]))}
async function showTask(id){
  try{
    const t=await request("/tasks/"+id);$("resultPanel").classList.remove("hidden");
    $("result").textContent=t.result||t.error||"Task is still running. Refresh in a moment.";
    $("resultPanel").scrollIntoView({behavior:"smooth"});
  }catch(e){alert(e.message)}
}
async function pollTask(id){
  for(let i=0;i<30;i++){
    await new Promise(r=>setTimeout(r,3000));
    try{const t=await request("/tasks/"+id);await loadTasks();if(["completed","failed"].includes(t.status)){await showTask(id);return}}catch{return}
  }
}
$("mic").onclick=()=>{
  const SR=window.SpeechRecognition||window.webkitSpeechRecognition;
  if(!SR){alert("Speech input is not supported in this browser. Try Chrome.");return}
  const rec=new SR();rec.lang="en-IN";rec.interimResults=false;
  rec.onresult=e=>{$("prompt").value+=($("prompt").value?" ":"")+e.results[0][0].transcript};
  rec.onerror=()=>alert("Voice input could not start. Check microphone permission.");
  rec.start();
};
$("speak").onclick=()=>{const text=$("result").textContent;if(!text){alert("No result to read yet.");return}if(!("speechSynthesis" in window)){alert("Speech output unavailable.");return}speechSynthesis.cancel();speechSynthesis.speak(new SpeechSynthesisUtterance(text))};
$("stopSpeak").onclick=()=>speechSynthesis.cancel();
checkHealth();loadTasks();
if("serviceWorker" in navigator) navigator.serviceWorker.register("sw.js").catch(()=>{});
