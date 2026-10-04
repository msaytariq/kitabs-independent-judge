import type {ComparisonView, Draft, Example, Inputs, Reference, Scope, Role} from '../types/comparison';
import {fullRanges} from '../utils/textRanges.mjs';
import {intakeErrors} from '../i18n/intake';
async function request<T>(path: string, body?: unknown): Promise<T> {
  const form = body instanceof FormData;
  const response = await fetch(path, {method: body === undefined ? 'GET' : 'POST', cache:'no-store',
    headers: body === undefined || form ? {} : {'Content-Type':'application/json'},
    body: body === undefined ? undefined : form ? body : JSON.stringify(body)});
  let data;
  try { data = await response.json(); }
  catch { throw new Error('Локальный сервер недоступен. Материалы на экране сохранены.'); }
  if (!response.ok) throw new Error(intakeErrors[data.error?.code] || data.error?.message || 'Не удалось обработать материалы. Проверьте формат файлов и заполнение полей.');
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
