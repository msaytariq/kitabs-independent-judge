"use client";
import type {EffortReduction as Effort} from '../../shared/types/rubric';
import {useJudgeLocale} from './JudgeLocale';
export function EffortReduction({effort}:{effort?:Effort|null}) {
  const {t}=useJudgeLocale();
  if(!effort) return null;
  const rows:[string,keyof Effort['a']][]=[[t('Edits that remain','Осталось правок'),'edits'],
    [t('of them, errors with quotations','из них ошибки с цитатами'),'defects'],
    [t('of them, missing verses and hadith','из них пропущенные аяты и хадисы'),'missing_quotations'],
    ...(effort.version==='effort-v2'?[[t('of them, missing or wrong references','из них пропущенные или неверные ссылки'),'references']] as [string,keyof Effort['a']][]:[]),
    [t('Acceptance of Kitabs edits, minutes','Принятие правок Kitabs, минуты'),'review_minutes'],
    [t('Editor time, minutes','Время редактора, минуты'),'minutes']];
  const percent=effort.reduction_percent,a=effort.a.minutes,b=effort.b.minutes;
  return <section className="panel"><h2>{t('Editing to publication','Редактура до публикации')}</h2>
    <table><thead><tr><th>{t('Measure','Показатель')}</th><th>A</th><th>B</th></tr></thead><tbody>
      {rows.map(([label,key])=><tr key={key}><th scope="row">{label}</th><td>{effort.a[key]}</td><td>{effort.b[key]}</td></tr>)}
    </tbody></table>
    <p><strong>{a>b&&percent!==null?t(`B saves ${percent}% of the editing time`,`Экономия времени с B: ${percent}%`)
      :a<b?t(`A needs less editing time: ${a} against ${b} minutes`,`A требует меньше редактуры: ${a} против ${b} минут`)
      :t('The editing time is equal','Время редактуры одинаково')}</strong></p>
    {effort.b.done_edits!==undefined&&(effort.a.done_edits||effort.b.done_edits)?<>
      <h3>{t('Editing work that the pipeline has already done','Редактура, которую пайплайн уже сделал')}</h3>
      <table><thead><tr><th>{t('Measure','Показатель')}</th><th>A</th><th>B</th></tr></thead><tbody>
        <tr><th scope="row">{t('Applied audit and editor edits','Применённые правки аудита и редактора')}</th><td>{effort.a.done_edits}</td><td>{effort.b.done_edits}</td></tr>
        <tr><th scope="row">{t('Editor time saved, minutes','Сэкономлено времени редактора, минуты')}</th><td>{effort.a.done_minutes}</td><td>{effort.b.done_minutes}</td></tr>
      </tbody></table>
      <p className="muted">{t('Each edit has a receipt with the text before and after (section Processing time). The judge grades the text after these edits.',
        'У каждой правки есть квитанция с текстом до и после (раздел «Время обработки»). Судья оценивает текст уже после этих правок.')}</p></>:null}
    <p className="muted">{t(`Assumption: ${effort.minutes_per_edit} minutes for one edit by an editor; 5 seconds to accept one edit that Kitabs has already applied.`,
      `Допущение: ${effort.minutes_per_edit} минуты на одну правку редактора; 5 секунд на принятие одной правки, которую Kitabs уже применил.`)}</p>
  </section>;
}
