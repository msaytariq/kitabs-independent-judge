import type {ComparisonView} from '../../shared/types/comparison';
import {countLabel} from './helpers.mjs';
export function Apparatus({view}:{view:ComparisonView}) {
  return <section className="panel">
    <h2>Проверка научного аппарата фрагмента</h2>
    <p>Сноски, пояснения и ссылки проверяются отдельно от точности перевода.</p>
    <div className="versions">{(['a','b'] as const).map(side=><div key={side}>
      <h3>Перевод {side.toUpperCase()}</h3>
      <p>Замечания модели: <b>{countLabel(view.summary.sides[side].apparatus_candidates)}</b></p>
      <p className="muted">Корректность аппарата и необходимые дополнения: пока не установлены.</p>
      {view.apparatus?.[side]?.length?<details><summary>Сохранённые примечания: {view.apparatus[side].length}</summary>
        {view.apparatus[side].map(note=><blockquote key={note.number} dir="auto">[{note.number}] {note.text}</blockquote>)}
      </details>:<p className="muted">Отдельные примечания к этому фрагменту не приложены.</p>}
    </div>)}</div>
    <p className="muted">Наличие сноски не доказывает её правильность. Отсутствие сноски само по себе не является ошибкой перевода.</p>
    {!!view.references?.length&&<details><summary>Справочные источники для дополнительной проверки</summary>
      <ul>{view.references.map(r=><li key={r.url}><a href={r.url} target="_blank" rel="noreferrer">{r.label}</a></li>)}</ul>
      <p>Различия признанных переводов Корана сами по себе не ошибка. Параллель хадиса не является полным тахричем или окончательной оценкой достоверности. Справочные источники ещё не подключены к оценке автоматически.</p>
    </details>}
  </section>;
}
