import {currentError} from '../i18n/intake';
import type {Reference} from '../types/comparison';
import type {ReferenceResult,RunState} from '../types/options';
import {apiUrl} from './base';
async function request<T>(path:string,method='GET'):Promise<T> {
  const response=await fetch(apiUrl(path),{method,cache:'no-store'});
  const data=await response.json();
  if(!response.ok) throw new Error(currentError(data.error?.code||'network',data.error?.message));
  return data;
}
export const capabilities=()=>request<{live_enabled:boolean}>('/api/runtime');
export const startRun=(id:string)=>request<RunState>(`/api/scopes/${encodeURIComponent(id)}/run`,'POST');
export const runStatus=(id:string)=>request<RunState>(`/api/scopes/${encodeURIComponent(id)}/run`);
export const checkReferences=(ref:Reference)=>request<ReferenceResult>(`/api/${ref.kind==='example'?'examples':'scopes'}/${encodeURIComponent(ref.id)}/references`,'POST');
