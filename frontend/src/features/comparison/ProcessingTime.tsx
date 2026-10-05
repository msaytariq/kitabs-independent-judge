"use client";
import type {ProcessingEffort} from '../../shared/types/rubric';
import {useJudgeLocale} from './JudgeLocale';
// Whole seconds for display; the backend keeps the measured value.
const seconds=(value:number|null|undefined)=>typeof value==='number'?Math.round(value):null;
export function ProcessingTime({effort}:{effort?:ProcessingEffort}) {
  const {t}=useJudgeLocale();const unknown=t('Time not established','Время не установлено');
  const rows=[['pipeline_seconds',t('Pipeline, seconds','Пайплайн, секунды')],['audit_operations',t('Applied audit edits','Применённые правки аудита')],
    ['editor_operations',t('Applied editor edits','Применённые правки редактора')],['simulated_seconds',t('Simulated acceptance, seconds','Смоделированное принятие, секунды')],
    ['total_seconds',t('Total, seconds','Итого, секунды')]] as const;
  return <section className="panel"><h2>{t('Processing time','Время обработки')}</h2>
    <table><thead><tr><th>{t('Measurement','Показатель')}</th><th>A</th><th>B</th></tr></thead><tbody>
      {rows.map(([key,label])=><tr key={key}><th>{label}</th>{(['a','b'] as const).map(side=><td key={side}>{seconds(effort?.sides[side][key])??(key==='total_seconds'?unknown:'—')}</td>)}</tr>)}
    </tbody></table>
    <p>{t('Edits are accepted automatically. Human participation is simulated: 5 seconds to accept one applied audit or editor edit. Proofreading is included in pipeline time.','Правки приняты автоматически. Участие человека смоделировано: 5 секунд на принятие одной применённой правки аудита или редактора. Корректор входит во время пайплайна.')}</p>
    {(['a','b'] as const).map(side=>!!effort?.sides[side].operations.length&&<details key={side}><summary>{side.toUpperCase()} · {t('Applied edits: before / after','Применённые правки: до / после')}</summary>
      {effort.sides[side].operations.map((op,i)=><article key={i}><p>{op.stage==='audit'?t('Audit','Аудит'):t('Editor','Редактор')} · {op.chunk_id}</p>
        <p><del>{op.before}</del></p><p><ins>{op.after}</ins></p></article>)}</details>)}
  </section>;
}
