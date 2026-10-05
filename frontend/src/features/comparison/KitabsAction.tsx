"use client";
import type {PipelineSource,PipelineState} from '../../shared/api/pipeline';
import {usePipelineB} from './usePipelineB';
import {useJudgeLocale} from './JudgeLocale';
export function LaunchesLeft({remaining}:{remaining:number|null}){
  const {t}=useJudgeLocale();
  if(remaining===null) return null;
  return <p className="muted">{remaining>0?t(`${remaining} of the demonstration launches remain.`,`Осталось запусков для демонстрации: ${remaining}.`)
    :t('All demonstration launches are used. You can upload any completed B.','Все запуски для демонстрации использованы. Можно загрузить любой готовый B.')}</p>;
}
export function KitabsAction({source,onReady,busy}:{source:PipelineSource;onReady:(job:PipelineState)=>void;busy:boolean}){
  const {t}=useJudgeLocale();const work=usePipelineB(onReady);
  const states:Record<string,string>={queued:t('Queued','В очереди'),uploading:t('Uploading','Загрузка'),creating:t('Creating job','Создание задания'),
    running:t('Autopilot is running','Автопилот работает'),completed:t('B is ready','B готов'),failed:t('Processing stopped','Обработка остановлена'),
    uncertain:t('Response uncertain. The same job will be checked; no new paid start.','Ответ не получен. Проверяется то же задание; повторного платного запуска нет.')};
  return <details className="kitabs-action" open><summary>{t('Process B on Kitabs.ai','Обработать B на Kitabs.ai')}</summary>
    <p>{t('Autopilot returns B here. Edits are accepted automatically. You can close this page.','Автопилот вернёт B сюда. Правки принимаются автоматически. Страницу можно закрыть.')}</p>
    {!work.enabled&&<p>{t('The operator has not enabled the pipeline connection. You can upload any completed B.','Подключение пайплайна не включено оператором. Можно загрузить любой готовый B.')}</p>}
    <LaunchesLeft remaining={work.remaining}/>
    {!work.requestId&&<button type="button" className="primary" disabled={busy||!work.enabled||work.running||work.remaining===0}
      onClick={()=>void work.start(source)}>{t('Start processing on Kitabs.ai (Autopilot)','Старт обработки на Kitabs.ai (автопилот)')}</button>}
    {work.job&&<p role="status">{states[work.job.status]||work.job.status} · {work.job.job_id||work.job.id}</p>}
    {work.error&&<p role="alert">{work.error==='pipeline_limit_reached'?t('All demonstration launches are used.','Все запуски для демонстрации использованы.'):work.error==='scope_too_large'?t('Source exceeds 18,000 characters.','Оригинал превышает 18 000 знаков.'):t('The request needs attention. Check the source and operator connection; no automatic paid retry.','Запрос требует проверки. Проверьте оригинал и подключение; автоматического платного повтора нет.')}</p>}
    {work.requestId&&!work.running&&<button type="button" onClick={work.clear}>{t('Use a new request','Использовать новый запрос')}</button>}
  </details>;
}
