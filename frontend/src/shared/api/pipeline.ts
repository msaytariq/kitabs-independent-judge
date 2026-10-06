import type {InputMethod} from '../types/comparison';
import {apiUrl} from './base';
export type PipelineProgress={percent:number;stage:string|null;chunk:number|null;chunks:number|null;
  steps:{key:'preparation'|'translation'|'apparatus'|'assembly';state:'done'|'current'|'waiting'}[]};
export type PipelineState={id:string;status:string;source:string|null;source_sha256:string|null;
  progress?:PipelineProgress|null;started_at?:number|null;job_id:string|null;error:string|null;
  result:{text:string;sha256:string;source_sha256:string}|null};
export type PipelineSource={method:InputMethod;value:string;file?:File;source_language:string;target_language:string};
// The server answered with a refusal: nothing was started for this request.
export class PipelineRefusal extends Error{constructor(readonly code:string,readonly detail:string){super(code);}}
async function request<T>(path:string, body?:FormData):Promise<T>{
  const response=await fetch(apiUrl(path),{method:body?'POST':'GET',body,cache:'no-store'});
  const data=await response.json().catch(()=>({}));
  if(response.status>=400&&response.status<500)throw new PipelineRefusal(data.error?.code||'pipeline_unavailable',data.error?.message||'');
  if(!response.ok)throw new Error('pipeline_unavailable');
  return data;
}
export const pipelineCapabilities=()=>request<{enabled:boolean;remaining?:number|null}>('/api/pipeline-b/capabilities');
export const pipelineStatus=(id:string)=>request<PipelineState>('/api/pipeline-b/'+encodeURIComponent(id));
export function startPipeline(id:string, source:PipelineSource){
  const form=new FormData();form.append('request_id',id);form.append('source_kind',source.method);
  form.append('source_value',source.value);form.append('source_language',source.source_language);
  form.append('target_language',source.target_language);
  if(source.file)form.append('source',source.file);
  return request<PipelineState>('/api/pipeline-b',form);
}
