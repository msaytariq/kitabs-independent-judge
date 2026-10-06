"use client";
import {Fragment,useState} from 'react';
import type {RubricResult,RubricSide,JuryTable,JuryRow,CriticalError} from '../../shared/types/rubric';
import {useJudgeLocale} from './JudgeLocale';
import {MethodLink} from './MethodLink';
// The winner and the summary lines are in the verdict card; this table gives the scores and the reasons.
export function RubricTable({result,jury}:{result:RubricResult;jury:JuryTable}) {
  const {t,locale}=useJudgeLocale();
  const [open,setOpen]=useState<Record<string,boolean>>({});
  const labels:Record<string,string>={accuracy:t('Accuracy','Точность'),completeness:t('Completeness','Полнота'),
    terminology:t('Terminology','Терминология'),readability:t('Readability','Читаемость'),
    seamlessness:t('Seamless assembly','Бесшовность сборки'),apparatus:t('Scholarly apparatus','Научный аппарат'),
    quran:t('Quran verses in the translation','Аяты Корана в переводе'),hadith:t('Hadith in the translation','Хадисы в переводе'),
    takhrij:t('Hadith takhrij: collections and hadith numbers','Тахридж хадисов: сборники и номера хадисов'),
    verse_refs:t('Verse references: surah and verse numbers','Ссылки на аяты: номера сур и аятов'),
    editing:t('Editing: the part of the editing work that is done','Редактура: доля выполненной правки'),
    seams:t('Seams: paragraph joins without a broken sentence','Стыки: абзацы без разрыва предложения'),
    critical:t('Critical errors, count','Критические ошибки, число')};
  const categories:Record<CriticalError['category'],string>={meaning_reversed:t('Meaning reversed','Смысл перевёрнут'),
    content_invented:t('Invented content','Выдуманное содержание'),unit_omitted:t('Omitted text','Пропуск текста'),
    quotation_corrupted:t('Verse or hadith changed','Искажён аят или хадис'),attribution_wrong:t('Wrong attribution or reference','Неверная атрибуция или ссылка')};
  const indexed=Object.fromEntries(result.criteria.map(row=>[row.criterion,row]));
  const points=(value:number|null)=><strong className="points">{value===null?'—':value}</strong>;
  const evidence=(s:RubricSide,side:'a'|'b')=><>
    <p dir="auto">{locale==='ru'?s.explanation_ru:s.explanation_en}</p>
    {s.evidence.map((e,i)=><article key={e.id+i}><p>{t('Source','Оригинал')}</p><blockquote dir="auto">{e.source_quote}</blockquote>
      <p>{t('Translation','Перевод')} {side.toUpperCase()}</p><blockquote dir="auto">{e.translation_quote}</blockquote>
      <p dir="auto">{locale==='ru'?e.explanation_ru:e.explanation_en}</p></article>)}
  </>;
  const critical=(errors:CriticalError[],side:'a'|'b')=>errors.map(e=><article key={e.id}><p><strong>{categories[e.category]}</strong></p><p>{t('Source','Оригинал')}</p><blockquote dir="auto">{e.source_quote}</blockquote>
      <p>{t('Translation','Перевод')} {side.toUpperCase()}</p><blockquote dir="auto">{e.translation_quote}</blockquote>
      <p dir="auto">{locale==='ru'?e.explanation_ru:e.explanation_en}</p></article>);
  // The reasons of a row open under it at full width: A and B side by side, one under the other on a phone.
  const reasons=(row:JuryRow,side:'a'|'b')=>{
    if(row.kind==='critical'){const errors=row.errors?.[side]??[];return errors.length?critical(errors,side):null;}
    const source=indexed[row.key]?.[side];
    return source&&row[side]!==null&&row.kind==='criterion'?evidence(source,side):null;
  };
  const cell=(row:JuryRow,side:'a'|'b')=>{
    if(row.kind==='critical') return <td key={side} className={row[side]?'bad':undefined}>{points(row[side])}</td>;
    if(row.kind==='coverage') return <td key={side}>{points(row[side])}<br/><small>{t(`${row.found?.[side]} of ${row.total}`,`${row.found?.[side]} из ${row.total}`)}</small></td>;
    if(row.kind==='seams') return <td key={side}>{points(row[side])}<br/><small>{t(`breaks: ${row.broken?.[side]} of ${row.joins?.[side]}`,`разрывов: ${row.broken?.[side]} из ${row.joins?.[side]}`)}</small></td>;
    if(row.kind==='editing') return <td key={side}>{points(row[side])}<br/><small>{t(`done: ${row.done?.[side]}`,`сделано: ${row.done?.[side]}`)}</small>
      <br/><small>{t(`remaining: ${row.remaining?.[side]}`,`осталось: ${row.remaining?.[side]}`)}</small></td>;
    if(row.kind==='takhrij') return <td key={side}>{points(row[side])}<br/><small>{t(`${row.delivered?.[side]} of ${row.total}`,`${row.delivered?.[side]} из ${row.total}`)}</small>
      <br/><small>{t(`wrong: ${row.wrong?.[side]}`,`неверных: ${row.wrong?.[side]}`)}</small></td>;
    const level=row.level?.[side];
    return <td key={side}>{points(row[side])}{level!=null&&<><br/><small>{t(`level ${level} of 5`,`уровень ${level} из 5`)}</small></>}
      {row.no_notes?.includes(side)&&<><br/><small>{t('No apparatus','Аппарата нет')}</small></>}
      {row.seam_breaks?.[side]?<><br/><small>{t(`broken sentences: ${row.seam_breaks[side]}`,`разорванных фраз: ${row.seam_breaks[side]}`)}</small></>:null}</td>;
  };
  const line=(row:JuryRow)=>{
    const id=`why-${row.key}`,parts=(['a','b'] as const).map(side=>reasons(row,side));
    const has=parts.some(Boolean),shown=!!open[row.key];
    return <Fragment key={row.key}><tr><th scope="row">{labels[row.key]||row.key}<br/><small className="row-source">{origin(row)}</small>
        {has&&<><br/><button type="button" className="why" aria-expanded={shown} aria-controls={id}
          onClick={()=>setOpen({...open,[row.key]:!shown})}>{row.kind==='critical'?t('Which errors','Какие'):t('Why','Почему')}</button></>}</th>
        {cell(row,'a')}{cell(row,'b')}</tr>
      {has&&<tr id={id} className="why-row" hidden={!shown}><td colSpan={3}><div className="why-sides">
        {(['a','b'] as const).map((side,i)=><div key={side}><h3>{t(`Translation ${side.toUpperCase()}`,`Перевод ${side.toUpperCase()}`)}</h3>
          {parts[i]??<p className="muted">—</p>}</div>)}</div></td></tr>}</Fragment>;
  };
  const note=(text:React.ReactNode)=><p className="muted">{text}</p>;
  // Who gives the points of a row: the AI judge (levels 1-5) or a count by the code.
  const origin=(row:JuryRow)=>row.kind==='critical'?t('Not in the total','Не входит в итог')
    :row.kind==='criterion'?t('AI judge','ИИ-судья'):t('Count','Подсчёт');
  // The total in plain numbers: the same rows and rounding as the total row (jury_points._total).
  const counted=jury.rows.filter(row=>row.kind!=='critical'&&row.a!==null&&row.b!==null);
  const sum=(side:'a'|'b')=>counted.reduce((total,row)=>total+(row[side] as number),0);
  const mean=(side:'a'|'b')=>Math.floor(sum(side)/counted.length+0.5);
  return <section className="panel"><h2>{t('Scores','Оценки')}</h2>
    <table className={jury.winner==='a'||jury.winner==='b'?`rubric-table win-${jury.winner}`:'rubric-table'}><thead><tr><th>{t('Measure, points 0–100','Показатель, баллы 0–100')}</th><th>A</th><th>B</th></tr></thead><tbody>
      {jury.rows.map(line)}
      <tr className="total-row"><th scope="row">{t('Total, 0–100','Итог, 0–100')}</th><td>{points(jury.totals.a)}</td><td>{points(jury.totals.b)}</td></tr>
    </tbody></table>
    {counted.length>0&&<div className="total-explained"><h3>{t('How the total is made','Как получается итог')}</h3><ul>
      <li>{t('Each row gives A and B from 0 to 100 points.','В каждой строке у A и B оценка от 0 до 100 баллов.')}</li>
      <li>{t('Rows "AI judge": an AI model reads the source and the two translations. It does not know which vendor made each translation. For each row it selects a level from 1 to 5 by a written definition: 1 = 0 points, 2 = 25, 3 = 50, 4 = 75, 5 = 100.',
        'Строки «ИИ-судья»: модель ИИ читает оригинал и оба перевода и не знает, чей какой перевод. По каждой строке она ставит уровень от 1 до 5 по готовому описанию: 1 = 0 баллов, 2 = 25, 3 = 50, 4 = 75, 5 = 100.')}</li>
      <li>{t('Rows "Count": the code counts the verses, the hadith, the references, the seams and the edits without AI. The points are the part that the code finds: for example, 3 of 4 = 75.',
        'Строки «Подсчёт»: программа считает аяты, хадисы, ссылки, стыки и правки без ИИ. Балл — доля найденного: например, 3 из 4 = 75.')}</li>
      <li><strong>{t('Total = the mean of all rows','Итог = среднее всех строк')}: A — {sum('a')} ÷ {counted.length} = {mean('a')}; B — {sum('b')} ÷ {counted.length} = {mean('b')}.</strong> {t('The higher total wins.','Побеждает больший итог.')}</li>
      {jury.rows.some(row=>row.kind==='critical')&&<li>{t('Critical errors and the second judge are not part of the total.','Критические ошибки и второй судья в итог не входят.')}</li>}
    </ul></div>}
    <p className="muted">{t('Errors with quotations','Ошибки с цитатами')}: A — {result.unique_defects.a}; B — {result.unique_defects.b}.</p>
    {jury.rows.some(row=>row.kind==='critical')&&note(t('Critical errors: the judge lists them, and the code counts an error only when it finds both quotes. The count is not part of the total. In Kitabs.ai, a person corrects each critical error: the audit and the editor propose an edit, and the person accepts or rejects it. Chat and other AI translation services that work without a person do not have this step.',
      'Критические ошибки: их перечисляет судья, код засчитывает ошибку, только если нашёл обе цитаты. В итог не входит. В Kitabs.ai критическую ошибку исправляет человек: аудит и редактор предлагают правку, человек принимает или отклоняет её. У чата и других сервисов ИИ перевода без участия человека такого шага нет.'))}
    <MethodLink/>
    <details className="table-notes"><summary>{t('How to read the table','Как читать таблицу')}</summary>
    <p className="muted">{t('100 — no defects; 75 — small local defects; 50 — notable defects; 25 — many substantive errors; 0 — meaning is systematically distorted.',
      '100 — замечаний нет; 75 — мелкие местные дефекты; 50 — заметные дефекты; 25 — много существенных ошибок; 0 — смысл систематически искажён.')}</p>
    <p className="muted">{t('An AI judge gives levels 1–5 with the same criteria for A and B: 1 = 0, 2 = 25, 3 = 50, 4 = 75, 5 = 100 points. The verse and hadith rows show the part of the source quotations found in the translation. The total is the mean of all rows.',
      'ИИ-судья выставляет уровни 1–5 по одинаковым критериям для A и B: 1 = 0, 2 = 25, 3 = 50, 4 = 75, 5 = 100 баллов. Строки аятов и хадисов — доля цитат оригинала, найденных в переводе. Итог — среднее всех строк.')}</p>
    {jury.rows.some(row=>row.no_notes?.length)&&<p className="muted">{t('Scholarly apparatus: the source gives references, and a translation without an apparatus (anchored notes, glossary or person index) gets 0 points. The code counts them.',
      'Научный аппарат: в оригинале есть ссылки, и перевод без аппарата (сносок, глоссария или списка лиц) получает 0 баллов. Их считает код.')}</p>}
    {jury.rows.some(row=>row.kind==='seams')&&<p className="muted">{t('The seams row: the code reads each join of two prose paragraphs, where also the fragments of a long text join. A join is broken when the first paragraph does not end a sentence or the next one starts in lowercase. No model takes part.',
      'Строка стыков: код проверяет каждый стык двух абзацев текста — там же стыкуются фрагменты длинного текста. Стык разорван, если абзац не закончил предложение или следующий начинается со строчной буквы. Модель не участвует.')}</p>}
    {jury.rows.some(row=>row.kind==='editing')&&<p className="muted">{t('The editing row: applied audit and editor edits with receipts, as a part of all edits (done and still needed). An editor makes the remaining edits: errors with quotations, missing quotations and references.',
      'Строка редактуры: применённые правки аудита и редактора (с квитанциями) как доля всей правки — сделанной и ещё нужной. Оставшиеся правки делает редактор: ошибки с цитатами, пропущенные цитаты и ссылки.')}</p>}
    {jury.rows.some(row=>row.kind==='takhrij')&&<p className="muted">{t('The takhrij and verse reference rows: correct references less wrong references, as a part of the references in the source.',
      'Строки тахриджа и ссылок на аяты: верные ссылки минус неверные, как доля ссылок оригинала.')}</p>}
    </details>
  </section>;
}
