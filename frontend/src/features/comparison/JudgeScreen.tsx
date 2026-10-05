"use client";
import {useEffect,useState} from 'react';
import {useComparison} from './useComparison';
import {useLocalRun} from './useLocalRun';
import {OwnMaterials} from './OwnMaterials';
import {JuryResult} from './JuryResult';
import {JudgeLocale,LanguageSwitch,useJudgeLocale} from './JudgeLocale';
import {Materials} from './Materials';
import {CompareButton} from './CompareButton';
import {initialMode} from './helpers.mjs';
import './comparison.css';

export function JudgeScreen(){return <JudgeLocale><JudgeContent/></JudgeLocale>;}
function JudgeContent(){
  const {t}=useJudgeLocale();
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
    <header><div className="brand"><span className="brand-mark">J</span><span>Judge<small>{t('TRANSLATION COMPARISON','СРАВНЕНИЕ ПЕРЕВОДОВ')}</small></span></div><LanguageSwitch/></header>
    <section className="intro"><h1>{t('One source. Two translations.','Один оригинал. Два перевода.')}<br/>{t('An evidence-based comparison.','Сравнение с доказательствами.')}</h1>
      <p>{t('Compare translation quality, evidence and processing time.','Сравните качество переводов, доказательства и время обработки.')}</p></section>
    <nav className="tabs main-tabs" aria-label={t('Comparison materials','Материалы сравнения')}>
      <button disabled={busy} className={mode==='own'?'selected':''} aria-pressed={mode==='own'} onClick={()=>setMode('own')}>{t('Your materials','Свои материалы')}</button>
      <button disabled={busy} className={mode==='example'?'selected':''} aria-pressed={mode==='example'} onClick={()=>{
        setMode('example');if(work.reference?.kind!=='example'&&work.examples[0])void work.open({kind:'example',id:work.examples[0].id});
      }}>{t('Example','Пример')}</button>
    </nav>
    {(work.error||run.error)&&<p role="alert" className="error">{work.error||run.error}</p>}
    {mode==='own'&&(!visible||work.draft)&&<OwnMaterials draft={work.draft} busy={busy} intake={work.intake} prepare={work.prepare} clearDraft={work.clearDraft}/>}
    {mode==='example'&&<section className="panel"><label>{t('Example','Пример')}<select disabled={busy||!work.examples.length}
      value={work.reference?.kind==='example'?work.reference.id:''} onChange={e=>void work.open({kind:'example',id:e.target.value})}>
      {!work.examples.length&&<option>{t('No saved examples yet','Сохранённых примеров пока нет')}</option>}
      {work.examples.map(e=><option key={e.id} value={e.id}>{e.title}</option>)}
    </select></label></section>}
    {visible&&work.reference&&<>
      <section className="panel comparison-action"><div><h2>{mode==='own'?t('Materials ready','Материалы готовы'):view.title}</h2>
        <p className="muted">{t('Same source · same criteria for A and B','Один оригинал · одинаковые критерии для A и B')}</p></div>
        <CompareButton kind={work.reference.kind} hasReport={!!view.run} enabled={run.enabled}
          busy={busy} hasJob={!!run.job?.id} running={run.running} checking={run.checking} onClick={()=>void compare()}/>
        {mode==='own'&&!run.enabled&&!view.run&&<p className="notice">{t('Materials saved. Live judging requires an operator-configured model and approved budget.','Материалы сохранены. Живому судье нужна настроенная модель и утверждённый бюджет.')}</p>}
        {mode==='own'&&<button disabled={busy} onClick={work.clearDraft}>{t('Other materials','Другие материалы')}</button>}
      </section>
      {run.running&&<p role="status">{t('Judging both translations. Closing this page does not cancel the run.','Судья проверяет оба перевода. Закрытие страницы не отменяет работу.')}</p>}
      {run.job&&['failed','budget_stopped','interrupted'].includes(run.job.status)&&<p role="alert" className="notice">{t('The run is incomplete. No automatic paid retry; the operator must inspect it.','Проверка не завершена. Автоматического повторного списания нет; оператору нужно проверить запуск.')}</p>}
      {(show||!!view.run&&mode==='own')&&<JuryResult view={view}/>}
      <Materials key={view.id} texts={view.scope.texts}/>
    </>}
    <footer>{t('Local preview · Machine assessment of the selected material.','Локальный просмотр · Машинная оценка выбранного материала.')}</footer>
  </main>;
}
