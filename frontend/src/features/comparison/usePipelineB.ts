"use client";
import {useEffect,useRef,useState} from 'react';
import {pipelineCapabilities,pipelineStatus,startPipeline} from '../../shared/api/pipeline';
import type {PipelineState,PipelineSource} from '../../shared/api/pipeline';
const STORAGE='judge-pipeline-request';
export function usePipelineB(onReady:(job:PipelineState)=>void){
  const [enabled,setEnabled]=useState(false),[remaining,setRemaining]=useState<number|null>(null),[job,setJob]=useState<PipelineState|null>(null);
  const [requestId,setRequestId]=useState<string|null>(null),[starting,setStarting]=useState(false),[error,setError]=useState('');
  const callback=useRef(onReady);callback.current=onReady;
  const busyRef=useRef(false),delivered=useRef<string|null>(null);
  useEffect(()=>{let active=true;setRequestId(localStorage.getItem(STORAGE));
    void pipelineCapabilities().then(r=>{if(active){setEnabled(r.enabled);setRemaining(r.remaining??null);}}).catch(()=>{});
    return()=>{active=false;};},[]);
  useEffect(()=>{if(!requestId)return;let active=true;
    async function poll(){try{const next=await pipelineStatus(requestId!);if(active){setJob(next);setError('');}}
      catch{if(active)setError('pipeline_unavailable');}}
    void poll();const timer=setInterval(()=>void poll(),2000);
    return()=>{active=false;clearInterval(timer);};},[requestId]);
  useEffect(()=>{if(job?.status==='completed'&&job.result&&delivered.current!==job.id){
    delivered.current=job.id;callback.current(job);
  }},[job]);
  async function start(source:PipelineSource){if(busyRef.current||requestId)return;
    busyRef.current=true;setStarting(true);setError('');
    const id=crypto.randomUUID();localStorage.setItem(STORAGE,id);setRequestId(id);
    try{setJob(await startPipeline(id,source));}catch(e){setError(e instanceof Error?e.message:'pipeline_unavailable');}
    finally{busyRef.current=false;setStarting(false);}}
  function clear(){setRequestId(null);setJob(null);setError('');delivered.current=null;localStorage.removeItem(STORAGE);}
  const running=starting||!!job&&['queued','uploading','creating','running'].includes(job.status);
  return {enabled,remaining,job,requestId,running,error,start,clear};
}
