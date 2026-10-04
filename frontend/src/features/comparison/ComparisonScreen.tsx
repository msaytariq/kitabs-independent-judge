"use client";
import {useEffect,useState} from 'react';
import {useComparison} from './useComparison';
import {OwnMaterials} from './OwnMaterials';
import {Materials} from './Materials';
import {ComparisonResult} from './ComparisonResult';
import {GeneratedApparatus} from './GeneratedApparatus';
import {SourceReview} from './SourceReview';
import {reportUrl} from '../../shared/api/comparison';
import './comparison.css';

export function ComparisonScreen() {
  const work = useComparison();
  const [mode,setMode] = useState('example'), [shownId,setShownId] = useState('');
  useEffect(()=>{if(work.reference?.kind==='scope') setMode('own');},[work.reference?.kind,work.reference?.id]);
  const view = work.view;
  const visible = view && (mode==='example'?work.reference?.kind==='example':work.reference?.kind==='scope');
  return <main className="comparison-screen">
    <header><div className="brand"><span className="brand-mark">IJ</span><span>Независимый судья<small>KITABS.AI · СРАВНЕНИЕ ПЕРЕВОДОВ</small></span></div>
    <span className="environment">Локальный стенд</span></header>
    <section className="intro"><h1>Сколько правок<br/>нужно переводу?</h1>
      <p>Один оригинал и два перевода. Замечания по смыслу, терминологии и стилю — с цитатами и обоснованиями. Научный аппарат — отдельно.</p></section>
    <nav className="tabs main-tabs" aria-label="Материалы сравнения">
      <button disabled={work.busy} className={mode==='example'?'selected':''} aria-pressed={mode==='example'} onClick={()=>{setMode('example'); if(work.reference?.kind!=='example'&&work.examples[0]) void work.open({kind:'example',id:work.examples[0].id});}}>Готовый пример</button>
      <button disabled={work.busy} className={mode==='own'?'selected':''} aria-pressed={mode==='own'} onClick={()=>setMode('own')}>Свои материалы</button>
    </nav>
    {work.error&&<div className="error" role="alert">{work.error}</div>}
    {work.busy&&<p role="status">Загружаю сохранённые материалы…</p>}
    {mode==='example'&&<section className="panel example-picker">
      <label>Выберите пример<select disabled={work.busy||!work.examples.length} value={work.reference?.kind==='example'?work.reference.id:''}
        onChange={e=>{setShownId('');void work.open({kind:'example',id:e.target.value});}}>
        {!work.examples.length&&<option>Примеры ещё не подготовлены</option>}
        {work.examples.map(e=><option value={e.id} key={e.id}>{e.title}{e.has_report?' · есть результат':e.has_source_review?' · разбор по источникам':' · без оценки'}</option>)}
      </select></label>
      {visible&&<><p>{view.description}</p><p className="muted">A: {view.provenance?.a}.<br/>B: {view.provenance?.b}.</p>
      <button className="primary" disabled={work.busy} onClick={()=>setShownId(view.id)}>{view.run?'Показать сравнение':'Показать состояние проверки'}</button>
      <span className="action-caption">{view.run?'Используем сохранённый результат — без нового ИИ-запуска.':'Границы сверены; ИИ-оценка ещё не проводилась.'}</span></>}
    </section>}
    {mode==='own'&&(!visible||work.draft)&&<OwnMaterials draft={work.draft} busy={work.busy} intake={work.intake} prepare={work.prepare} clearDraft={work.clearDraft}/>}
    {mode==='own'&&visible&&!work.draft&&<button disabled={work.busy} onClick={work.clearDraft}>Загрузить другие материалы</button>}
    {visible&&!work.busy&&<>
      {view.source_review&&work.reference&&<SourceReview review={view.source_review} reportHref={reportUrl(work.reference)}/>}
      {view.generated_apparatus&&<GeneratedApparatus evidence={view.generated_apparatus}/>}
      {view.boundary_review&&<details className="panel boundary"><summary>Границы примера проверены · паспорт версии 2</summary>
        <p>{view.boundary_review.note_ru}</p><p>Начало: {view.boundary_review.start_ru}</p><p>Конец: {view.boundary_review.end_ru}</p>
        <p className="muted">{view.boundary_review.reviewer}</p>
        {view.boundary_review.previous_review_id&&<a href={`/editorial/#${view.boundary_review.previous_review_id}`}>Предыдущая запись сохранена</a>}
      </details>}
      {(shownId===view.id||work.reference?.kind==='scope')&&work.reference&&<ComparisonResult view={view} reference={work.reference}/>}
      <Materials key={view.id} texts={view.scope.texts}/>
    </>}
    <footer>Находки модели требуют проверки. Окончательное решение о необходимых правках принимает человек.</footer>
  </main>;
}
