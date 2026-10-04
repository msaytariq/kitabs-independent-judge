import type {Effort} from '../../shared/types/options';
export function EffortSummary({effort}:{effort:Effort}) {
  const value=effort.reduction_percent;
  return <section className="panel effort-summary">
    <h3>Оставшаяся работа редактора</h3>
    <p className="forecast-value">{value===null?'Недостаточно данных':`${value}%`}</p>
    <p>{value===null?'Процент появится после оценки при ненулевой базе A.':'Прогноз сокращения трудозатрат на исправления B относительно A'}</p>
    <p className="muted">По замечаниям модели · не измеренное время</p>
    <details><summary>Как рассчитано</summary>
      <p>Кандидатов на исправление: A — {effort.sides.a.edits??'не оценено'}, B — {effort.sides.b.edits??'не оценено'}.
        {effort.edit_reduction_percent!==null&&` Сокращение числа правок: ${effort.edit_reduction_percent}%.`}</p>
      <p>Условная сложность: критические — 5, терминология — 3, научный аппарат — 4, стиль — 1.
        Веса одинаковы для A и B и пока не откалиброваны по работе экспертов.</p>
      {effort.sensitivity_percent&&<p>При изменении весов: {effort.sensitivity_percent[0]}…{effort.sensitivity_percent[1]}%.
        Это чувствительность расчёта, не доверительный интервал.</p>}
      <p>Спорные и непривязанные находки исключены: A — {effort.sides.a.excluded}, B — {effort.sides.b.excluded}.
        Формула: (1 − работа B / работа A) × 100%. Отрицательное значение означает больше работы для B.</p>
      <p>Чтение, проверка правильных мест и предыдущий человеческий труд не оценены.
        100% означает отсутствие включённых находок в B, а не отсутствие работы редактора.</p>
    </details>
  </section>;
}
