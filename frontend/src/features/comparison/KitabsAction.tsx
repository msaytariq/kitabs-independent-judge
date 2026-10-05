"use client";
import {useState} from 'react';
import {useJudgeLocale} from './JudgeLocale';
export function KitabsAction(){const {t}=useJudgeLocale();const [mode,setMode]=useState('autopilot');
  return <details className="kitabs-action"><summary>{t('Create B on KITABS','Получить B через KITABS')}</summary>
    <label>{t('Processing mode','Режим обработки')}<select value={mode} onChange={e=>setMode(e.target.value)}>
      <option value="autopilot">{t('Autopilot','Автопилот')}</option><option value="manual">{t('Manual review','Ручная проверка')}</option></select></label>
    <p>{t('In the platform tab, upload the same source and select','Во вкладке платформы загрузите тот же оригинал и выберите')} {mode==='autopilot'?t('Autopilot.','Автопилот.'):t('manual review.','ручную проверку.')}</p>
    <a className="button" href="https://app.kitabs.ai/workspace" target="_blank" rel="noreferrer">{t('Process on Kitabs.ai','Обработать на Kitabs.ai')} ↗</a>
    <p className="muted">{t('Review the price and start there. Return here and upload the completed result with its apparatus as B. This link does not start a paid job or transfer files.','Проверьте цену и запустите там. Вернитесь сюда и загрузите готовый результат с аппаратом как B. Ссылка не запускает платную работу и не передаёт файлы.')}</p>
  </details>;
}
