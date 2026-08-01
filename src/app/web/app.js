const form=document.querySelector('#project-form'),list=document.querySelector('#projects'),empty=document.querySelector('#empty'),statusBox=document.querySelector('#status'),variantSection=document.querySelector('#variant-section'),variantsBox=document.querySelector('#variants');
const say=message=>{statusBox.textContent=message};
const formTitle=document.querySelector('#form-title'),saveProjectButton=document.querySelector('#save-project'),cancelEditButton=document.querySelector('#cancel-edit');
let editingProjectId=null;
function finishEdit(){editingProjectId=null;formTitle.textContent='Create content';saveProjectButton.textContent='Save project';cancelEditButton.hidden=true;form.removeAttribute('data-editing-project')}
function startEdit(project){
  editingProjectId=project.id;formTitle.textContent='Edit project';saveProjectButton.textContent='Update project';cancelEditButton.hidden=false;form.dataset.editingProject=project.id;
  form.title.value=project.title;form.body.value=project.body;
  for(const box of form.querySelectorAll('[name=formats]'))box.checked=project.target_formats.includes(box.value);
  form.voice.value=project.brand_voice;document.querySelector('#instructions').value=project.custom_instructions||'';
  document.querySelector('#draft-state').textContent=`Editing ${project.title}. Existing generated versions will be preserved.`;
  formTitle.scrollIntoView({behavior:'smooth',block:'start'});form.title.focus();
}
cancelEditButton.addEventListener('click',()=>{finishEdit();form.reset();form.querySelector('[value=linkedin_post]').checked=true;localStorage.removeItem('repurposeai-project-draft');document.querySelector('#draft-state').textContent='Edit cancelled. Local draft cleared.';say('Project edit cancelled.')});
function errors(){for(const id of ['title','body','formats'])document.querySelector(`#${id}-error`).textContent=''}
function validate(){errors();let ok=true;const title=form.title.value.trim(),body=form.body.value.trim(),formats=[...form.querySelectorAll('[name=formats]:checked')];if(!title){document.querySelector('#title-error').textContent='Add a project title.';ok=false}if(!body){document.querySelector('#body-error').textContent='Add source content.';ok=false}if(!formats.length){document.querySelector('#formats-error').textContent='Choose at least one destination.';ok=false}return ok}
function variantCard(variant){const article=document.createElement('article');article.className='variant-card';const heading=document.createElement('h3');heading.textContent=variant.format.replaceAll('_',' ');const meta=document.createElement('p');meta.className='meta';meta.textContent=`Version ${variant.version} • ${variant.status} • ${variant.generation_mode.replaceAll('_',' ')}`;const text=document.createElement('textarea');text.value=variant.content;text.rows=8;text.setAttribute('aria-label',`${heading.textContent} content`);const save=document.createElement('button');save.type='button';save.textContent='Save revision';save.onclick=async()=>{save.disabled=true;say(`Saving ${heading.textContent}…`);const response=await fetch(`/api/v1/projects/${variant.project_id}/variants/${variant.id}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({content:text.value,status:'draft'})});save.disabled=false;if(!response.ok){say('Revision could not be saved. Your text is still here.');return}say(`${heading.textContent} revision saved.`);await showVariants(variant.project_id);await loadSummary()};const approve=document.createElement('button');approve.type='button';approve.textContent='Approve';approve.onclick=async()=>{approve.disabled=true;const response=await fetch(`/api/v1/projects/${variant.project_id}/variants/${variant.id}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({content:text.value,status:'approved'})});approve.disabled=false;if(!response.ok){say('Draft could not be approved.');return}say(`${heading.textContent} approved.`);await showVariants(variant.project_id);await loadSummary()};const copy=document.createElement('button');copy.type='button';copy.textContent='Copy';copy.onclick=async()=>{await navigator.clipboard.writeText(text.value);say(`${heading.textContent} copied.`)};const history=document.createElement('button');history.type='button';history.textContent='View history';history.onclick=async()=>{history.disabled=true;const response=await fetch(`/api/v1/projects/${variant.project_id}/variants?include_history=true`);history.disabled=false;if(!response.ok){say('Version history could not be loaded.');return}const all=await response.json();const versions=all.filter(item=>item.format===variant.format);let details=article.querySelector('.history-list');if(details){details.remove();return}details=document.createElement('details');details.className='history-list';details.open=true;const summary=document.createElement('summary');summary.textContent=`Version history (${versions.length})`;details.append(summary,...versions.map(item=>{const row=document.createElement('div');row.className='history-item';const label=document.createElement('span');label.textContent=`Version ${item.version} • ${item.status} • ${new Date(item.created_at).toLocaleString()}`;const restore=document.createElement('button');restore.type='button';restore.textContent='Restore this version';restore.onclick=async()=>{restore.disabled=true;say(`Restoring version ${item.version}…`);const restored=await fetch(`/api/v1/projects/${item.project_id}/variants/${item.id}/restore`,{method:'POST'});restore.disabled=false;if(!restored.ok){say('Version could not be restored.');return}say(`Version ${item.version} restored as a new draft.`);await showVariants(item.project_id);await loadSummary()};row.append(label,restore);return row}));article.append(details)};const actions=document.createElement('div');actions.className='actions';actions.append(save,approve,copy,history);article.append(heading,meta,text,actions);return article}
async function showVariants(projectId){const response=await fetch(`/api/v1/projects/${projectId}/variants`);if(!response.ok)return;const variants=await response.json();variantsBox.replaceChildren(...variants.map(variantCard));variantSection.hidden=!variants.length;if(variants.length)variantSection.scrollIntoView({behavior:'smooth',block:'start'})}
async function generate(project){say(`Generating ${project.target_formats.length} drafts for ${project.title}…`);const response=await fetch(`/api/v1/projects/${project.id}/generate`,{method:'POST'});if(!response.ok){say('Draft generation failed. Your project is safe.');return}const result=await response.json();say(result.warning||`${result.variants.length} drafts generated.`);await showVariants(project.id);await loadSummary()}
function card(project){const li=document.createElement('li');li.className='project-card';const title=document.createElement('h3');title.textContent=project.title;const meta=document.createElement('p');meta.className='meta';meta.textContent=`${project.target_formats.length} formats • Updated ${new Date(project.updated_at).toLocaleString()}`;const pill=document.createElement('span');pill.className='status-pill';pill.textContent=project.status;const generateButton=document.createElement('button');generateButton.type='button';generateButton.className='primary';generateButton.textContent='Generate drafts';generateButton.onclick=()=>generate(project);const view=document.createElement('button');view.type='button';view.textContent='View drafts';view.onclick=()=>showVariants(project.id);const edit=document.createElement('button');edit.type='button';edit.textContent='Edit project';edit.onclick=()=>startEdit(project);const duplicate=document.createElement('button');duplicate.type='button';duplicate.textContent='Create similar';duplicate.onclick=async()=>{const requested=window.prompt('New project title',`${project.title} copy`);if(requested===null)return;const response=await fetch(`/api/v1/projects/${project.id}/duplicate`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({title:requested.trim()||null})});if(!response.ok){say('Similar project could not be created.');return}const created=await response.json();say(`${created.title} created without copying drafts or publication state.`);await load();await loadSummary()};const archive=document.createElement('button');archive.type='button';archive.textContent='Archive';archive.setAttribute('aria-label',`Archive ${project.title}`);archive.onclick=async()=>{await fetch(`/api/v1/projects/${project.id}`,{method:'DELETE'});say(`${project.title} archived.`);variantSection.hidden=true;load();loadSummary()};const actions=document.createElement('div');actions.className='actions';actions.append(generateButton,view,edit,duplicate,archive);li.append(title,meta,pill,actions);return li}
let currentQuery='';
async function load(){say('Loading projects…');try{const url=currentQuery?`/api/v1/projects?q=${encodeURIComponent(currentQuery)}`:'/api/v1/projects';const response=await fetch(url);if(!response.ok)throw new Error('Could not load projects');const projects=await response.json();list.replaceChildren(...projects.map(card));empty.hidden=projects.length>0;say(projects.length?`${projects.length} project${projects.length===1?'':'s'} loaded.`:'No saved projects.')}catch(error){say(`${error.message}. Try Refresh.`)}}
form.addEventListener('submit',async event=>{event.preventDefault();if(!validate()){say('Fix the highlighted fields.');document.querySelector('.error:not(:empty)')?.previousElementSibling?.focus();return}const payload={title:form.title.value.trim(),body:form.body.value.trim(),source_format:'blog_post',target_formats:[...form.querySelectorAll('[name=formats]:checked')].map(x=>x.value),brand_voice:form.voice.value,custom_instructions:document.querySelector('#instructions').value.trim()||null};const editing=editingProjectId!==null;say(editing?'Updating project…':'Saving project…');const response=await fetch(editing?`/api/v1/projects/${editingProjectId}`:'/api/v1/projects',{method:editing?'PATCH':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});if(!response.ok){say(`${editing?'Project update':'Project'} could not be saved. Your input is still here.`);return}const project=await response.json();say(editing?`${project.title} updated. Existing draft history was preserved.`:`${project.title} saved. You can generate drafts now.`);finishEdit();form.reset();localStorage.removeItem('repurposeai-project-draft');document.querySelector('#draft-state').textContent='Local draft cleared after save.';form.querySelector('[value=linkedin_post]').checked=true;await load();await loadSummary()});
document.querySelector('#refresh').addEventListener('click',load);load();

