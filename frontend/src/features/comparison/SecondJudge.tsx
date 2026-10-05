"use client";
import type {SecondOpinion} from '../../shared/types/rubric';
import {useJudgeLocale} from './JudgeLocale';
export function SecondJudge({opinion}:{opinion?:SecondOpinion|null}) {
  const {t}=useJudgeLocale();
  if(!opinion) return null;
  const labels:Record<string,string>={accuracy:t('Accuracy','Точность'),completeness:t('Completeness','Полнота'),
    terminology:t('Terminology','Терминология'),readability:t('Readability','Читаемость'),
    seamlessness:t('Assembly integrity','Целостность сборки'),apparatus:t('Scholarly apparatus','Научный аппарат')};
  const name=(w:string|null)=>w==='a'?'A':w==='b'?'B':w==='tie'?t('tie','ничья'):'—';
  const {first,second}=opinion;
  const value=(v:number|null)=>v===null?'—':v;
  return <section className="panel"><h2>{t('Second judge: bias check','Второй судья: проверка беспристрастности')}</h2>
    <table><thead><tr><th>{t('Criterion','Критерий')}</th><th colSpan={2}>{first.model}</th><th colSpan={2}>{second.model}</th></tr>
      <tr><th></th><th>A</th><th>B</th><th>A</th><th>B</th></tr></thead><tbody>
      {opinion.rows.map(r=><tr key={r.key}><th scope="row">{labels[r.key]||r.key}</th>
        <td>{value(r.first.a)}</td><td>{value(r.first.b)}</td><td>{value(r.second.a)}</td><td>{value(r.second.b)}</td></tr>)}
      <tr><th scope="row">{t('Total of criteria','Итог по критериям')}</th>
        {[first,second].flatMap((j,i)=>(['a','b'] as const).map(s=><td key={i+s}><strong>{value(j.totals[s])}</strong></td>))}</tr>
    </tbody></table>
    <p><strong>{opinion.agree?t(`Same winner: ${name(first.winner)}`,`Победитель совпал: ${name(first.winner)}`)
      :t(`Different winners: ${name(first.winner)} and ${name(second.winner)}`,`Победители разные: ${name(first.winner)} и ${name(second.winner)}`)}</strong></p>
    <p className="muted">{t('Both judges receive the texts without vendor or model names. The family of the second judge made neither translation nor the first assessment. The verse and hadith rows come from verified quotations and are not repeated.',
      'Оба судьи получили тексты без имён вендоров и моделей. Семья второго судьи не участвовала в переводах и в первой оценке. Строки аятов и хадисов основаны на проверенных цитатах и не повторяются.')}</p>
  </section>;
}
