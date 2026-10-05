"use client";
import type {ComparisonView} from '../../shared/types/comparison';
import {useJudgeLocale} from './JudgeLocale';
import {QualityTable} from './QualityTable';
import {DecisionSummary} from './DecisionSummary';
import {Findings} from './Findings';
export function JuryResult({view}:{view:ComparisonView}) {
  const {t}=useJudgeLocale();
  return <div className="comparison-result">
    {view.demonstration&&<p className="notice">{t('Synthetic demonstration · fixed test responses, no live model. These scores do not evaluate a real book or vendor.','Учебный пример · фиксированные тестовые ответы, без живой модели. Эти баллы не оценивают реальную книгу или производителя.')}</p>}
    <QualityTable ratings={view.ratings} effort={view.decision_effort}/>
    <DecisionSummary effort={view.decision_effort}/>
    <details className="panel"><summary>{t('Evidence and explanations','Доказательства и пояснения')}</summary>
      <p>{t('Scores use the undisputed, located candidates below. Each item shows the exact source and translation excerpts.','Оценки используют неспорные, привязанные к тексту кандидаты ниже. Для каждого показаны точные цитаты оригинала и перевода.')}</p>
      <Findings findings={view.summary.findings}/></details>
    <details className="panel"><summary>{t('Apparatus and source matching','Аппарат и сверка источников')}</summary>
      <p>{t('The apparatus index counts structure. It does not verify relevance, attribution, translation accuracy or hadith authenticity.','Индекс аппарата учитывает структуру. Он не подтверждает уместность, атрибуцию, точность перевода или достоверность хадисов.')}</p>
      {(['a','b'] as const).map(side=><p key={side}>{side.toUpperCase()}: {t('notes','примечаний')} {view.ratings.sides[side].inventory.notes??0}; {t('glossary entries','терминов')} {view.ratings.sides[side].inventory.glossary??0}; {t('persons','персоналий')} {view.ratings.sides[side].inventory.persons??0}.</p>)}
      <p>{!view.hadith?t('Source matching has not been performed.','Сверка источников не выполнена.'):t('Source check status: ','Статус сверки: ')+view.hadith.status}</p>
      {view.hadith?.limit_reached&&<p>{t('The search limit was reached; remaining quotations were not assessed.','Достигнут лимит поиска; остальные цитаты не оценены.')}</p>}
      {view.hadith?.items.map((item,i)=><article key={i}><blockquote dir="auto">{item.quote}</blockquote><p>{item.status}</p>
        {item.candidates.map(c=><section key={c.id}><a href={c.url} target="_blank" rel="noreferrer">{c.collection} · {c.number}</a>
          <blockquote dir="auto">{c.text}</blockquote><p className="muted">{c.edition} · {c.retrieved_at} · SHA-256: {c.snapshot_sha256}</p></section>)}</article>)}
    </details>
    <details className="panel"><summary>{t('Method and provenance','Методика и происхождение')}</summary>
      <p>{t('Three blind passes per translation, critical review and cross-checks. Producer names are withheld from judging input. Model-family independence is not established.','Три слепых прохода по каждому переводу, пересмотр критических замечаний и перекрёстная проверка. Названия производителей скрыты от судьи. Независимость семейства модели не установлена.')}</p>
      <p>{t('Accuracy = max(0, 10 − (3K + T + 0.5S) / source units) × 10. Terminology and readability are diagnostic indices already included in accuracy.','Точность = max(0, 10 − (3K + T + 0,5S) / страницы оригинала) × 10. Терминология и читаемость — диагностические индексы, уже учтённые в точности.')}</p>
      <p>{t('Apparatus: notes up to 50, glossary 30, persons/narrators 20. A score of 100 means no included penalties, not proven perfection.','Аппарат: примечания до 50, глоссарий 30, персоналии/передатчики 20. Оценка 100 означает отсутствие учтённых штрафов, а не доказанное совершенство.')}</p>
      <p>{t('Source characters','Знаков оригинала')}: {view.summary.source_chars}; {t('1,800-character units','условных страниц по 1800 знаков')}: {view.summary.source_pages}.</p>
      <p>{t('Rubric','Методика')}: {view.ratings.version}. {t('Judge','Судья')}: {view.run?.model||t('Unknown','Неизвестно')}.</p>
      <p>{t('Run','Прогон')}: {view.run?.id||'—'} · Git: {view.run?.code_sha||'—'}</p>
      {Object.entries(view.scope.hashes).map(([role,hash])=><p key={role}>{role}: <code>{hash}</code></p>)}
    </details>
  </div>;
}
