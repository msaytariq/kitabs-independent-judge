import type {ComparisonView,Reference} from '../../shared/types/comparison';
import {reportUrl} from '../../shared/api/comparison';
import {countLabel} from './helpers.mjs';
import {Findings} from './Findings';
import {Apparatus} from './Apparatus';

export function ComparisonResult({view,reference}:{view:ComparisonView;reference:Reference}) {
  const result = view.summary;
  return <div className="comparison-result">
    <div className="result-heading"><h2>{result.measured?'Результат сравнения':'Материалы готовы'}</h2>
      <a className="button" href={reportUrl(reference)} target="_blank" rel="noreferrer">Открыть отчёт</a></div>
    {!result.measured?<section className="panel"><h3>Количество правок пока неизвестно</h3>
      <p>Для этих материалов нет завершённой ИИ-оценки. Они сохранены локально; новый платный запуск сейчас выключен.</p>
      <p className="muted">Готовый пример «Вступление: сохранённый пилот» показывает полный сценарий по уже полученному результату.</p>
    </section>:<>
      <p className="saved-caption">Сохранённый пилот · новый ИИ-запуск не выполнялся</p>
      <div className="versions">{(['a','b'] as const).map(side=>{
        const s = result.sides[side];
        return <section className="panel score-card" key={side}>
          <span className="eyebrow">Перевод {side.toUpperCase()}</span>
          <div className="score-number">{countLabel(s.candidates)}</div><p className="score-label">находки модели</p>
          <p>Ожидают проверки: {(s.candidates||0)-s.disputed} · Спорные: {s.disputed}</p>
          <p className="necessary">Необходимых правок: <b>не установлено</b></p>
        </section>;
      })}</div>
      <section className="panel"><h3>Типы замечаний</h3><div className="table-scroll"><table>
        <thead><tr><th>Кандидаты на исправление текста</th><th>A</th><th>B</th></tr></thead>
        <tbody>{[['K','Критические'],['T','Терминология'],['S','Стиль']].map(([code,label])=><tr key={code}>
          <th scope="row">{label}</th>{(['a','b'] as const).map(s=><td key={s}>{countLabel(result.sides[s].by_code?.[code])}</td>)}
        </tr>)}</tbody></table></div>
        <p className="muted">Включая спорные замечания. Повторные ответы модели не суммируются. Научный аппарат показан отдельно.</p>
        <p className="notice">Экспертная проверка не завершена. Эти числа не доказывают превосходство одного перевода и не измеряют экономию времени.</p>
        {(['a','b'] as const).some(s=>result.sides[s].unlocated>0||result.sides[s].classification_conflicts>0)&&<p className="notice">Есть замечания без однозначной цитаты или категории. Они отмечены в списке и не включены в соответствующие категории.</p>}
      </section>
      <Findings key={view.id} findings={result.findings}/>
    </>}
    <Apparatus view={view}/>
    <details className="panel"><summary>Методика и границы результата</summary>
      <p>Один оригинал, два перевода. Три отдельных прохода по каждой стороне → согласование находок → повторная проверка критических замечаний → перекрёстная проверка → проверка полноты.</p>
      <p>Оригинал: {result.source_chars} знаков, {result.source_pages} условной страницы. Одна страница — 1800 знаков оригинала; знаменатель одинаков для A и B.</p>
      {!result.negotiation_grade&&<p>Выборка меньше трёх страниц. Результат нельзя обобщать на всю книгу или платформу.</p>}
      <p>Уникальность определяется совпадающей парой точных цитат. Разные формулировки об одном месте могут потребовать объединения экспертом.</p>
      <p>Условные 40 и 10 правок означают в четыре раза меньше правок. Это не измеренная экономия времени: сложность исправлений различается.</p>
      {view.run&&<><p>Судья: {view.run.model}. Прогон: <code>{view.run.id}</code>.</p>
        <p>{view.provenance?.independence_note || 'Независимость судьи от переводчиков требует отдельной проверки.'}</p>
        <p>Хэш сохранённого отчёта: <code>{view.run.report_sha256}</code></p></>}
      <p>Идентификатор материалов: <code>{view.id}</code></p>
      {(['source','a','b'] as const).map(r=><p key={r}>{r==='source'?'Оригинал':`Перевод ${r.toUpperCase()}`}: <code>{view.scope.hashes[r]}</code></p>)}
    </details>
  </div>;
}
