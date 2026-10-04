"use client";
import {useState} from 'react';
import type {Finding} from '../../shared/types/comparison';
const labels:Record<string,string> = {K:'Критическое замечание',T:'Терминология',A:'Научный аппарат',S:'Стиль','?':'Категория спорная'};
export function Findings({findings}:{findings:Finding[]}) {
  const [filter,setFilter] = useState('all');
  const visible = findings.filter(f=>filter==='all'||f.side===filter||(filter==='disputed'&&f.status==='disputed'));
  return <section className="panel findings">
    <h2>Что именно предлагает проверить судья</h2>
    <p className="muted">Русские пояснения подготовлены Codex по сохранённым ответам. Это не заключение независимого эксперта.</p>
    <div className="tabs filter-tabs">{[['all','Все'],['a','Перевод A'],['b','Перевод B'],['disputed','Спорные']].map(([id,label])=><button key={id} className={filter===id?'selected':''} aria-pressed={filter===id} onClick={()=>setFilter(id)}>{label}</button>)}</div>
    {visible.length===0&&<p>В этой группе нет находок. Это не подтверждение безошибочности перевода.</p>}
    {visible.map(f=><article className="finding" key={f.id}>
      <div className="finding-heading"><h3>Перевод {f.side.toUpperCase()} · {labels[f.code]}</h3>
      <span className={`status ${f.status==='disputed'?'status-warn':''}`}>{f.status==='disputed'?'Спорное':f.status==='unlocated'?'Цитата не подтверждена':'Требует проверки'}</span></div>
      <p>{f.why_ru||'Русского пояснения пока нет; сохранённый ответ приведён ниже.'}</p>
      {f.review_note_ru&&<p className="notice">{f.review_note_ru}</p>}
      <div className="quote-grid"><div><span className="quote-label">В оригинале</span><blockquote dir="auto">{f.source_excerpt}</blockquote></div>
      <div><span className="quote-label">В переводе {f.side.toUpperCase()}</span><blockquote dir="auto">{f.current_text}</blockquote></div></div>
      <details><summary>Ответ модели и точные места в текстах</summary><p lang="en">{f.why}</p>
      <p>Предложенная формулировка модели:</p><blockquote dir="auto">{f.should_be}</blockquote>
      <p className="muted">Смещения в знаках Unicode от начала выборки, с нуля; конец не включён. Найденная цитата доказывает место, но не верность замечания.</p>
      {Object.entries(f.anchors).map(([role,a])=><p key={role}>{role==='source'?'Оригинал':'Перевод'}: {a.ranges.length?a.ranges.map(r=>`${r.start}–${r.end}`).join(', '):'место не найдено'}{a.ranges.length>1?' — несколько совпадений':''}</p>)}
      {f.repeated&&<p>Повторяющееся замечание считается один раз.</p>}</details>
    </article>)}
  </section>;
}
