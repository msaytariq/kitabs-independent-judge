"use client";
import type {TakhrijCheck as Check,TakhrijItem} from '../../shared/types/rubric';
import {useJudgeLocale} from './JudgeLocale';
const ORDER:TakhrijItem['status'][]=['wrong','missing','as_in_source','unchecked','correct'];
export function TakhrijCheck({check}:{check?:Check|null}) {
  const {t}=useJudgeLocale();
  if(!check) return null;
  const labels:Record<TakhrijItem['status'],string>={wrong:t('Wrong','Неверно'),missing:t('Missing','Нет в переводе'),
    as_in_source:t('As in the source; the library has a different text under this number','Как в оригинале; в библиотеке под этим номером другой текст'),
    unchecked:t('Not checked: no open library has this collection','Не проверено: этого сборника нет в открытых библиотеках'),
    correct:t('Correct','Верно')};
  const side=(key:'a'|'b')=><div key={key}><h3>{t('Translation','Перевод')} {key.toUpperCase()}</h3>
    {ORDER.map(status=>{const items=check[key].items.filter(i=>i.status===status);
      if(!items.length) return null;
      const list=<ul>{items.map(i=><li key={i.kind+i.reference}>{i.reference}</li>)}</ul>;
      return status==='correct'?<details key={status}><summary>{labels[status]}: {items.length}</summary>{list}</details>
        :<div key={status}><p><strong>{labels[status]}: {items.length}</strong></p>{list}</div>;})}
  </div>;
  return <section className="panel"><h2>{t('Takhrij check','Проверка тахриджа')}</h2>
    <p>{t('The code reads each reference to a Quran verse or a hadith collection in A and B and compares it with the source. It opens each hadith number in the library and compares the hadith text with the source. No model takes part.',
      'Код читает в A и B каждую ссылку на аят или сборник хадисов и сверяет её с оригиналом. Номер хадиса код открывает в библиотеке и сравнивает текст хадиса с оригиналом. Модель не участвует.')}</p>
    <div className="takhrij-sides">{side('a')}{side('b')}</div>
    <p className="muted">{t('A reference is wrong when the source does not quote that verse, when the hadith under that number is not in the source, or when the source does not name that collection.',
      'Ссылка неверна, если оригинал не цитирует этот аят, если хадиса под этим номером нет в оригинале или если оригинал не называет этот сборник.')}</p>
  </section>;
}
