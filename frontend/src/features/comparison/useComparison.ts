"use client";
import {currentError} from '../../shared/i18n/intake';
import {useEffect, useRef, useState} from 'react';
import {mixedInputs, listExamples, loadComparison, pasteInputs, uploadInputs, prepareComparison} from '../../shared/api/comparison';
import type {ComparisonView, Draft, Example, Inputs, Reference, Role, InputMethod} from '../../shared/types/comparison';
import {referenceFromHash} from './helpers.mjs';

export function useComparison() {
  const [examples,setExamples] = useState<Example[]>([]);
  const [view,setView] = useState<ComparisonView|null>(null);
  const [reference,setReference] = useState<Reference|null>(null);
  const [draft,setDraft] = useState<Draft|null>(null);
  const [busy,setBusy] = useState(false), [error,setError] = useState('');
  const generation = useRef(0);
  async function attempt<T>(operation:()=>Promise<T>):Promise<T|null> {
    const ticket = ++generation.current;
    setBusy(true); setError('');
    try { const result = await operation(); return ticket === generation.current ? result : null; }
    catch (e) { if (ticket === generation.current) setError(e instanceof Error ? e.message : currentError('request_failed')); return null; }
    finally { if (ticket === generation.current) setBusy(false); }
  }
  async function open(ref:Reference) {
    const next = await attempt(()=>loadComparison(ref));
    if (next) {setView(next); setReference(ref); setDraft(null); window.history.replaceState(null,'',`#${ref.kind}=${ref.id}`);}
  }
  useEffect(()=>{
    let active = true;
    void listExamples().then(async items=>{
      if (!active) return;
      setExamples(items);
      const ref = referenceFromHash(window.location.hash);
      if (ref?.kind === 'legacy') {window.location.replace(`/editorial/#${ref.id}`); return;}
      if (ref) await open(ref as Reference);
      else if (items[0]) await open({kind:'example',id:items[0].id});
    }).catch(()=>{if(active) setError(currentError('network'));});
    return ()=>{active=false;};
  },[]);
  async function intake(inputs:Inputs, files:Partial<Record<Role,File>>|null, methods?:Record<Role,InputMethod>) {
    const next = await attempt(()=>methods ? mixedInputs(inputs,files||{},methods) : files ? uploadInputs(files as Record<Role,File>,inputs.source_language,inputs.target_language) : pasteInputs(inputs));
    if (next) {setDraft(next); setView(null);setReference(null);}
  }
  async function prepare(profile:string) {
    if (!draft) return;
    const scope = await attempt(()=>prepareComparison(draft,profile));
    if(scope) await open({kind:'scope',id:scope.id});
  }
  function clearDraft() {setDraft(null);setError('');setView(null);setReference(null);window.history.replaceState(null,'',window.location.pathname);}
  return {examples,view,reference,draft,busy,error,open,intake,prepare,clearDraft};
}
