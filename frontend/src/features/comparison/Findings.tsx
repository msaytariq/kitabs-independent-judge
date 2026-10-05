"use client";
import {useState} from 'react';
import type {Finding} from '../../shared/types/comparison';
import {useJudgeLocale} from './JudgeLocale';
export function Findings({findings}:{findings:Finding[]}) {
  const {t,locale}=useJudgeLocale();const [filter,setFilter]=useState('all');
  const labels:Record<string,string>={K:t('Critical','Критическое'),T:t('Terminology','Терминология'),A:t('Apparatus','Аппарат'),S:t('Style','Стиль'),'?':t('Disputed category','Спорная категория')};
  const visible=findings.filter(f=>filter==='all'||f.side===filter||(filter==='disputed'&&f.status==='disputed'));
  return <section className="findings"><h3>{t('Candidates for review','Кандидаты на проверку')}</h3>
    <div className="tabs filter-tabs">{[['all',t('All','Все')],['a','A'],['b','B'],['disputed',t('Disputed','Спорные')]].map(([id,label])=><button key={id} className={filter===id?'selected':''} aria-pressed={filter===id} onClick={()=>setFilter(id)}>{label}</button>)}</div>
    {!visible.length&&<p>{t('No findings in this group. This does not prove that the translation is error-free.','В этой группе нет находок. Это не доказывает безошибочность перевода.')}</p>}
    {visible.map(f=><article className="finding" key={f.id} id={'finding-'+f.id}>
      <div className="finding-heading"><h3>{f.side.toUpperCase()} · {labels[f.code]}</h3><span className="status">{f.status==='disputed'?t('Disputed','Спорное'):f.status==='unlocated'?t('Unlocated quotation','Цитата не подтверждена'):t('Needs review','Требует проверки')}</span></div>
      <p>{locale==='ru'&&f.why_ru?f.why_ru:f.why}</p>
      {locale==='ru'&&f.review_note_ru&&<p>{f.review_note_ru}</p>}
      <div className="quote-grid"><div><span className="quote-label">{t('Source','Оригинал')}</span><blockquote dir="auto">{f.source_excerpt}</blockquote></div>
        <div><span className="quote-label">{t('Translation','Перевод')} {f.side.toUpperCase()}</span><blockquote dir="auto">{f.current_text}</blockquote></div></div>
      <details><summary>{t('Suggested change and exact locations','Предложение и точные места')}</summary><blockquote dir="auto">{f.should_be}</blockquote>
        <p className="muted">{t('Zero-based Unicode character ranges; end excluded. A quote match locates evidence, it does not confirm the finding.','Диапазоны знаков Unicode с нуля, конец не включён. Совпадение цитаты подтверждает место, а не верность замечания.')}</p>
        {Object.entries(f.anchors).map(([role,a])=><p key={role}>{role}: {a.ranges.length?a.ranges.map(r=>`${r.start}–${r.end}`).join(', '):t('Not located','Не найдено')}</p>)}
      </details></article>)}
  </section>;
}
