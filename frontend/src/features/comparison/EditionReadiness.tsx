"use client";
import type {Edition} from '../../shared/types/rubric';
import {apiUrl} from '../../shared/api/base';
import {useJudgeLocale} from './JudgeLocale';
// What a reader gets besides the translation. Shown apart: it is not part of the quality total.
export function EditionReadiness({edition}:{edition?:Edition|null}){
  const {t}=useJudgeLocale();
  if(!edition) return null;
  const labels:Record<string,string>={notes:t('Notes moved out of the author text','Сноски вынесены из текста автора'),
    glossary:t('Glossary entries','Термины глоссария'),persons:t('Person index entries','Персоналии'),
    typeset:t('Typeset book (PDF)','Свёрстанная книга (PDF)'),edits:t('Applied audit and editor edits','Применённые правки аудита и редактора')};
  const typeset=(value:string|null)=>value==='done'?t('ready','готова'):value==='error'?t('failed','не удалась')
    :value?t('typesetting…','идёт вёрстка…'):'—';
  const cell=(key:string,value:number|string|null)=>key==='typeset'?typeset(value as string|null):String(value??'—');
  return <section className="panel"><h2>{t('Readiness for publication','Готовность к изданию')}</h2>
    <p><strong>A: {t(`${edition.checks.a} of ${edition.total}`,`${edition.checks.a} из ${edition.total}`)} · B: {t(`${edition.checks.b} of ${edition.total}`,`${edition.checks.b} из ${edition.total}`)}</strong></p>
    <table><thead><tr><th>{t('Part of the edition','Часть издания')}</th><th>A</th><th>B</th></tr></thead><tbody>
      {edition.rows.map(row=><tr key={row.key}><th scope="row">{labels[row.key]||row.key}</th><td>{cell(row.key,row.a)}</td><td>{cell(row.key,row.b)}</td></tr>)}
    </tbody></table>
    {edition.download&&<p><a className="button primary" href={apiUrl(edition.download)} download>{t('Download the typeset book B (PDF)','Скачать свёрстанную книгу B (PDF)')}</a></p>}
    <p className="muted">{t('A separate block: it is not part of the translation quality total. The code counts the notes, glossary and person entries in each text; Kitabs.ai typesets book B after the autopilot.',
      'Отдельный блок: в итог качества перевода не входит. Сноски, термины и персоналии считает код в каждом тексте; книгу B верстает Kitabs.ai после автопилота.')}</p>
  </section>;
}
