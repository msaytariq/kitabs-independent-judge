"use client";
import {useState} from 'react';
import type {Draft,Inputs,Role,InputMethod} from '../../shared/types/comparison';
import {Materials} from './Materials';
import {MaterialInput} from './MaterialInput';
import {useJudgeLocale} from './JudgeLocale';
import {inputWarning} from '../../shared/i18n/intake';
import {KitabsAction} from './KitabsAction';
type Props = {draft:Draft|null;busy:boolean;intake:(inputs:Inputs,files:Partial<Record<Role,File>>|null,methods?:Record<Role,InputMethod>,pipelineRequestId?:string)=>Promise<void>;
  prepare:(profile:string)=>Promise<void>;clearDraft:()=>void};
export function OwnMaterials({draft,busy,intake,prepare,clearDraft}:Props) {
  const {t,locale}=useJudgeLocale();
  const [profile,setProfile]=useState('islamic-scholarly'),[confirmed,setConfirmed]=useState(false);
  const [methods,setMethods]=useState<Record<Role,InputMethod>>({source:'file',a:'file',b:'file'});
  const [bKitabs,setBKitabs]=useState(true);  // B comes from the Kitabs.ai autopilot until the jury selects another input
  const [inputs,setInputs]=useState<Inputs>({source:'',a:'',b:'',source_language:'ar',target_language:'en'});
  const [files,setFiles]=useState<Partial<Record<Role,File>>>({});
  const [localError,setLocalError]=useState('');
  const [pipelineRequestId,setPipelineRequestId]=useState<string>();
  if(draft)return <><Materials open texts={{source:draft.materials.source.text,a:draft.materials.a.text,b:draft.materials.b.text}}/>
    <section className="panel"><h2>{t('Confirm the source boundaries','Подтвердите границы')}</h2>
      <p>{t('All three passages must start and end at the same source locations. Keep internal translation differences for the judge.','Все три фрагмента должны начинаться и заканчиваться на одном смысловом месте. Различия внутри переводов сохраняются для судьи.')}</p>
      {Object.values(draft.materials).map(m=>m.warnings.length>0&&<p className="notice" key={m.filename}>{m.filename}: {m.warnings.map(w=>locale==='ru'?inputWarning(w):w).join('; ')}</p>)}
      <label className="check"><input type="checkbox" checked={confirmed} onChange={e=>setConfirmed(e.target.checked)}/>{t('I checked the start and end of all three passages.','Я сверил начало и конец всех трёх фрагментов.')}</label>
      <div className="actions"><button className="primary" disabled={busy||!confirmed} onClick={()=>void prepare(profile)}>{t('Save comparison','Сохранить сравнение')}</button>
        <button disabled={busy} onClick={()=>{clearDraft();setConfirmed(false);}}>{t('Change inputs','Изменить материалы')}</button></div>
    </section></>;
  return <section className="panel own-materials"><h2>{t('One source. Two translations.','Один оригинал. Два перевода.')}</h2>
    <p>{t('Up to 10 physical PDF pages and 18,000 source characters. Text and DOCX use 1,800-character page units. Nothing is truncated.','До 10 физических страниц PDF и 18 000 знаков оригинала. Для текста и DOCX — условные страницы по 1800 знаков. Ничего не обрезается.')}</p>
    <form onSubmit={e=>{e.preventDefault();setLocalError('');setConfirmed(false);
      if(bKitabs){setLocalError(t('Start the autopilot and wait for B, or select another input for B.','Запустите автопилот и дождитесь B или выберите для B другой способ ввода.'));return;}
      if((['source','a','b'] as const).some(r=>methods[r]==='file'&&!files[r])){setLocalError(t('Choose a file for each file input.','Выберите файл для каждого файлового поля.'));return;}
      void intake(inputs,files,methods,pipelineRequestId);}}>
      <div className="material-grid">{(['source','a','b'] as const).map(role=><MaterialInput key={role} role={role} busy={busy}
        method={role==='b'&&bKitabs?'kitabs':methods[role]} value={inputs[role]}
        setMethod={v=>{if(role==='b')setBKitabs(v==='kitabs');if(v!=='kitabs')setMethods({...methods,[role]:v});}}
        setValue={v=>setInputs({...inputs,[role]:v})} setFile={v=>setFiles({...files,[role]:v})}
        kitabs={role==='b'?<KitabsAction busy={busy} source={{method:methods.source,value:inputs.source,file:files.source,source_language:inputs.source_language,target_language:inputs.target_language}}
          onReady={job=>{if(job.result){setInputs(current=>({...current,source:job.source,b:job.result!.text}));
            setMethods(current=>({...current,source:'text',b:'text'}));setBKitabs(false);setPipelineRequestId(job.id);}}}/>:undefined}/>)}</div>
      <details><summary>{t('Languages and review profile','Языки и профиль проверки')}</summary><div className="row">
        <label>{t('Source language','Язык оригинала')}<input required value={inputs.source_language} onChange={e=>setInputs({...inputs,source_language:e.target.value})}/></label>
        <label>{t('Translation language','Язык переводов')}<input required value={inputs.target_language} onChange={e=>setInputs({...inputs,target_language:e.target.value})}/></label></div>
        <label>{t('Review profile','Профиль')}<select value={profile} onChange={e=>setProfile(e.target.value)}>
          <option value="general">{t('General','Общий')}</option><option value="islamic-scholarly">{t('Islamic scholarly texts','Исламская научная литература')}</option></select></label></details>
      <p className="muted">{t('TXT, MD, DOCX, HTML or selectable-text PDF · 20 MiB each · no OCR','TXT, MD, DOCX, HTML или PDF с текстовым слоем · по 20 МиБ · без OCR')}</p>
      {localError&&<p role="alert">{localError}</p>}<button className="primary" disabled={busy}>{t('Check materials','Проверить материалы')}</button>
    </form></section>;
}
