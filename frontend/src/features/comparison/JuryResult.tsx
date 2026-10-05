"use client";
import type {ComparisonView} from '../../shared/types/comparison';
import {useJudgeLocale} from './JudgeLocale';
import {RubricTable} from './RubricTable';
import {EffortReduction} from './EffortReduction';
import {CaseStudy} from './CaseStudy';
import {SecondJudge} from './SecondJudge';
import {ProcessingTime} from './ProcessingTime';
import {ReferenceEvidence} from './ReferenceEvidence';
import {Findings} from './Findings';
export function JuryResult({view}:{view:ComparisonView}) {
  const {t,locale}=useJudgeLocale();
  return <div className="comparison-result">
    {view.demonstration&&<p className="notice">{t('Synthetic test example; no live model.','Учебный пример; без живой модели.')}</p>}
    {view.rubric&&view.jury?<RubricTable result={view.rubric} jury={view.jury} summary={view.jury_summary}/>:<section className="panel"><h2>{view.rubric_protocol?t('The assessment did not finish.','Оценка не завершена.'):view.run?t('Saved result of an earlier method','Сохранённый результат прежней методики'):t('Start the comparison to get grades.','Запустите сравнение, чтобы получить оценки.')}</h2></section>}
    <CaseStudy study={view.case_study}/>
    <SecondJudge opinion={view.second_judge}/>
    <EffortReduction effort={view.effort_reduction}/>
    <ProcessingTime effort={view.processing_effort}/>
    {!view.rubric&&!view.rubric_protocol&&<details className="panel"><summary>{t('Evidence and explanations','Доказательства и пояснения')}</summary>
      <Findings findings={view.summary.findings}/></details>}
    <ReferenceEvidence result={view.hadith}/>
    <details className="panel"><summary>{t('Method and provenance','Методика и происхождение')}</summary>
      <p>{view.rubric?t('The AI judge reads the source and two anonymous translations once and grades six criteria.','ИИ-судья один раз читает оригинал и два анонимных перевода и оценивает шесть критериев.'):t('Saved detailed protocol of an earlier method.','Сохранённый протокол прежней методики.')}</p>
      <p>{t('Unknown vendor chunk boundaries are not inferred. API reference matching is shown separately from machine grades.','Неизвестные границы чанков вендора не угадываются. Сверка с API библиотеки показана отдельно от машинных оценок.')}</p>
      <p>{t('Source characters','Знаков оригинала')}: {view.summary.source_chars}; {t('1,800-character units','условных страниц по 1800 знаков')}: {view.summary.source_pages}.</p>
      <p>{t('Judge','Судья')}: {view.run?.model||t('Unknown','Неизвестно')}. {t('Protocol','Протокол')}: {view.run?.protocol||view.rubric?.version||'—'}.</p>
      <p>{t('Run','Прогон')}: {view.run?.id||'—'} · Git: {view.run?.code_sha||'—'}</p>
      {view.run?.cost&&<p>{t('Reported cost, USD','Учтённая стоимость, USD')}: {view.run.cost.reported_usd}; {t('unresolved reserve','незакрытый резерв')}: {view.run.cost.unresolved_reserved_usd}</p>}
      {Object.entries(view.scope.hashes).map(([role,hash])=><p key={role}>{role}: <code>{hash}</code></p>)}
    </details>
  </div>;
}
