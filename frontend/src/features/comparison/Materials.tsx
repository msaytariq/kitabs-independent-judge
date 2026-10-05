"use client";
import type {Role} from '../../shared/types/comparison';
import {useJudgeLocale} from './JudgeLocale';
export function Materials({texts,open=false}:{texts:Record<Role,string>;open?:boolean}) {
  const {t}=useJudgeLocale();
  return <details className="panel materials" open={open}><summary>{t('Full source and translations','Оригинал и переводы целиком')}</summary>
    <div className="material-grid">{(['source','a','b'] as const).map(role=><section key={role}>
      <h3>{role==='source'?t('Source','Оригинал'):t('Text ','Перевод ')+role.toUpperCase()}</h3><pre dir="auto">{texts[role]}</pre>
      <p className="text-end">{t('End of text','Конец текста')}</p></section>)}</div></details>;
}
