"use client";
import type {RubricResult,RubricSide,JuryTable,JuryRow,JurySummary} from '../../shared/types/rubric';
import {useJudgeLocale} from './JudgeLocale';
export function RubricTable({result,jury,summary}:{result:RubricResult;jury:JuryTable;summary?:JurySummary|null}) {
  const {t,locale}=useJudgeLocale();
  const labels:Record<string,string>={accuracy:t('Accuracy','Точность'),completeness:t('Completeness','Полнота'),
    terminology:t('Terminology','Терминология'),readability:t('Readability','Читаемость'),
    seamlessness:t('Seamless assembly','Бесшовность сборки'),apparatus:t('Scholarly apparatus','Научный аппарат'),
    quran:t('Quran verses in the translation','Аяты Корана в переводе'),hadith:t('Hadith in the translation','Хадисы в переводе'),
    takhrij:t('Hadith takhrij: collections and hadith numbers','Тахридж хадисов: сборники и номера хадисов'),
    verse_refs:t('Verse references: surah and verse numbers','Ссылки на аяты: номера сур и аятов'),
    editing:t('Editing: the part of the editing work that is done','Редактура: доля выполненной правки'),
    seams:t('Seams: paragraph joins without a broken sentence','Стыки: абзацы без разрыва предложения')};
  const winners:Record<string,string>={a:t('Translation A is better','Лучше перевод A'),
    b:t('Translation B is better','Лучше перевод B'),tie:t('The translations are equal','Переводы равны')};
  const indexed=Object.fromEntries(result.criteria.map(row=>[row.criterion,row]));
  const points=(value:number|null)=><strong className="points">{value===null?'—':value}</strong>;
  const evidence=(s:RubricSide,side:'a'|'b')=><details><summary>{t('Why','Почему')}</summary>
    <p>{locale==='ru'?s.explanation_ru:s.explanation_en}</p>
    {s.evidence.map((e,i)=><article key={e.id+i}><p>{t('Source','Оригинал')}</p><blockquote dir="auto">{e.source_quote}</blockquote>
      <p>{t('Translation','Перевод')} {side.toUpperCase()}</p><blockquote dir="auto">{e.translation_quote}</blockquote>
      <p>{locale==='ru'?e.explanation_ru:e.explanation_en}</p></article>)}
  </details>;
  const cell=(row:JuryRow,side:'a'|'b')=>{
    if(row.kind==='coverage') return <td key={side}>{points(row[side])}<br/><small>{t(`${row.found?.[side]} of ${row.total}`,`${row.found?.[side]} из ${row.total}`)}</small></td>;
    if(row.kind==='seams') return <td key={side}>{points(row[side])}<br/><small>{t(`breaks: ${row.broken?.[side]} of ${row.joins?.[side]}`,`разрывов: ${row.broken?.[side]} из ${row.joins?.[side]}`)}</small></td>;
    if(row.kind==='editing') return <td key={side}>{points(row[side])}<br/><small>{t(`done: ${row.done?.[side]}`,`сделано: ${row.done?.[side]}`)}</small>
      <br/><small>{t(`remaining: ${row.remaining?.[side]}`,`осталось: ${row.remaining?.[side]}`)}</small></td>;
    if(row.kind==='takhrij') return <td key={side}>{points(row[side])}<br/><small>{t(`${row.delivered?.[side]} of ${row.total}`,`${row.delivered?.[side]} из ${row.total}`)}</small>
      <br/><small>{t(`wrong: ${row.wrong?.[side]}`,`неверных: ${row.wrong?.[side]}`)}</small></td>;
    const source=indexed[row.key]?.[side];const level=row.level?.[side];
    return <td key={side}>{points(row[side])}{level!=null&&<><br/><small>{t(`level ${level} of 5`,`уровень ${level} из 5`)}</small></>}
      {row.no_notes?.includes(side)&&<><br/><small>{t('No notes','Сносок нет')}</small></>}
      {source&&row[side]!==null&&evidence(source,side)}</td>;
  };
  return <section className="panel"><h2>{jury.winner?winners[jury.winner]:t('The assessment did not finish.','Оценка не завершена.')}</h2>
    <table><thead><tr><th>{t('Measure, points 0–100','Показатель, баллы 0–100')}</th><th>A</th><th>B</th></tr></thead><tbody>
      {jury.rows.map(row=><tr key={row.key}><th scope="row">{labels[row.key]||row.key}</th>{cell(row,'a')}{cell(row,'b')}</tr>)}
      <tr><th scope="row">{t('Total, 0–100','Итог, 0–100')}</th><td>{points(jury.totals.a)}</td><td>{points(jury.totals.b)}</td></tr>
    </tbody></table>
    {summary&&<ul className="jury-summary">{(locale==='ru'?summary.ru:locale==='ar'?(summary.ar??summary.en):summary.en).map(line=><li key={line}>{line}</li>)}</ul>}
    <p className="muted">{t('Errors with quotations','Ошибки с цитатами')}: A — {result.unique_defects.a}; B — {result.unique_defects.b}.</p>
    <p className="muted">{t('100 — no defects; 75 — small local defects; 50 — notable defects; 25 — many substantive errors; 0 — meaning is systematically distorted.',
      '100 — замечаний нет; 75 — мелкие местные дефекты; 50 — заметные дефекты; 25 — много существенных ошибок; 0 — смысл систематически искажён.')}</p>
    <p className="muted">{t('An AI judge gives levels 1–5 with the same criteria for A and B: 1 = 0, 2 = 25, 3 = 50, 4 = 75, 5 = 100 points. The verse and hadith rows show the part of the source quotations found in the translation. The total is the mean of all rows.',
      'ИИ-судья выставляет уровни 1–5 по одинаковым критериям для A и B: 1 = 0, 2 = 25, 3 = 50, 4 = 75, 5 = 100 баллов. Строки аятов и хадисов — доля цитат оригинала, найденных в переводе. Итог — среднее всех строк.')}</p>
    {jury.rows.some(row=>row.no_notes?.length)&&<p className="muted">{t('Scholarly apparatus: the source gives references, and a translation without anchored notes gets 0 points. The code counts the notes.',
      'Научный аппарат: в оригинале есть ссылки, и перевод без сносок получает 0 баллов. Сноски считает код.')}</p>}
    {jury.rows.some(row=>row.kind==='seams')&&<p className="muted">{t('The seams row: the code reads each join of two prose paragraphs, where also the fragments of a long text join. A join is broken when the first paragraph does not end a sentence or the next one starts in lowercase. No model takes part.',
      'Строка стыков: код проверяет каждый стык двух абзацев текста — там же стыкуются фрагменты длинного текста. Стык разорван, если абзац не закончил предложение или следующий начинается со строчной буквы. Модель не участвует.')}</p>}
    {jury.rows.some(row=>row.kind==='editing')&&<p className="muted">{t('The editing row: applied audit and editor edits with receipts, as a part of all edits (done and still needed). An editor makes the remaining edits: errors with quotations, missing quotations and references.',
      'Строка редактуры: применённые правки аудита и редактора (с квитанциями) как доля всей правки — сделанной и ещё нужной. Оставшиеся правки делает редактор: ошибки с цитатами, пропущенные цитаты и ссылки.')}</p>}
        {jury.rows.some(row=>row.kind==='takhrij')&&<p className="muted">{t('The takhrij and verse reference rows: correct references less wrong references, as a part of the references in the source.',
      'Строки тахриджа и ссылок на аяты: верные ссылки минус неверные, как доля ссылок оригинала.')}</p>}
  </section>;
}
