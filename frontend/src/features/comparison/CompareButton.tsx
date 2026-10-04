type Props = {kind:'scope'|'example';hasReport:boolean;enabled:boolean;busy:boolean;
  hasJob:boolean;running:boolean;checking:boolean;onClick:()=>void};
export function CompareButton(props:Props) {
  const needsJudge=props.kind==='scope'&&!props.hasReport;
  const disabled=props.busy||(needsJudge&&(!props.enabled||props.hasJob&&!props.running));
  return <button className="primary" disabled={disabled} onClick={props.onClick}>
    {props.running?'Сравнение выполняется…':props.checking?'Проверяю источники…':
      needsJudge?'Сравнить':'Показать сравнение'}
  </button>;
}
