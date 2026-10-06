"use client";
import type {ReferenceResult,HadithCandidate} from '../../shared/types/options';
import {useJudgeLocale} from './JudgeLocale';
export function ReferenceEvidence({result}:{result:ReferenceResult|null}) {
  const {t}=useJudgeLocale();
  if(!result||result.status!=='checked'||!result.quran||!result.hadith) return <section className="panel"><h2>{t('Sources in the original','Источники в оригинале')}</h2>
    <p>{result?.status==='unavailable'?t('The reference libraries are unavailable now. Try again later.','Справочные библиотеки сейчас недоступны. Повторите позже.'):t('The source check has not run yet.','Сверка источников ещё не выполнена.')}</p></section>;
  const {quran,hadith}=result;
  const collections=Object.entries(hadith.by_collection).map(([name,n])=>`${name} — ${n}`).join(', ');
  const wrong=quran.items.filter(i=>i.label_status==='label_differs');
  const states:Record<string,string>={exact:t('Exact match','Точное совпадение'),normalized:t('Match without diacritics','Совпадение без огласовок'),
    fragment:t('The quotation is part of the hadith','Цитата — часть хадиса'),ambiguous:t('Found in several collections','Найден в нескольких сборниках'),
    review:t('Close text with differences','Близкий текст с расхождениями'),not_found:t('Not in the connected collections','Нет в подключённых сборниках')};
  const record=(c:HadithCandidate)=><p key={c.id}><a href={c.url} target="_blank" rel="noreferrer">{c.collection} {c.number}</a></p>;
  return <section className="panel"><h2>{t('Sources in the original','Источники в оригинале')}</h2>
    <p><strong>{t(`Quran verses: ${quran.found} of ${quran.total} found`,`Аяты Корана: найдено ${quran.found} из ${quran.total}`)}</strong></p>
    {wrong.length>0&&<p className="muted">{t('The edition prints these references with an error. The code found each verse by its text and gives its real place in the Quran.',
      'Издание печатает эти ссылки с ошибкой. Код нашёл каждый аят по тексту и указывает его настоящее место в Коране.')}</p>}
    {wrong.map((i,n)=><p key={n} className="notice">{t(`Printed in the edition: "${i.label}" — in the Quran: ${i.ayah}`,`В издании напечатано: «${i.label}» — в Коране: ${i.ayah}`)}</p>)}
    <p><strong>{t(`Hadith: ${hadith.found} of ${hadith.total} found`,`Хадисы: найдено ${hadith.found} из ${hadith.total}`)}</strong>{collections&&<> · {collections}</>}</p>
    <details><summary>{t('Verses and hadith one by one','Аяты и хадисы по отдельности')}</summary>
      {quran.items.map((i,n)=><article key={`q${n}`}><blockquote dir="auto">{i.quote}</blockquote>
        <p>{i.status==='found'?<a href={`https://quran.com/${i.ayah?.split('-')[0].replace(':','/')}`} target="_blank" rel="noreferrer">{t('Quran','Коран')} {i.ayah} · {i.surah_name}</a>:t('Not found in the Quran text','Не найдено в тексте Корана')}</p></article>)}
      {hadith.items.map((i,n)=><article key={`h${n}`}><blockquote dir="auto">{i.quote}</blockquote><p>{states[i.status]||i.status}</p>{i.candidates.map(record)}</article>)}
      <p className="muted">{t('Texts: public Quran (simple script) and the Arabic editions of Bukhari, Muslim, Abu Dawud, Tirmidhi, Nasa\'i, Ibn Majah and Malik. A text match is not a ruling on authenticity.','Тексты: открытый текст Корана и арабские издания Бухари, Муслима, Абу Дауда, Тирмизи, Насаи, Ибн Маджи и Малика. Совпадение текста не является заключением о достоверности.')}</p>
    </details></section>;
}
