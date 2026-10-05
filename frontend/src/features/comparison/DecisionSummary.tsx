"use client";
import type {DecisionEffort} from '../../shared/types/comparison';
import {useJudgeLocale} from './JudgeLocale';
export function DecisionSummary({effort}:{effort:DecisionEffort}) {
  const {t}=useJudgeLocale();const unknown=t('Unknown','Неизвестно');
  return <details className="panel"><summary>{t('Work estimate — assuming 5 seconds per decision','Оценка работы — допущение: 5 секунд на решение')}</summary>
    <p>{t('Each remaining candidate counts as one hypothetical decision. This is not measured editing time. Reading, research and writing are excluded.','Каждый оставшийся кандидат считается одним предполагаемым решением. Это не измеренное время редактирования. Чтение, исследование и написание текста не учтены.')}</p>
    <table><thead><tr><th>{t('Work','Работа')}</th><th>A</th><th>B</th></tr></thead><tbody>
      <tr><th>{t('Remaining decision estimate, seconds','Оценка оставшихся решений, секунды')}</th>{(['a','b'] as const).map(s=><td key={s}>{effort.sides[s].remaining_estimated_seconds??unknown}</td>)}</tr>
      <tr><th>{t('Prior human decisions','Предыдущие решения человека')}</th>{(['a','b'] as const).map(s=><td key={s}>{effort.sides[s].prior_decisions??unknown}</td>)}</tr>
      <tr><th>{t('Accepted / rejected','Принято / отклонено')}</th>{(['a','b'] as const).map(s=><td key={s}>{effort.sides[s].accepted??unknown} / {effort.sides[s].rejected??unknown}</td>)}</tr>
      <tr><th>{t('Prior decision estimate, seconds','Оценка прошлых решений, секунды')}</th>{(['a','b'] as const).map(s=><td key={s}>{effort.sides[s].prior_estimated_seconds??unknown}</td>)}</tr>
    </tbody></table>
    <p className="muted">{t('Autopilot output does not prove zero previous human work. Unknown history stays unknown. A candidate is not a confirmed required correction.','Автопилот не доказывает отсутствие предыдущей работы человека. Неизвестная история остаётся неизвестной. Кандидат не является подтверждённой необходимой правкой.')}</p>
  </details>;
}
