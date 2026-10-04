"use client";
import {useState} from 'react';
import type {Draft,Inputs,Role} from '../../shared/types/comparison';
import {Materials} from './Materials';
import {inputWarning} from '../../shared/i18n/intake';
type Props = {draft:Draft|null;busy:boolean;intake:(inputs:Inputs,files:Record<Role,File>|null)=>Promise<void>;
  prepare:(profile:string)=>Promise<void>; clearDraft:()=>void};
export function OwnMaterials({draft,busy,intake,prepare,clearDraft}:Props) {
  const [mode,setMode] = useState('files'), [profile,setProfile] = useState('islamic-scholarly');
  const [confirmed,setConfirmed] = useState(false);
  const [inputs,setInputs] = useState<Inputs>({source:'',a:'',b:'',source_language:'ar',target_language:'en'});
  const [files,setFiles] = useState<Partial<Record<Role,File>>>({});
  const [localError,setLocalError] = useState('');
  if(draft) return <>
    <Materials open texts={{source:draft.materials.source.text,a:draft.materials.a.text,b:draft.materials.b.text}}/>
    <section className="panel">
      <h2>Проверьте границы</h2><p>Все три фрагмента должны начинаться и заканчиваться на одном смысловом месте. Различия внутри перевода сохраняются для проверки.</p>
      {Object.entries(draft.materials).map(([role,m])=>m.warnings.length>0 && <p className="notice" key={role}>При чтении файла {m.filename} получены предупреждения: {m.warnings.map(inputWarning).join('; ')}</p>)}
      <label className="check"><input type="checkbox" checked={confirmed} onChange={e=>setConfirmed(e.target.checked)}/>Я сверил начало и конец всех трёх фрагментов.</label>
      <div className="actions"><button className="primary" disabled={busy||!confirmed} onClick={()=>void prepare(profile)}>Сохранить сравнение</button>
      <button disabled={busy} onClick={()=>{clearDraft();setConfirmed(false);}}>Изменить материалы</button></div>
      <p className="muted">После подтверждения можно запустить сравнение. Уже сохранённые оценки повторно не оплачиваются.</p>
    </section></>;
  return <section className="panel own-materials">
    <h2>Добавьте один оригинал и два перевода</h2>
    <p>Подойдут тексты любых авторов и систем. Загрузите соответствующие фрагменты, до 18 000 знаков оригинала.</p>
    <div className="tabs"><button disabled={busy} aria-pressed={mode==='text'} className={mode==='text'?'selected':''} onClick={()=>setMode('text')}>Вставить текст</button><button disabled={busy} aria-pressed={mode==='files'} className={mode==='files'?'selected':''} onClick={()=>setMode('files')}>Загрузить файлы</button></div>
    <form onSubmit={e=>{e.preventDefault();setLocalError('');setConfirmed(false);
      if(mode==='files'&&(!files.source||!files.a||!files.b)){setLocalError('Выберите все три файла.');return;}
      void intake(inputs,mode==='files'?files as Record<Role,File>:null);}}>
      <div className="row"><label>Язык оригинала (код)<input required value={inputs.source_language} onChange={e=>setInputs({...inputs,source_language:e.target.value})}/></label>
      <label>Язык переводов (код)<input required value={inputs.target_language} onChange={e=>setInputs({...inputs,target_language:e.target.value})}/></label></div>
      <p className="muted">ar — арабский, ru — русский, en — английский.</p>
      <div className="material-grid">{(['source','a','b'] as const).map(role=><label key={role}>
        {role==='source'?'Оригинал':`Перевод ${role.toUpperCase()}`}
        {mode==='text'?<textarea required rows={7} dir="auto" value={inputs[role]} onChange={e=>setInputs({...inputs,[role]:e.target.value})}/>
        :<input type="file" required accept=".txt,.md,.docx,.pdf" onChange={e=>setFiles({...files,[role]:e.target.files?.[0]})}/>}
      </label>)}</div>
      <details><summary>Профиль проверки</summary><label>Профиль<select value={profile} onChange={e=>setProfile(e.target.value)}>
        <option value="general">Общее качество текста</option><option value="islamic-scholarly">Исламская литература: цитаты, ссылки и научный аппарат</option>
      </select></label></details>
      <p className="muted">TXT, MD, DOCX или PDF с текстовым слоем · до 20 МБ каждый · без OCR</p>
      {localError&&<p role="alert">{localError}</p>}
      <button className="primary" disabled={busy}>Проверить материалы</button>
    </form>
  </section>;
}
