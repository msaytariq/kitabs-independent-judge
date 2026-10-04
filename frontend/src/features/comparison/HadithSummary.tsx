import type {HadithResult} from '../../shared/types/options';
const labels:Record<string,string>={exact:'Полное совпадение',normalized:'Совпадение без огласовок',
  fragment:'Совпадает фрагмент',ambiguous:'Несколько соответствий',review:'Есть расхождения — нужна проверка',
  not_found:'Текстовое соответствие не найдено',unavailable:'Источник недоступен'};
export function HadithSummary({result}:{result:HadithResult|null}) {
  return <section className="panel hadith-summary"><h3>Хадисы и источники</h3>
    <p>{!result?'Библиотечная сверка ещё не выполнена.':result.status==='unavailable'?'Библиотека недоступна — вывод не сделан.':
      result.status==='not_requested'?'Профиль не включает библиотечную сверку.':
      result.status==='no_candidates'?'Нет выделенных арабских цитат для сверки.':`Проверено цитат: ${result.checked_count??result.items.length}`}</p>
    {result?.status==='checked'&&<p className="muted">Полных однозначных совпадений: {result.verified_count}. Фрагменты и спорные соответствия — в деталях.</p>}
    {result?.official?.status==='requires_key'&&<p className="muted">Sunnah.com: для официальной сверки нужен API-доступ. Ниже — отдельная электронная коллекция.</p>}
    {result?.official?.status==='unavailable'&&<p className="notice">Sunnah.com недоступен — официальная сверка не выполнена.</p>}
    <details><summary>Источники и результаты сверки</summary>
      <p>{result?.library||'Поиск по арабскому оригиналу'}</p>
      {result?.official?.limit_reached&&<p className="notice">Sunnah.com: запрошены первые 10 уникальных записей; остальные не проверены.</p>}
      {result?.official?.records.map((item,index)=><article key={`official-${index}`}>
        <h4>Sunnah.com · {labels[item.status]||item.status}</h4>
        {item.record&&<><a href={item.record.url} target="_blank" rel="noreferrer">Открыть запись Sunnah.com</a>
          <blockquote dir="auto">{item.record.text}</blockquote><blockquote lang="en">{item.record.english_text}</blockquote>
          <p>{item.record.grade||'Оценка достоверности в ответе API не указана.'}</p></>}
      </article>)}
      <p>Сверяется текст, а не выносится заключение о достоверности хадиса или точности английского перевода.
        Поиск охватывает арабские цитаты в кавычках или круглых скобках и подключённые сборники.</p>
      {result?.limit_reached&&<p className="notice">Проверены первые 30 цитат; остальные не оценены.</p>}
      {result?.items.map((item,index)=><article className="finding" key={index}>
        <h4>{labels[item.status]||item.status}</h4><blockquote dir="auto">{item.quote}</blockquote>
        {item.candidates.map(c=><div key={c.id}>
          <a href={c.url} target="_blank" rel="noreferrer">{c.collection} · {c.number}</a>
          <blockquote dir="auto">{c.text}</blockquote>
          {c.english_text&&<blockquote lang="en">{c.english_text}</blockquote>}
          {c.grade&&<p>Оценка источника: {c.grade}</p>}
          <p className="muted">Издание: {c.edition}. Получено: {c.retrieved_at}.</p>
        </div>)}
      </article>)}
    </details>
  </section>;
}
