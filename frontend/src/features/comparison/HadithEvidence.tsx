"use client";
import type {HadithResult,HadithCandidate} from '../../shared/types/options';
import {useJudgeLocale} from './JudgeLocale';
export function HadithEvidence({result}:{result:HadithResult|null}) {
  const {t}=useJudgeLocale();
  const states:Record<string,string>={exact:t('Exact text match','Точное совпадение текста'),normalized:t('Match after diacritic normalization','Совпадение после нормализации огласовок'),
    review:t('Differences found','Есть расхождения'),fragment:t('Partial quotation','Частичная цитата'),ambiguous:t('Ambiguous match','Неоднозначное совпадение'),
    not_found:t('No match found','Совпадение не найдено'),requires_key:t('Not checked: API access is not configured','Не сверено: доступ к API не настроен'),
    unavailable:t('Not checked: library unavailable','Не сверено: библиотека недоступна'),no_candidates:t('No marked candidates found','Помеченные кандидаты не найдены'),
    checked:t('Lookup completed','Поиск выполнен'),partial:t('Lookup is incomplete','Поиск выполнен частично')};
  function evidence(record:HadithCandidate){return <section><a href={record.url} target="_blank" rel="noreferrer">{record.collection||t('Source','Источник')} {record.number||''}</a>
    <blockquote dir="auto">{record.text}</blockquote>{record.english_text&&<blockquote>{record.english_text}</blockquote>}
    <p>{t('Attributed library grade','Оценка с атрибуцией из библиотеки')}: {record.grade||t('Not supplied','Не указана')}</p>
    <small>{record.retrieved_at} · SHA-256: {record.snapshot_sha256}</small></section>;}
  return <details className="panel"><summary>{t('Hadith library API evidence','Сверка хадисов через API библиотеки')}</summary>
    <p>{t('Candidate search: marked Arabic quotations in Bukhari and Muslim. This does not cover every hadith or verify the translation.','Поиск кандидатов: помеченные арабские цитаты в Бухари и Муслиме. Это не охватывает все хадисы и не подтверждает правильность перевода.')}</p>
    {!result?<p>{t('Not checked','Не сверено')}</p>:<>
      <p>{t('Candidate index','Кандидатный индекс')}: {states[result.status]||t('Not checked','Не сверено')}</p>
      {result.items.map((item,i)=><article key={i}><blockquote dir="auto">{item.quote}</blockquote><p>{states[item.status]||item.status}</p>
        {item.candidates.map(c=><div key={c.id}>{evidence(c)}</div>)}</article>)}
      <h3>Sunnah.com API</h3><p>{states[result.official?.status||'requires_key']||t('Not checked','Не сверено')}</p>
      {result.official?.records.map((item,i)=><article key={i}><blockquote dir="auto">{item.quote}</blockquote>
        <p>{states[item.status]||item.status}</p>{item.record&&evidence(item.record)}</article>)}
      {(result.limit_reached||result.official?.limit_reached)&&<p>{t('Lookup limit reached. Remaining quotations are not checked.','Достигнут предел запросов. Остальные цитаты не сверены.')}</p>}
    </>}
    <p>{t('Generated notes are not library verification. A text match does not establish authenticity; the named scholar owns the quoted grade.','Созданные примечания не являются сверкой с библиотекой. Совпадение текста не устанавливает достоверность; приведённая оценка принадлежит указанному учёному.')}</p>
  </details>;
}
