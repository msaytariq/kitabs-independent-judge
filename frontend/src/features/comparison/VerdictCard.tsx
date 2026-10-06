"use client";
import type {JuryTable,JurySummary,SecondOpinion,Edition} from '../../shared/types/rubric';
import {apiUrl} from '../../shared/api/base';
import {useJudgeLocale} from './JudgeLocale';
type Props={jury:JuryTable;summary?:JurySummary|null;second?:SecondOpinion|null;edition?:Edition|null};
type Pair={a:number|null;b:number|null};
// The first thing the jury reads: the figures of the result below, without new calculations.
export function VerdictCard({jury,summary,second,edition}:Props){
  const {t,locale}=useJudgeLocale();
  const winners:Record<string,string>={a:t('Translation A is better','Лучше перевод A'),
    b:t('Translation B is better','Лучше перевод B'),tie:t('The translations are equal','Переводы равны')};
  const name=(w:string|null)=>w==='a'?'A':w==='b'?'B':w==='tie'?t('tie','ничья'):'—';
  const critical=jury.rows.find(row=>row.kind==='critical');
  const lines=summary&&(locale==='ru'?summary.ru:locale==='ar'?(summary.ar??summary.en):summary.en);
  // The winner side is green; a critical error count above zero is red.
  const pair=(value:Pair,mark:(side:'a'|'b')=>string|undefined)=><dd>{(['a','b'] as const).map(side=>
    <span key={side} className="verdict-side"><span className="side-name">{side.toUpperCase()}</span> <strong className={mark(side)}>{value[side]??'—'}</strong></span>)}</dd>;
  const winner=(w:string|null)=>(side:'a'|'b')=>w===side?'win':undefined;
  return <div className="verdict">
    <h2>{jury.winner?winners[jury.winner]:t('The assessment did not finish.','Оценка не завершена.')}</h2>
    <dl className="verdict-figures">
      <div><dt>{t('Total, 0–100','Итог, 0–100')}</dt>{pair(jury.totals,winner(jury.winner))}</div>
      {critical&&<div><dt>{t('Critical errors','Критические ошибки')}</dt>{pair(critical,side=>(critical[side]??0)>0?'bad':undefined)}</div>}
      {second&&<div><dt>{t('Second judge','Второй судья')}</dt>{pair(second.second.totals,winner(second.second.winner))}
        <dd className="verdict-note">{second.agree?t(`Same winner: ${name(second.first.winner)}`,`Победитель совпал: ${name(second.first.winner)}`)
          :t(`Different winners: ${name(second.first.winner)} and ${name(second.second.winner)}`,`Победители разные: ${name(second.first.winner)} и ${name(second.second.winner)}`)}</dd></div>}
    </dl>
    {lines&&<ul className="jury-summary">{lines.map(line=><li key={line}>{line}</li>)}</ul>}
    {edition?.download&&<p><a className="button primary" href={apiUrl(edition.download)} download>{t('Download the typeset book B (PDF)','Скачать свёрстанную книгу B (PDF)')}</a></p>}
  </div>;
}
