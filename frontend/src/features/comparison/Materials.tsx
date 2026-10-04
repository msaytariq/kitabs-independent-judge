import type {Role} from '../../shared/types/comparison';
const names = {source:'Оригинал',a:'Перевод A',b:'Перевод B'};
export function Materials({texts,open=false}:{texts:Record<Role,string>;open?:boolean}) {
  return <details className="panel materials" open={open}>
    <summary>Оригинал и два перевода — целиком</summary>
    <p className="muted">Развернутые тексты показаны полностью, без скрытой внутренней прокрутки.</p>
    <div className="material-grid">{(['source','a','b'] as const).map(role=><section key={role}>
      <h3>{names[role]}</h3><pre dir="auto">{texts[role]}</pre>
      <p className="text-end">Конец {role==='source'?'оригинала':`перевода ${role.toUpperCase()}`}</p>
    </section>)}</div>
  </details>;
}
