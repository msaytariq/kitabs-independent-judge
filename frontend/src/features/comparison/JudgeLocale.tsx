"use client";
import {createContext,useContext,useEffect,useState} from 'react';
export type Locale='en'|'ru';
const Context=createContext<{locale:Locale;setLocale:(v:Locale)=>void}>({locale:'ru',setLocale:()=>{}});
export function JudgeLocale({children,initial='en'}:{children:React.ReactNode;initial?:Locale}) {
  const [locale,setLocale]=useState<Locale>(initial);
  useEffect(()=>{const saved=localStorage.getItem('judge-language');if(saved==='en'||saved==='ru')setLocale(saved);},[]);
  useEffect(()=>{document.documentElement.lang=locale;},[locale]);
  function change(value:Locale){setLocale(value);localStorage.setItem('judge-language',value);}
  return <Context.Provider value={{locale,setLocale:change}}>{children}</Context.Provider>;
}
export function useJudgeLocale(){const context=useContext(Context);return {...context,t:(en:string,ru:string)=>context.locale==='en'?en:ru};}
export function LanguageSwitch(){const {locale,setLocale}=useJudgeLocale();return <div className="tabs language-switch" aria-label="Language / Язык">
  <button aria-pressed={locale==='en'} onClick={()=>setLocale('en')}>EN</button>
  <button aria-pressed={locale==='ru'} onClick={()=>setLocale('ru')}>RU</button>
</div>;}
