"use client";
import {assetUrl} from '../../shared/api/base';
import {LanguageSwitch,useJudgeLocale} from './JudgeLocale';
// The Kitabs.ai wordmark is language-neutral; the site link and the contact are the same for every locale.
export function JudgeHeader(){
  const {t}=useJudgeLocale();
  return <header className="judge-header">
    <div className="brand">
      <img className="judge-logo" src={assetUrl('/kitabs-logo.png')} alt="Kitabs.ai" width={154} height={28}/>
      <span className="judge-name">{t('Independent Judge','Независимый судья')}<small>{t('TRANSLATION COMPARISON','СРАВНЕНИЕ ПЕРЕВОДОВ')}</small></span>
    </div>
    <div className="judge-contacts">
      <a href="https://kitabs.ai">https://kitabs.ai</a>
      <a className="contact-email" href="mailto:m.sayfuddin@kitabs.ai">m.sayfuddin@kitabs.ai</a>
      <LanguageSwitch/>
    </div>
  </header>;
}
