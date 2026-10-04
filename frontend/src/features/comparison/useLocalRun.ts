"use client";
import {useEffect,useRef,useState} from 'react';
import {capabilities,startRun,runStatus,checkReferences} from '../../shared/api/runs';
import type {Reference} from '../../shared/types/comparison';
import type {RunState} from '../../shared/types/options';
export function useLocalRun(reference:Reference|null,reload:(ref:Reference)=>Promise<void>) {
  const [enabled,setEnabled]=useState(false),[checking,setChecking]=useState(false),[error,setError]=useState('');
  const [job,setJob]=useState<RunState|null>(null);
  const key=reference?`${reference.kind}:${reference.id}`:'';
  const current=useRef(key);current.current=key;
  const latestReload=useRef(reload);latestReload.current=reload;
  useEffect(()=>{let active=true;void capabilities().then(x=>{if(active)setEnabled(x.live_enabled);}).catch(()=>{});return()=>{active=false;};},[]);
  useEffect(()=>{setJob(null);setError('');setChecking(false);if(reference?.kind!=='scope')return;
    let active=true;void runStatus(reference.id).then(x=>{if(active)setJob(x);}).catch(()=>{});return()=>{active=false;};
  },[key]);
  useEffect(()=>{if(reference?.kind!=='scope'||!['queued','running','checking_references'].includes(job?.status||''))return;
    let active=true;const timer=setInterval(()=>{void runStatus(reference.id).then(next=>{
      if(!active)return;setJob(next);if(!['queued','running','checking_references'].includes(next.status))void latestReload.current(reference);
    }).catch(()=>{if(active)setError('Не удалось получить состояние. Запуск продолжается на сервере.');});},1000);
    return()=>{active=false;clearInterval(timer);};
  },[key,job?.status]);
  async function start(){if(!reference||reference.kind!=='scope')return;const ticket=key;setError('');
    try{const next=await startRun(reference.id);if(current.current===ticket){setJob(next);
      if(!['queued','running','checking_references'].includes(next.status))await latestReload.current(reference);}}
    catch(e){if(current.current===ticket)setError(e instanceof Error?e.message:'Ошибка запуска.');}}
  async function verify(){if(!reference)return;const ticket=key;setChecking(true);setError('');
    try{await checkReferences(reference);if(current.current===ticket)await latestReload.current(reference);}
    catch{if(current.current===ticket)setError('Не удалось проверить источники. Повторите позднее.');}
    finally{if(current.current===ticket)setChecking(false);}}
  return {enabled,checking,error,job,start,verify,running:['queued','running','checking_references'].includes(job?.status||'')};
}
