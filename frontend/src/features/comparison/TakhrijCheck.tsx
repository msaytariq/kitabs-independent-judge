"use client";
import type {TakhrijCheck as Check,TakhrijItem} from '../../shared/types/rubric';
import {useJudgeLocale} from './JudgeLocale';
const ORDER:TakhrijItem['status'][]=['wrong','missing','as_in_source','unchecked','correct'];
const HADITH:TakhrijItem['kind'][]=['hadith','collection'];
// Takhrij is about hadith; verse references are a separate check with the same statuses.
export function TakhrijCheck({check}:{check?:Check|null}) {
  const {t}=useJudgeLocale();
  if(!check) return null;
  const labels:Record<TakhrijItem['status'],string>={wrong:t('Wrong','Неверно'),missing:t('Missing','Нет в переводе'),
    as_in_source:t('As in the source; the library has a different text under this number','Как в оригинале; в библиотеке под этим номером другой текст'),
    unchecked:t('Not checked: the code cannot open this reference','Не проверено: код не может открыть эту ссылку'),
    correct:t('Correct','Верно')};
  const side=(key:'a'|'b',kinds:TakhrijItem['kind'][])=><div key={key}><h3>{t('Translation','Перевод')} {key.toUpperCase()}</h3>
    {ORDER.map(status=>{const items=check[key].items.filter(i=>i.status===status&&kinds.includes(i.kind));
      if(!items.length) return null;
      const list=<ul>{items.map(i=><li key={i.kind+i.reference}>{i.reference}</li>)}</ul>;
      return status==='correct'?<details key={status}><summary>{labels[status]}: {items.length}</summary>{list}</details>
        :<div key={status}><p><strong>{labels[status]}: {items.length}</strong></p>{list}</div>;})}
  </div>;
  const hasHadith=['a','b'].some(k=>check[k as 'a'|'b'].items.some(i=>HADITH.includes(i.kind)));
  const hasVerses=['a','b'].some(k=>check[k as 'a'|'b'].items.some(i=>i.kind==='quran'));
  return <>
    {hasHadith&&<section className="panel"><h2>{t('Hadith takhrij check','Проверка тахриджа хадисов')}</h2>
      <p>{t('The code reads each hadith collection and hadith number in A and B and compares it with the source. It opens each hadith number in the library and compares the hadith text with the source. No model takes part.',
        'Код читает в A и B каждый сборник и номер хадиса и сверяет его с оригиналом. Номер хадиса код открывает в библиотеке и сравнивает текст хадиса с оригиналом. Модель не участвует.')}</p>
      <div className="takhrij-sides">{side('a',HADITH)}{side('b',HADITH)}</div>
      <p className="muted">{t('A hadith reference is wrong when the hadith under that number is not in the source. A collection that the source does not name is correct only when the library finds a hadith of the source in it.',
        'Ссылка на хадис неверна, если хадиса под этим номером нет в оригинале. Сборник, которого оригинал не называет, верен, только если библиотека находит в нём хадис оригинала.')}</p>
    </section>}
    {hasVerses&&<section className="panel"><h2>{t('Verse reference check','Проверка ссылок на аяты')}</h2>
      <p>{t('The code reads each surah and verse number in A and B and compares it with the verses that the source quotes. No model takes part.',
        'Код читает в A и B каждый номер суры и аята и сверяет его с аятами, которые цитирует оригинал. Модель не участвует.')}</p>
      <div className="takhrij-sides">{side('a',['quran'])}{side('b',['quran'])}</div>
      <p className="muted">{t('A verse reference is wrong when the source does not quote that verse.','Ссылка на аят неверна, если оригинал не цитирует этот аят.')}</p>
    </section>}
  </>;
}
