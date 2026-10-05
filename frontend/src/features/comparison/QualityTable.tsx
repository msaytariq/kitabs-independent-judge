"use client";
import type {Ratings,DecisionEffort} from '../../shared/types/comparison';
import {useJudgeLocale} from './JudgeLocale';
import {conclusionKey} from './qualityView.mjs';
export function QualityTable({ratings,effort}:{ratings:Ratings;effort?:DecisionEffort}) {
  const {t}=useJudgeLocale();
  const labels={total:t('Overall index','Общий индекс'),accuracy:t('Accuracy','Точность'),
    terminology:t('Terminology','Терминология'),readability:t('Readability','Читаемость'),apparatus:t('Structural apparatus','Структурный аппарат')};
  const conclusions={unknown:t('Not enough evidence for a score comparison.','Для сравнения баллов недостаточно данных.'),
    a:t('Text A has the higher index.','У перевода A выше индекс.'),b:t('Text B has the higher index.','У перевода B выше индекс.'),
    tie:t('The displayed indices are equal.','Показанные индексы равны.')};
  return <section className="panel quality-table"><h2>{t('Comparison','Сравнение')}</h2>
    <div className="table-scroll"><table><caption>{t('Provisional machine indices · 0–100','Предварительные индексы ИИ · 0–100')}</caption>
      <thead><tr><th scope="col">{t('Criterion','Критерий')}</th><th scope="col">{t('Text A','Перевод A')}</th><th scope="col">{t('Text B','Перевод B')}</th></tr></thead>
      <tbody>{(Object.keys(labels) as (keyof typeof labels)[]).map(key=><tr key={key} className={key==='total'?'total-row':''}>
        <th scope="row">{labels[key]}</th>{(['a','b'] as const).map(side=><td key={side}>{ratings.sides[side][key]??t('Not assessed','Не оценено')}</td>)}</tr>)}
      {effort&&<><tr><th scope="row">{t('Remaining correction candidates','Оставшиеся кандидаты на исправление')}</th>{(['a','b'] as const).map(side=><td key={side}>{effort.sides[side].remaining_candidates??t('Not assessed','Не оценено')}</td>)}</tr>
      <tr><th scope="row">{t('Decision estimate, seconds','Оценка решений, секунды')}</th>{(['a','b'] as const).map(side=><td key={side}>{effort.sides[side].remaining_estimated_seconds??t('Not assessed','Не оценено')}</td>)}</tr></>}
      </tbody></table></div>
    <p className="conclusion">{conclusions[conclusionKey(ratings) as keyof typeof conclusions]}</p>
    <p className="muted">{t('70% accuracy + 30% structural apparatus. Scientific correctness is not assessed.','70% точности + 30% структурного аппарата. Научная корректность не оценена.')}</p>
    {(['a','b'] as const).some(s=>ratings.sides[s].excluded>0)&&<p className="notice">{t('Disputed or unlocated findings are excluded:','Спорные и непривязанные находки исключены:')} A {ratings.sides.a.excluded} · B {ratings.sides.b.excluded}</p>}
  </section>;
}
