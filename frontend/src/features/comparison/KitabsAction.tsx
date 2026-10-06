"use client";
import type {PipelineSource,PipelineState} from '../../shared/api/pipeline';
import {intakeError} from '../../shared/i18n/intake';
import {usePipelineB} from './usePipelineB';
import {useJudgeLocale} from './JudgeLocale';
export function LaunchesLeft({remaining}:{remaining:number|null}){
  const {t}=useJudgeLocale();
  if(remaining===null) return null;
  return <p className="muted">{remaining>0?t(`${remaining} of the demonstration launches remain.`,`Осталось запусков для демонстрации: ${remaining}.`)
    :t('All demonstration launches are used. You can upload any completed B.','Все запуски для демонстрации использованы. Можно загрузить любой готовый B.')}</p>;
}
// Translation B made by the Kitabs.ai pipeline: one autopilot launch for the source on this screen.
export function KitabsAction({source,onReady,busy}:{source:PipelineSource;onReady:(job:PipelineState)=>void;busy:boolean}){
  const {t,locale}=useJudgeLocale();const work=usePipelineB(onReady);
  const states:Record<string,string>={queued:t('Queued','В очереди'),uploading:t('Uploading the source','Загрузка оригинала'),creating:t('Creating job','Создание задания'),
    running:t('Autopilot is running. You can close this page.','Автопилот работает. Страницу можно закрыть.'),completed:t('B is ready','B готов'),failed:t('Processing stopped','Обработка остановлена'),
    uncertain:t('Response uncertain. The same job will be checked; no new paid start.','Ответ не получен. Проверяется то же задание; повторного платного запуска нет.')};
  const noSource=source.method==='file'?!source.file:!source.value.trim();
  return <div className="kitabs-action">
    <p>{t('The Kitabs.ai pipeline translates the source: translator, audit, editor, proofreader, apparatus and assembly. Edits are accepted automatically, and B appears here.',
      'Пайплайн Kitabs.ai переводит оригинал: переводчик, аудит, редактор, корректор, научный аппарат и сборка. Правки принимаются автоматически, B появится здесь.')}</p>
    {!work.enabled&&<p>{t('The operator has not enabled the pipeline connection. You can upload any completed B.','Подключение пайплайна не включено оператором. Можно загрузить любой готовый B.')}</p>}
    <LaunchesLeft remaining={work.remaining}/>
    {!work.requestId&&<button type="button" className="primary" disabled={busy||noSource||!work.enabled||work.running||work.remaining===0}
      onClick={()=>void work.start(source)}>{t('Start the autopilot on Kitabs.ai','Запустить автопилот Kitabs.ai')}</button>}
    {!work.requestId&&noSource&&<p className="muted">{t('First add the Arabic source.','Сначала добавьте арабский оригинал.')}</p>}
    {work.job&&<p role="status">{states[work.job.status]||work.job.status} · {work.job.job_id||work.job.id}</p>}
    {work.error&&<p role="alert">{intakeError(work.error,work.detail,locale)}</p>}
    {work.requestId&&!work.running&&<button type="button" onClick={work.clear}>{t('Use a new request','Использовать новый запрос')}</button>}
  </div>;
}
