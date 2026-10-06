"use client";
import {useEffect,useState} from 'react';
import type {PipelineState} from '../../shared/api/pipeline';
import {useJudgeLocale} from './JudgeLocale';
// A visible sign that Kitabs works: finished steps, the current fragment and stage, and the time.
export function PipelineProgressBar({job}:{job:PipelineState}){
  const {t}=useJudgeLocale();
  const [now,setNow]=useState(()=>Date.now());
  useEffect(()=>{const timer=setInterval(()=>setNow(Date.now()),1000);return()=>clearInterval(timer);},[]);
  const progress=job.progress,percent=job.status==='completed'?100:progress?.percent??0;
  const stages:Record<string,string>={translator:t('translation','перевод'),audit:t('audit','аудит'),editor:t('editing','редактура'),
    proofreader:t('proofreading','корректура'),apparatus:t('scholarly apparatus','научный аппарат'),assembly:t('assembly','сборка')};
  const phases:Record<string,string>={preparation:t('Preparation','Подготовка'),translation:t('Fragments: translation, audit, editing, proofreading','Фрагменты: перевод, аудит, редактура, корректура'),
    apparatus:t('Scholarly apparatus','Научный аппарат'),assembly:t('Seamless assembly','Бесшовная сборка')};
  const seconds=job.started_at?Math.max(0,Math.round(now/1000-job.started_at)):null;
  const elapsed=seconds===null?'':` · ${Math.floor(seconds/60)}:${String(seconds%60).padStart(2,'0')}`;
  const stage=progress?.stage&&stages[progress.stage];
  const where=progress?.chunks?t(`Fragment ${progress.chunk} of ${progress.chunks}`,`Фрагмент ${progress.chunk} из ${progress.chunks}`)
    +(stage?' · '+stage:''):t('Preparing the source','Подготовка оригинала');
  return <div className="pipeline-progress">
    <div className="progress-track" role="progressbar" aria-valuemin={0} aria-valuemax={100} aria-valuenow={percent}>
      <div className={'progress-fill'+(progress?'':' progress-waiting')} style={{width:`${Math.max(percent,4)}%`}}/></div>
    <p><strong>{percent}%</strong> · {job.status==='completed'?t('B is ready','B готов'):where}{elapsed}</p>
    {progress&&<ol className="progress-steps">{progress.steps.map(s=><li key={s.key} className={s.state}>
      {s.state==='done'?'✓ ':s.state==='current'?'● ':'○ '}{phases[s.key]}</li>)}</ol>}
  </div>;
}
