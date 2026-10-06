"use client";
import {useEffect,useRef,useState} from 'react';
import {useJudgeLocale} from './JudgeLocale';
export type ResultSection={id:string;label:string};
// The section menu stays at the top while the jury scrolls. The links scroll to the section and do not
// change the address: the address hash names the opened example (#example=...).
export function ResultNav({sections}:{sections:ResultSection[]}){
  const {t}=useJudgeLocale();
  const [current,setCurrent]=useState(sections[0]?.id);
  const list=useRef<HTMLUListElement>(null);
  const ids=sections.map(s=>s.id).join(' ');
  useEffect(()=>{
    let frame=0;
    const update=()=>{frame=0;
      const offset=(list.current?.getBoundingClientRect().bottom??0)+24;
      let found=sections[0]?.id;
      for(const s of sections){const el=document.getElementById(s.id);if(el&&el.getBoundingClientRect().top<=offset)found=s.id;}
      setCurrent(found);};
    const schedule=()=>{if(!frame)frame=requestAnimationFrame(update);};
    update();window.addEventListener('scroll',schedule,{passive:true});window.addEventListener('resize',schedule);
    return()=>{window.removeEventListener('scroll',schedule);window.removeEventListener('resize',schedule);if(frame)cancelAnimationFrame(frame);};
  },[ids]);
  // On a narrow screen the menu scrolls sideways: keep the current item in view.
  // Only while the whole menu is on the screen, so that the page itself does not move.
  useEffect(()=>{const ul=list.current;if(!ul||ul.scrollWidth<=ul.clientWidth)return;
    const box=ul.getBoundingClientRect();if(box.top<0||box.bottom>window.innerHeight)return;
    ul.querySelector<HTMLElement>('[aria-current]')?.scrollIntoView({block:'nearest',inline:'nearest'});},[current]);
  function go(event:React.MouseEvent,id:string){
    const el=document.getElementById(id);if(!el)return;
    event.preventDefault();
    const smooth=!window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    el.scrollIntoView({behavior:smooth?'smooth':'auto',block:'start'});
    el.focus({preventScroll:true});setCurrent(id);
  }
  return <nav className="result-nav" aria-label={t('Result sections','Разделы результата')}>
    <ul ref={list}>{sections.map(s=><li key={s.id}>
      <a href={`#${s.id}`} aria-current={current===s.id?'location':undefined} onClick={e=>go(e,s.id)}>{s.label}</a></li>)}</ul>
  </nav>;
}
