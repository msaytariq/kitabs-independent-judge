"use client";
import type {PairedResult} from '../../shared/types/paired';
import {useJudgeLocale} from './JudgeLocale';
export function PairedTable({result}:{result:PairedResult}) {
  const {t,locale}=useJudgeLocale();
  const labels:Record<string,string>={accuracy:t('Accuracy','Точность'),completeness:t('Completeness','Полнота'),
    terminology:t('Terminology','Терминология'),readability:t('Readability','Читаемость'),
    seamlessness:t('Assembly integrity','Целостность сборки'),apparatus:t('Scholarly apparatus','Научный аппарат')};
  const states:Record<string,string>={not_assessed:t('Not assessed','Не оценено'),not_applicable:t('Not applicable','Не применимо'),
    unstable:t('Unstable','Неустойчиво'),unverified_evidence:t('Evidence not located','Цитата не подтверждена')};
  const reasons:Record<string,string>={score_changed:t('The grade changed after A and B changed places.','Оценка изменилась после перестановки A и B.'),
    status_changed:t('The passes gave different statuses.','Проходы дали разные статусы.'),
    evidence_not_located:t('One pass cited a quotation that is not in the text.','Один из проходов привёл цитату, которой нет в тексте.'),
    evidence_conflict:t('The passes reached opposite conclusions on the same quotation.','Проходы пришли к противоположным выводам по одной и той же цитате.'),
    symmetry:t('Identical texts received different grades.','Одинаковые тексты получили разные оценки.')};
  const verdicts:Record<string,string>={a:t('A has the advantage on this material','На этом материале преимущество у A'),
    b:t('B has the advantage on this material','На этом материале преимущество у B'),
    mixed:t('Each translation has advantages','Преимущества по разным критериям'),
    none:t('No stable advantage established','Устойчивое преимущество не установлено')};
  return <section className="panel"><h2>{verdicts[result.advantage]||verdicts.none}</h2>
    <p>{t('Machine assessment · 1–5 · selected material only','Машинная оценка · 1–5 · только выбранный материал')}</p>
    <table><thead><tr><th>{t('Criterion','Критерий')}</th><th>A</th><th>B</th></tr></thead><tbody>
      {result.criteria.map(row=><tr key={row.criterion}><th scope="row">{labels[row.criterion]}</th>{(['a','b'] as const).map(side=>{
        const s=row[side];return <td key={side}><strong>{s.score===null?(states[s.status]||states.not_assessed):`${s.score} / 5`}</strong>
          {s.status==='unstable'&&<p className="muted">{t('Passes','Проходы')}: {s.pass_scores.map(v=>v??'—').join(' / ')}</p>}
          {(s.instability||(s.evidence_conflict&&'evidence_conflict'))&&<p className="muted">{reasons[s.instability||'evidence_conflict']}</p>}
          <details><summary>{t('Evidence and coverage','Доказательства и охват')}</summary>
            <p>{s.coverage.every(v=>v==='whole_selected_range')?t('The model reports checking the selected range.','Модель заявляет проверку выбранного диапазона.'):t('Partial coverage.','Частичный охват.')}</p>
            {s.explanations.map((e,i)=><p key={i}>{locale==='ru'?e.explanation_ru:e.explanation_en}</p>)}
            {s.evidence.map((e,i)=><article key={e.id+i}><p>{t('Source','Оригинал')}</p><blockquote dir="auto">{e.source_quote}</blockquote>
              <p>{t('Translation','Перевод')} {side.toUpperCase()}</p><blockquote dir="auto">{e.translation_quote}</blockquote>
              <p>{locale==='ru'?e.explanation_ru:e.explanation_en}</p>
              <small>{e.verified?t('Exact quote located; judgment remains machine-generated.','Точная цитата найдена; вывод сделан машиной.'):t('Quote is missing or ambiguous.','Цитата не найдена или неоднозначна.')}</small>
            </article>)}
          </details></td>;})}</tr>)}
    </tbody></table>
    <p className="muted">{t('Unique located defect candidates','Уникальные привязанные кандидаты на ошибки')}: A — {result.unique_defects.a}; B — {result.unique_defects.b}.
      {' '}{t('Counts do not measure how many times better a translation is.','Количество не показывает, во сколько раз перевод качественнее.')}</p>
  </section>;
}