const recipeSelect=document.querySelector('#recipe-select');
let savedRecipes=[];
async function loadRecipes(){
  try{
    const response=await fetch('/api/v1/recipes');
    if(!response.ok)throw new Error('Could not load recipes');
    savedRecipes=await response.json();
    const options=savedRecipes.map(recipe=>{
      const option=document.createElement('option');
      option.value=recipe.id;option.textContent=recipe.name;return option;
    });
    recipeSelect.replaceChildren(new Option('No recipe selected',''),...options);
  }catch(error){say(`${error.message}. Project creation is still available.`)}
}
document.querySelector('#apply-recipe').addEventListener('click',()=>{
  const recipe=savedRecipes.find(item=>item.id===recipeSelect.value);
  if(!recipe){say('Choose a saved recipe first.');return}
  for(const box of form.querySelectorAll('[name=formats]'))box.checked=recipe.target_formats.includes(box.value);
  form.voice.value=recipe.brand_voice;
  document.querySelector('#instructions').value=recipe.custom_instructions||'';
  say(`${recipe.name} applied. Add the title and source content.`);
});
document.querySelector('#save-recipe').addEventListener('click',async()=>{
  const formats=[...form.querySelectorAll('[name=formats]:checked')].map(item=>item.value);
  if(!formats.length){document.querySelector('#formats-error').textContent='Choose at least one destination.';say('Choose formats before saving a recipe.');return}
  const suggested=form.title.value.trim()?`${form.title.value.trim()} recipe`:'My content recipe';
  const name=window.prompt('Recipe name',suggested);
  if(!name||!name.trim()){say('Recipe was not saved.');return}
  const response=await fetch('/api/v1/recipes',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:name.trim(),target_formats:formats,brand_voice:form.voice.value,custom_instructions:document.querySelector('#instructions').value.trim()||null})});
  if(!response.ok){say('Recipe could not be saved. Check its name and formats.');return}
  const recipe=await response.json();
  say(`${recipe.name} saved for reuse.`);
  await loadRecipes();recipeSelect.value=recipe.id;
});
loadRecipes();

