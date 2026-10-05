"use client";
import {useJudgeLocale} from './JudgeLocale';
type Props = {kind:'scope'|'example';hasReport:boolean;enabled:boolean;busy:boolean;
  hasJob:boolean;running:boolean;checking:boolean;onClick:()=>void};
export function CompareButton(props:Props) {
  const {t}=useJudgeLocale();
  const needsJudge=props.kind==='scope'&&!props.hasReport;
  const disabled=props.busy||(needsJudge&&(!props.enabled||props.hasJob&&!props.running));
  return <button className="primary" disabled={disabled} onClick={props.onClick}>
    {props.running?t('Comparing…','Сравнение выполняется…'):props.checking?t('Checking sources…','Проверяю источники…'):
      needsJudge?t('Compare','Сравнить'):t('Show comparison','Показать сравнение')}
  </button>;
}
