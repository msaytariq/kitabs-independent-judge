"use client";
import type {CaseStudy as Study} from '../../shared/types/rubric';
import {useJudgeLocale} from './JudgeLocale';
export function CaseStudy({study}:{study?:Study|null}) {
  const {t,locale}=useJudgeLocale();
  if(!study) return null;
  const labels:Record<string,string>={accuracy:t('accuracy','точность'),completeness:t('completeness','полнота'),
    terminology:t('terminology','терминология'),readability:t('readability','читаемость'),
    seamlessness:t('assembly integrity','целостность сборки'),apparatus:t('scholarly apparatus','научный аппарат')};
  return <section className="panel case-study"><h2>{t('What the judge caught','Что поймал судья')}</h2>
    {(['a','b'] as const).map(side=><div key={side}>
      {study[side].length===0&&<p>{t(`${side.toUpperCase()} has no errors with quotations.`,`В ${side.toUpperCase()} ошибок с цитатами нет.`)}</p>}
      {study[side].map(d=><article key={side+d.id}>
        <h3>{t(`Translation ${side.toUpperCase()}`,`Перевод ${side.toUpperCase()}`)} · {labels[d.criterion]||d.criterion}</h3>
        <p className="muted">{t('Source','Оригинал')}</p><blockquote dir="auto">{d.source_quote}</blockquote>
        <p className="muted">{t('Translation','Перевод')}</p><blockquote dir="auto">{d.translation_quote}</blockquote>
        <p>{locale==='ru'?d.explanation_ru:d.explanation_en}</p></article>)}
    </div>)}
    {study.kitabs_corrections.length>0&&<div><h3>{t('What the Kitabs audit corrected on the way to B','Что исправил аудит Kitabs на пути к B')}</h3>
      {study.kitabs_corrections.map((c,i)=><p key={i}><del>{c.before}</del><br/><ins>{c.after}</ins></p>)}</div>}
  </section>;
}
