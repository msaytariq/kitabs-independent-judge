"use client";
import type {RubricResult,RubricSide,ReferenceCoverage} from '../../shared/types/rubric';
import {useJudgeLocale} from './JudgeLocale';
export function RubricTable({result,coverage}:{result:RubricResult;coverage?:ReferenceCoverage|null}) {
  const {t,locale}=useJudgeLocale();
  const labels:Record<string,string>={accuracy:t('Accuracy','Точность'),completeness:t('Completeness','Полнота'),
    terminology:t('Terminology','Терминология'),readability:t('Readability','Читаемость'),
    seamlessness:t('Assembly integrity','Целостность сборки'),apparatus:t('Scholarly apparatus','Научный аппарат')};
  const winners:Record<string,string>={a:t('Translation A is better','Лучше перевод A'),
    b:t('Translation B is better','Лучше перевод B'),tie:t('The translations are equal','Переводы равны')};
  const total=(value:number|null)=>value===null?'—':`${value.toFixed(1).replace('.',locale==='ru'?',':'.')} / 5`;
  const cell=(s:RubricSide,side:'a'|'b')=><td key={side}><strong>{s.score===null?'—':`${s.score} / 5`}</strong>
    <details><summary>{t('Why','Почему')}</summary>
      <p>{locale==='ru'?s.explanation_ru:s.explanation_en}</p>
      {s.evidence.map((e,i)=><article key={e.id+i}><p>{t('Source','Оригинал')}</p><blockquote dir="auto">{e.source_quote}</blockquote>
        <p>{t('Translation','Перевод')} {side.toUpperCase()}</p><blockquote dir="auto">{e.translation_quote}</blockquote>
        <p>{locale==='ru'?e.explanation_ru:e.explanation_en}</p></article>)}
    </details></td>;
  return <section className="panel"><h2>{result.winner?winners[result.winner]:t('The assessment did not finish.','Оценка не завершена.')}</h2>
    <table><thead><tr><th>{t('Criterion','Критерий')}</th><th>A</th><th>B</th></tr></thead><tbody>
      {result.criteria.map(row=><tr key={row.criterion}><th scope="row">{labels[row.criterion]}</th>{cell(row.a,'a')}{cell(row.b,'b')}</tr>)}
      {coverage&&(['quran','hadith'] as const).filter(g=>coverage[g].total>0).map(g=><tr key={g}><th scope="row">{g==='quran'?t('Quran verses in the translation','Аяты Корана в переводе'):t('Hadith in the translation','Хадисы в переводе')}</th>
        {(['a','b'] as const).map(side=><td key={side}><strong>{t(`${coverage[g][side]} of ${coverage[g].total}`,`${coverage[g][side]} из ${coverage[g].total}`)}</strong></td>)}</tr>)}
      <tr><th scope="row">{t('Total','Итог')}</th><td><strong>{total(result.totals.a)}</strong></td><td><strong>{total(result.totals.b)}</strong></td></tr>
    </tbody></table>
    <p className="muted">{t('Errors with quotations','Ошибки с цитатами')}: A — {result.unique_defects.a}; B — {result.unique_defects.b}.</p>
    <p className="muted">{t('An AI judge gives grades 1–5 with the same criteria for A and B. The total is the mean of the criterion grades.','Оценки 1–5 выставляет ИИ-судья по одинаковым критериям для A и B. Итог — среднее оценок по критериям.')}</p>
  </section>;
}
