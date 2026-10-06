"use client";
import {useJudgeLocale} from './JudgeLocale';
// Where each text of a saved example comes from: the jury reads it before the grades.
export function ExampleProvenance({description,provenance}:{description?:string|null;provenance?:Record<string,string>|null}) {
  const {t}=useJudgeLocale();
  if(!description&&!provenance?.a&&!provenance?.b) return null;
  return <div className="provenance">
    {description&&<p>{description}</p>}
    {provenance?.a&&<p className="muted">{t('Translation A','Перевод A')}: {provenance.a}</p>}
    {provenance?.b&&<p className="muted">{t('Translation B','Перевод B')}: {provenance.b}</p>}
  </div>;
}
