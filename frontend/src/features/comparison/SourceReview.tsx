import type {Proof,SourceReviewData} from '../../shared/types/sourceReview';
import './sourceReview.css';

function Evidence({item,review}:{item:Proof;review:SourceReviewData}) {
  return <details className="review-evidence"><summary>Цитаты и источники</summary>
    {item.evidence_ids.map(id=>{
      const quote=review.evidence.find(q=>q.id===id)!;
      return <div key={id}><p className="muted">{quote.label_ru}</p><blockquote dir="auto">{quote.text}</blockquote></div>;
    })}
    {!!item.source_ids?.length&&<ul>{item.source_ids.map(id=>{
      const source=review.sources.find(s=>s.id===id)!;
      return <li key={id}><a href={source.url} target="_blank" rel="noreferrer">{source.label}</a></li>;
    })}</ul>}
  </details>;
}

export function SourceReview({review,reportHref}:{review:SourceReviewData;reportHref:string}) {
  return <section className="panel source-review">
    <div className="result-heading"><h2>Разбор по источникам</h2>
      <a className="button" href={reportHref} target="_blank" rel="noreferrer">Открыть разбор целиком</a></div>
    <p className="muted">Подготовил Codex · {review.checked_on} · без нового прогона судьи</p>
    <p className="review-lead">{review.summary_ru}</p>
    <h3>Что уже сделала платформа</h3>
    <div className="review-benefits">{review.benefits.map(item=><article key={item.title_ru}>
      <h4>{item.title_ru}</h4><p>{item.detail_ru}</p><Evidence item={item} review={review}/>
    </article>)}</div>
    <h3>Сопоставление A и B</h3>
    {review.checks.map(item=><article className="review-check" key={item.id}>
      <h4>{item.title_ru}</h4><div className="versions"><div><b>A — опубликованный перевод</b><p>{item.a_ru}</p></div>
        <div><b>B — Kitabs</b><p>{item.b_ru}</p></div></div>
      <p>{item.conclusion_ru}</p><Evidence item={item} review={review}/>
    </article>)}
    <h3>Работа редактора</h3><p className="muted">Конкретные задачи для проверки и дополнения; это не окончательный счёт ошибок.</p>
    {review.tasks.map(item=><article className="review-check" key={item.id}>
      <h4>{item.side==='both'?'Обе стороны':`Перевод ${item.side.toUpperCase()}`}: {item.title_ru}</h4><p>{item.reason_ru}</p>
      {item.draft_ru&&<details><summary>Проект дополнения — не применён</summary><p>{item.draft_ru}</p></details>}
      <Evidence item={item} review={review}/>
    </article>)}
    <details className="review-limits"><summary>Проверенные источники и границы разбора</summary>
      <ul>{review.sources.map(s=><li key={s.id}><a href={s.url} target="_blank" rel="noreferrer">{s.label}</a><p>{s.summary_ru}</p></li>)}</ul>
      <ul>{review.limitations_ru.map(text=><li key={text}>{text}</li>)}</ul>
    </details>
  </section>;
}
