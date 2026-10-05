"use client";
import type {Role,InputMethod} from '../../shared/types/comparison';
import {useJudgeLocale} from './JudgeLocale';
type Props={role:Role;method:InputMethod;value:string;busy:boolean;setMethod:(v:InputMethod)=>void;
  setValue:(v:string)=>void;setFile:(file:File|undefined)=>void};
export function MaterialInput({role,method,value,busy,setMethod,setValue,setFile}:Props){const {t}=useJudgeLocale();
  const name=role==='source'?t('Arabic source','Арабский оригинал'):t('Text ','Перевод ')+role.toUpperCase();
  return <section className="material-input"><h3>{name}</h3>
    <label>{t('Input method','Способ ввода')}<select aria-label={name+' '+t('input method','способ ввода')} disabled={busy} value={method} onChange={e=>setMethod(e.target.value as InputMethod)}>
      <option value="file">{t('File','Файл')}</option><option value="text">{t('Text','Текст')}</option><option value="url">URL</option>
    </select></label>
    <label>{method==='file'?t('Document','Документ'):method==='url'?'URL':t('Paste text','Вставьте текст')}
      {method==='file'?<input type="file" required disabled={busy} accept=".txt,.md,.docx,.pdf,.html" onChange={e=>setFile(e.target.files?.[0])}/>
      :method==='url'?<input type="url" required disabled={busy} placeholder="https://…" value={value} onChange={e=>setValue(e.target.value)}/>
      :<textarea required disabled={busy} rows={7} dir="auto" value={value} onChange={e=>setValue(e.target.value)}/>}
    </label>
  </section>;
}
