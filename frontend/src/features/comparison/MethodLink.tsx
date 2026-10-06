"use client";
import {useJudgeLocale} from './JudgeLocale';
// The full method for the jury: the six criteria, each level 1-5, the code rows and the total.
const METHOD_URL='https://github.com/msaytariq/kitabs-independent-judge/blob/main/docs/rating-method.md';
export function MethodLink(){
  const {t}=useJudgeLocale();
  return <p className="method-link"><a href={METHOD_URL} target="_blank" rel="noreferrer">
    {t('Method: criteria, levels 1–5 and formulas','Методика: критерии, уровни 1–5 и формулы (на английском)')}</a></p>;
}
