"use client";
import {createContext,useContext,useEffect,useState} from 'react';
import {arabic} from '../../shared/i18n/ar';
export type Locale='en'|'ru'|'ar';
const Context=createContext<{locale:Locale;setLocale:(v:Locale)=>void}>({locale:'ru',setLocale:()=>{}});
export function JudgeLocale({children,initial='en'}:{children:React.ReactNode;initial?:Locale}) {
  const [locale,setLocale]=useState<Locale>(initial);
  useEffect(()=>{const saved=localStorage.getItem('judge-language');if(saved==='en'||saved==='ru'||saved==='ar')setLocale(saved);},[]);
  useEffect(()=>{document.documentElement.lang=locale;document.documentElement.dir=locale==='ar'?'rtl':'ltr';},[locale]);
  function change(value:Locale){setLocale(value);localStorage.setItem('judge-language',value);}
  return <Context.Provider value={{locale,setLocale:change}}>{children}</Context.Provider>;
}
export function useJudgeLocale(){const context=useContext(Context);return {...context,t:(en:string,ru:string)=>context.locale==='ru'?ru:context.locale==='ar'?arabic(en):en};}
export function LanguageSwitch(){const {locale,setLocale}=useJudgeLocale();return <div className="tabs language-switch" aria-label="Language / Язык">
  <button aria-pressed={locale==='en'} onClick={()=>setLocale('en')}>EN</button>
  <button aria-pressed={locale==='ru'} onClick={()=>setLocale('ru')}>RU</button>
  <button aria-pressed={locale==='ar'} onClick={()=>setLocale('ar')} lang="ar">عربي</button>
</div>;}
