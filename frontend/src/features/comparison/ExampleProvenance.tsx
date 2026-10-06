"use client";
import type {LocalizedExampleText} from '../../shared/types/comparison';
import {useJudgeLocale} from './JudgeLocale';
type Props={description?:string|null;provenance?:Record<string,string>|null;localized?:Partial<Record<'ru'|'ar',LocalizedExampleText>>|null};
// Where each text of a saved example comes from: the jury reads it before the grades.
// The record carries the English text; a Russian or Arabic variant replaces it for that interface language.
export function ExampleProvenance({description,provenance,localized}:Props) {
  const {t,locale}=useJudgeLocale();
  const own=locale==='en'?undefined:localized?.[locale];
  const text=own?.description??description;
  const from=own?.provenance??provenance;
  if(!text&&!from?.a&&!from?.b) return null;
  return <div className="provenance">
    {text&&<p>{text}</p>}
    {from?.a&&<p className="muted">{t('Translation A','Перевод A')}: {from.a}</p>}
    {from?.b&&<p className="muted">{t('Translation B','Перевод B')}: {from.b}</p>}
  </div>;
}