// Daily-use enhancements: attention summary, search, and privacy-preserving local draft recovery.
async function loadSummary(){
  try{
    const response=await fetch('/api/v1/workspace/summary');
    if(!response.ok)return;
    const data=await response.json();
    document.querySelector('#summary-projects').textContent=data.active_projects;
    document.querySelector('#summary-needs-drafts').textContent=data.projects_without_drafts;
    document.querySelector('#summary-drafts').textContent=data.draft_variants;
    document.querySelector('#summary-approved').textContent=data.approved_variants;
    document.querySelector('#summary-fallback').textContent=data.fallback_variants_needing_review;
    const summary=document.querySelector('#workspace-summary');
    summary.setAttribute('aria-label',`Workspace attention summary: ${data.active_projects} active projects, ${data.projects_without_drafts} need drafts, ${data.draft_variants} drafts to review, ${data.approved_variants} approved, ${data.fallback_variants_needing_review} fallback drafts needing review.`);
  }catch(_error){/* Summary is supplementary; the core workspace remains available. */}
}
const searchInput=document.querySelector('#project-search');
document.querySelector('#search-button').addEventListener('click',()=>{currentQuery=searchInput.value.trim();load()});
document.querySelector('#clear-search').addEventListener('click',()=>{searchInput.value='';currentQuery='';load();searchInput.focus()});
searchInput.addEventListener('keydown',event=>{if(event.key==='Enter'){event.preventDefault();currentQuery=searchInput.value.trim();load()}});

const localDraftKey='repurposeai-project-draft';
const draftState=document.querySelector('#draft-state');
function draftSnapshot(){return {title:form.title.value,body:form.body.value,formats:[...form.querySelectorAll('[name=formats]:checked')].map(item=>item.value),voice:form.voice.value,instructions:document.querySelector('#instructions').value,savedAt:new Date().toISOString()}}
let autosaveTimer;
form.addEventListener('input',()=>{clearTimeout(autosaveTimer);draftState.textContent='Saving local draft…';autosaveTimer=setTimeout(()=>{try{localStorage.setItem(localDraftKey,JSON.stringify(draftSnapshot()));draftState.textContent=`Local draft saved at ${new Date().toLocaleTimeString()}.`}catch(_error){draftState.textContent='Local draft could not be saved in this browser.'}},350)});
form.addEventListener('reset',()=>{finishEdit();localStorage.removeItem(localDraftKey);draftState.textContent='Local draft cleared.'});
function restoreLocalDraft(){
  try{
    const raw=localStorage.getItem(localDraftKey);if(!raw)return;
    const draft=JSON.parse(raw);if(!draft.title&&!draft.body)return;
    form.title.value=draft.title||'';form.body.value=draft.body||'';
    for(const box of form.querySelectorAll('[name=formats]'))box.checked=(draft.formats||[]).includes(box.value);
    if([...form.voice.options].some(option=>option.value===draft.voice))form.voice.value=draft.voice;
    document.querySelector('#instructions').value=draft.instructions||'';
    draftState.textContent=`Recovered an unsaved local draft from ${new Date(draft.savedAt).toLocaleString()}.`;
  }catch(_error){localStorage.removeItem(localDraftKey)}
}
restoreLocalDraft();loadSummary();
