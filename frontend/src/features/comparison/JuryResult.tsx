"use client";
import type {ComparisonView} from '../../shared/types/comparison';
import {useJudgeLocale} from './JudgeLocale';
import {PairedTable} from './PairedTable';
import {ProcessingTime} from './ProcessingTime';
import {HadithEvidence} from './HadithEvidence';
import {Findings} from './Findings';
export function JuryResult({view}:{view:ComparisonView}) {
  const {t,locale}=useJudgeLocale();
  return <div className="comparison-result">
    {view.demonstration&&<p className="notice">{t('Synthetic test example; no live model.','Учебный пример; без живой модели.')}</p>}
    {view.paired?<PairedTable result={view.paired}/>:<section className="panel"><h2>{t('Not assessed with the paired rubric','По парной методике не оценено')}</h2>
      <p>{view.paired_protocol?t('The paired run did not finish; no grades were assigned.','Запуск по парной методике не завершён; оценки не выставлены.'):view.run?t('This saved run uses a different protocol. Its evidence is available below.','Этот сохранённый запуск использует другую методику. Его доказательства доступны ниже.'):t('Start the comparison to obtain machine assessments.','Запустите сравнение для получения машинных оценок.')}</p></section>}
    <ProcessingTime effort={view.processing_effort}/>
    {!view.paired&&!view.paired_protocol&&<details className="panel"><summary>{t('Evidence and explanations','Доказательства и пояснения')}</summary>
      <Findings findings={view.summary.findings}/></details>}
    {view.adjudication&&view.adjudication.status!=='not_needed'&&<details className="panel"><summary>{t('Analysis of disagreements','Разбор противоречий')}</summary>
      <p>{view.adjudication.status==='completed'?t('Additional machine analysis. Original instability remains visible.','Дополнительный машинный разбор. Исходная неустойчивость сохранена.'):t('Additional analysis is incomplete.','Дополнительный разбор не завершён.')}</p>
      {view.adjudication.result?.criteria.map(row=><article key={row.criterion}>{(['a','b'] as const).map(s=><p key={s}>{s.toUpperCase()}: {locale==='ru'?row[s].explanation_ru:row[s].explanation_en}</p>)}</article>)}
    </details>}
    <HadithEvidence result={view.hadith}/>
    <details className="panel"><summary>{t('Method and provenance','Методика и происхождение')}</summary>
      <p>{view.paired?t('Source and two anonymous translations, then the same comparison in reverse order. Disagreements receive targeted analysis when budget permits. Two passes of one model are not an independent panel.','Оригинал и два анонимных перевода, затем сравнение в обратном порядке. При доступном бюджете противоречия разбираются адресно. Два прохода одной модели не являются независимой панелью.'):t('Saved detailed protocol: separate blind passes, critical review and cross-checks. Historical scores are not converted into the new rubric.','Сохранённый подробный протокол: отдельные слепые проходы, пересмотр критических замечаний и перекрёстная проверка. Исторические баллы не пересчитываются в новую шкалу.')}</p>
      <p>{t('Unknown vendor chunk boundaries are not inferred. API reference matching is shown separately from machine grades.','Неизвестные границы чанков вендора не угадываются. Сверка с API библиотеки показана отдельно от машинных оценок.')}</p>
      <p>{t('Source characters','Знаков оригинала')}: {view.summary.source_chars}; {t('1,800-character units','условных страниц по 1800 знаков')}: {view.summary.source_pages}.</p>
      <p>{t('Judge','Судья')}: {view.run?.model||t('Unknown','Неизвестно')}. {t('Protocol','Протокол')}: {view.run?.protocol||view.paired?.version||'—'}.</p>
      <p>{t('Run','Прогон')}: {view.run?.id||'—'} · Git: {view.run?.code_sha||'—'}</p>
      {view.run?.cost&&<p>{t('Reported cost, USD','Учтённая стоимость, USD')}: {view.run.cost.reported_usd}; {t('unresolved reserve','незакрытый резерв')}: {view.run.cost.unresolved_reserved_usd}</p>}
      {Object.entries(view.scope.hashes).map(([role,hash])=><p key={role}>{role}: <code>{hash}</code></p>)}
    </details>
  </div>;
}
