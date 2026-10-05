import type {ComparisonView, Draft, Example, Inputs, Reference, Scope, Role, InputMethod} from '../types/comparison';
import {fullRanges} from '../utils/textRanges.mjs';
import {currentError} from '../i18n/intake';
async function request<T>(path: string, body?: unknown): Promise<T> {
  const form = body instanceof FormData;
  const response = await fetch(path, {method: body === undefined ? 'GET' : 'POST', cache:'no-store',
    headers: body === undefined || form ? {} : {'Content-Type':'application/json'},
    body: body === undefined ? undefined : form ? body : JSON.stringify(body)});
  let data;
  try { data = await response.json(); }
  catch { throw new Error(currentError('network')); }
  if (!response.ok) throw new Error(currentError(data.error?.code||'request_failed',data.error?.message));
  return data;
}
export const listExamples = () => request<Example[]>('/api/examples');
export const loadComparison = (ref:Reference) => request<ComparisonView>(ref.kind === 'example'
  ? `/api/examples/${encodeURIComponent(ref.id)}` : `/api/scopes/${encodeURIComponent(ref.id)}/comparison`);
export const reportUrl = (ref:Reference) => ref.kind === 'example'
  ? `/api/examples/${encodeURIComponent(ref.id)}/report.html` : `/api/scopes/${encodeURIComponent(ref.id)}/report.html`;
export const pasteInputs = (inputs:Inputs) => request<Draft>('/api/comparisons/text', inputs);
export const uploadInputs = (files:Record<Role,File>, source:string, target:string) => {
  const form = new FormData();
  for (const role of ['source','a','b'] as const) form.append(role,files[role]);
  form.append('source_language', source); form.append('target_language',target);
  return request<Draft>('/api/comparisons',form);
};
export const prepareComparison = (draft:Draft, profile:string) => request<Scope & {id:string}>(
  `/api/comparisons/${draft.id}/scopes`, {ranges:fullRanges(draft.materials),profile,confirmed:true});

export const mixedInputs = (inputs:Inputs, files:Partial<Record<Role,File>>, methods:Record<Role,InputMethod>) => {
  const form=new FormData();
  for(const role of ['source','a','b'] as const){
    form.append(role+'_kind',methods[role]); form.append(role+'_value',inputs[role]);
    if(methods[role]==='file'&&files[role])form.append(role,files[role]!);
  }
  form.append('source_language',inputs.source_language);form.append('target_language',inputs.target_language);
  return request<Draft>('/api/comparisons/mixed',form);
};
