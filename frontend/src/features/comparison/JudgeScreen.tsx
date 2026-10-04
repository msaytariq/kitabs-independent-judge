"use client";
import {useEffect,useState} from 'react';
import {useComparison} from './useComparison';
import {useLocalRun} from './useLocalRun';
import {OwnMaterials} from './OwnMaterials';
import {ComparisonResult} from './ComparisonResult';
import {Materials} from './Materials';
import {CompareButton} from './CompareButton';
import {initialMode} from './helpers.mjs';
import './comparison.css';

export function JudgeScreen(){
  const work=useComparison();
  const run=useLocalRun(work.reference,work.open);
  const [mode,setMode]=useState('own'),[show,setShow]=useState(false);
  useEffect(()=>{setMode(initialMode(window.location.hash));},[]);
  useEffect(()=>{setShow(false);if(work.reference?.kind==='scope')setMode('own');},[work.reference?.id]);
  const view=work.view;
  const visible=view&&(mode==='own'?work.reference?.kind==='scope':work.reference?.kind==='example');
  const busy=work.busy||run.running||run.checking;
  async function compare(){setShow(true);if(work.reference?.kind==='scope'&&!view?.run)await run.start();else await run.verify();}
  return <main className="comparison-screen">
    <header><div className="brand"><span className="brand-mark">IJ</span><span>Независимый судья<small>СРАВНЕНИЕ ПЕРЕВОДОВ</small></span></div><span className="environment">Локальный стенд</span></header>
    <section className="intro"><h1>Один оригинал.<br/>Два перевода. Ясный итог.</h1>
      <p>Сравните оставшиеся правки и проверьте хадисы по источникам.</p></section>
    <nav className="tabs main-tabs" aria-label="Материалы сравнения">
      <button disabled={busy} className={mode==='own'?'selected':''} aria-pressed={mode==='own'} onClick={()=>setMode('own')}>Свои материалы</button>
      <button disabled={busy} className={mode==='example'?'selected':''} aria-pressed={mode==='example'} onClick={()=>{
        setMode('example');if(work.reference?.kind!=='example'&&work.examples[0])void work.open({kind:'example',id:work.examples[0].id});
      }}>Готовый пример</button>
    </nav>
    {(work.error||run.error)&&<p role="alert" className="error">{work.error||run.error}</p>}
    {mode==='own'&&(!visible||work.draft)&&<OwnMaterials draft={work.draft} busy={busy} intake={work.intake} prepare={work.prepare} clearDraft={work.clearDraft}/>}
    {mode==='example'&&<section className="panel"><label>Пример<select disabled={busy||!work.examples.length}
      value={work.reference?.kind==='example'?work.reference.id:''} onChange={e=>void work.open({kind:'example',id:e.target.value})}>
      {!work.examples.length&&<option>Сохранённых примеров пока нет</option>}
      {work.examples.map(e=><option key={e.id} value={e.id}>{e.title}</option>)}
    </select></label></section>}
    {visible&&work.reference&&<>
      <section className="panel comparison-action"><div><h2>{mode==='own'?'Материалы готовы':view.title}</h2>
        <p className="muted">Оригинал и версии A/B · одинаковые критерии оценки</p></div>
        <CompareButton kind={work.reference.kind} hasReport={!!view.run} enabled={run.enabled}
          busy={busy} hasJob={!!run.job?.id} running={run.running} checking={run.checking} onClick={()=>void compare()}/>
        {mode==='own'&&!run.enabled&&!view.run&&<p className="notice">Материалы сохранены. Живой судья ожидает настройки модели и утверждённого бюджета оператора.</p>}
        {mode==='own'&&<button disabled={busy} onClick={work.clearDraft}>Другие материалы</button>}
      </section>
      {run.running&&<p role="status">Судья проверяет оба перевода. Закрытие страницы не отменяет работу.</p>}
      {run.job&&['failed','budget_stopped','interrupted'].includes(run.job.status)&&<p role="alert" className="notice">Проверка не завершена. Автоматического повторного списания нет; оператору нужно проверить сохранённый запуск.</p>}
      {(show||!!view.run&&mode==='own')&&<ComparisonResult view={view} reference={work.reference}/>}
      <Materials key={view.id} texts={view.scope.texts}/>
    </>}
    <footer>Автоматические замечания и прогноз помогают редактору. Итоговое решение остаётся за человеком.</footer>
  </main>;
}
