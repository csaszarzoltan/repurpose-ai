const form=document.querySelector('#project-form'),list=document.querySelector('#projects'),empty=document.querySelector('#empty'),statusBox=document.querySelector('#status'),variantSection=document.querySelector('#variant-section'),variantsBox=document.querySelector('#variants');
const say=message=>{statusBox.textContent=message};
function errors(){for(const id of ['title','body','formats'])document.querySelector(`#${id}-error`).textContent=''}
function validate(){errors();let ok=true;const title=form.title.value.trim(),body=form.body.value.trim(),formats=[...form.querySelectorAll('[name=formats]:checked')];if(!title){document.querySelector('#title-error').textContent='Add a project title.';ok=false}if(!body){document.querySelector('#body-error').textContent='Add source content.';ok=false}if(!formats.length){document.querySelector('#formats-error').textContent='Choose at least one destination.';ok=false}return ok}
function variantCard(variant){const article=document.createElement('article');article.className='variant-card';const heading=document.createElement('h3');heading.textContent=variant.format.replaceAll('_',' ');const meta=document.createElement('p');meta.className='meta';meta.textContent=`Version ${variant.version} • ${variant.status} • ${variant.generation_mode.replaceAll('_',' ')}`;const text=document.createElement('textarea');text.value=variant.content;text.rows=8;text.setAttribute('aria-label',`${heading.textContent} content`);const save=document.createElement('button');save.type='button';save.textContent='Save revision';save.onclick=async()=>{save.disabled=true;say(`Saving ${heading.textContent}…`);const response=await fetch(`/api/v1/projects/${variant.project_id}/variants/${variant.id}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({content:text.value,status:'draft'})});save.disabled=false;if(!response.ok){say('Revision could not be saved. Your text is still here.');return}say(`${heading.textContent} revision saved.`);await showVariants(variant.project_id)};const approve=document.createElement('button');approve.type='button';approve.textContent='Approve';approve.onclick=async()=>{approve.disabled=true;const response=await fetch(`/api/v1/projects/${variant.project_id}/variants/${variant.id}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({content:text.value,status:'approved'})});approve.disabled=false;if(!response.ok){say('Draft could not be approved.');return}say(`${heading.textContent} approved.`);await showVariants(variant.project_id)};const copy=document.createElement('button');copy.type='button';copy.textContent='Copy';copy.onclick=async()=>{await navigator.clipboard.writeText(text.value);say(`${heading.textContent} copied.`)};const actions=document.createElement('div');actions.className='actions';actions.append(save,approve,copy);article.append(heading,meta,text,actions);return article}
async function showVariants(projectId){const response=await fetch(`/api/v1/projects/${projectId}/variants`);if(!response.ok)return;const variants=await response.json();variantsBox.replaceChildren(...variants.map(variantCard));variantSection.hidden=!variants.length;if(variants.length)variantSection.scrollIntoView({behavior:'smooth',block:'start'})}
async function generate(project){say(`Generating ${project.target_formats.length} drafts for ${project.title}…`);const response=await fetch(`/api/v1/projects/${project.id}/generate`,{method:'POST'});if(!response.ok){say('Draft generation failed. Your project is safe.');return}const result=await response.json();say(result.warning||`${result.variants.length} drafts generated.`);await showVariants(project.id)}
function card(project){const li=document.createElement('li');li.className='project-card';const title=document.createElement('h3');title.textContent=project.title;const meta=document.createElement('p');meta.className='meta';meta.textContent=`${project.target_formats.length} formats • Updated ${new Date(project.updated_at).toLocaleString()}`;const pill=document.createElement('span');pill.className='status-pill';pill.textContent=project.status;const generateButton=document.createElement('button');generateButton.type='button';generateButton.className='primary';generateButton.textContent='Generate drafts';generateButton.onclick=()=>generate(project);const view=document.createElement('button');view.type='button';view.textContent='View drafts';view.onclick=()=>showVariants(project.id);const archive=document.createElement('button');archive.type='button';archive.textContent='Archive';archive.setAttribute('aria-label',`Archive ${project.title}`);archive.onclick=async()=>{await fetch(`/api/v1/projects/${project.id}`,{method:'DELETE'});say(`${project.title} archived.`);variantSection.hidden=true;load()};const actions=document.createElement('div');actions.className='actions';actions.append(generateButton,view,archive);li.append(title,meta,pill,actions);return li}
async function load(){say('Loading projects…');try{const response=await fetch('/api/v1/projects');if(!response.ok)throw new Error('Could not load projects');const projects=await response.json();list.replaceChildren(...projects.map(card));empty.hidden=projects.length>0;say(projects.length?`${projects.length} project${projects.length===1?'':'s'} loaded.`:'No saved projects.')}catch(error){say(`${error.message}. Try Refresh.`)}}
form.addEventListener('submit',async event=>{event.preventDefault();if(!validate()){say('Fix the highlighted fields.');document.querySelector('.error:not(:empty)')?.previousElementSibling?.focus();return}const payload={title:form.title.value.trim(),body:form.body.value.trim(),source_format:'blog_post',target_formats:[...form.querySelectorAll('[name=formats]:checked')].map(x=>x.value),brand_voice:form.voice.value,custom_instructions:document.querySelector('#instructions').value.trim()||null};say('Saving project…');const response=await fetch('/api/v1/projects',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});if(!response.ok){say('Project could not be saved. Your input is still here.');return}const project=await response.json();say(`${project.title} saved. You can generate drafts now.`);form.reset();form.querySelector('[value=linkedin_post]').checked=true;await load()});
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
