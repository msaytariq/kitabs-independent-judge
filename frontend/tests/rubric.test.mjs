import test from 'node:test';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const {React,render}=require('./render.cjs');
function show(name, props, locale='ru') {
  const {JudgeLocale}=require('../src/features/comparison/JudgeLocale.tsx');
  const Component=require(`../src/features/comparison/${name}.tsx`)[name];
  return render(React.createElement(JudgeLocale,{initial:locale},React.createElement(Component,props)));
}
test('rubric table shows points 0-100 in every cell, a total, a winner and a legend',()=>{
  const side=(score)=>({score,status:'assessed',explanation_en:'Reason',explanation_ru:'Причина',
    evidence:[{id:'x',source_quote:'المصدر',translation_quote:'Translation',kind:'defect',verified:true,explanation_en:'Why',explanation_ru:'Почему так'}]});
  const result={version:'rubric-v1',winner:'b',totals:{a:2.5,b:4},unique_defects:{a:3,b:0},
    criteria:[{criterion:'accuracy',a:side(2),b:side(4)},{criterion:'terminology',a:side(3),b:side(4)},
      {criterion:'apparatus',a:{...side(null),status:'not_applicable',evidence:[]},b:{...side(null),status:'not_applicable',evidence:[]}}]};
  const jury={version:'points-v1',winner:'b',totals:{a:29,b:81},rows:[
    {key:'accuracy',kind:'criterion',a:25,b:75,level:{a:2,b:4}},{key:'terminology',kind:'criterion',a:50,b:75,level:{a:3,b:4}},
    {key:'apparatus',kind:'criterion',a:null,b:null,level:{a:null,b:null}},
    {key:'quran',kind:'coverage',a:0,b:100,found:{a:0,b:17},total:17},{key:'hadith',kind:'coverage',a:38,b:75,found:{a:3,b:6},total:8}]};
  const summary={en:['Translation B is better: 81 against 29 points.','B is better in: accuracy (+50).'],
    ru:['Перевод B лучше: 81 против 29 баллов.','B лучше в: точность (+50).']};
  const ru=show('RubricTable',{result,jury,summary});
  assert.ok(ru.includes('Лучше перевод B'));
  assert.ok(ru.includes('>25<') && ru.includes('>75<') && ru.includes('уровень 2 из 5'));
  assert.ok(ru.includes('Итог, 0–100') && ru.includes('>29<') && ru.includes('>81<'));
  assert.ok(ru.includes('Аяты Корана в переводе') && ru.includes('0 из 17') && ru.includes('17 из 17'));
  assert.ok(ru.includes('Хадисы в переводе') && ru.includes('3 из 8'));
  assert.ok(ru.includes('Перевод B лучше: 81 против 29 баллов.'));
  assert.ok(ru.includes('100 — замечаний нет'));
  assert.ok(ru.includes('Ошибки с цитатами: A — 3; B — 0'));
  assert.ok(ru.includes('المصدر') && ru.includes('Почему так'));
  for(const word of ['Неустойчиво','Не оценено','Проходы','Unstable','/ 5']) assert.ok(!ru.includes(word));
  assert.ok(!ru.includes('<details open'));
  const en=show('RubricTable',{result,jury:{...jury,winner:'tie',totals:{a:60,b:60}},summary},'en');
  assert.ok(en.includes('The translations are equal') && en.includes('Total, 0–100') && en.includes('level 2 of 5'));
  assert.ok(en.includes('0 of 17') && en.includes('100 — no defects') && en.includes('Translation B is better: 81 against 29 points.'));
});
test('remaining editing work shows edits, minutes, saving and the assumption',()=>{
  const effort={version:'effort-v1',minutes_per_edit:3,reduction_percent:81,
    a:{edits:9,defects:6,missing_quotations:3,review_minutes:0,minutes:27},
    b:{edits:1,defects:1,missing_quotations:0,review_minutes:2,minutes:5}};
  const ru=show('EffortReduction',{effort});
  assert.ok(ru.includes('Редактура до публикации') && ru.includes('Экономия времени с B: 81%'));
  assert.ok(ru.includes('>27<') && ru.includes('>5<') && ru.includes('3 минуты на одну правку'));
  const en=show('EffortReduction',{effort},'en');
  assert.ok(en.includes('Editing to publication') && en.includes('B saves 81% of the editing time'));
  assert.ok(en.includes('3 minutes for one edit'));
  const none=show('EffortReduction',{effort:{...effort,reduction_percent:null}},'en');
  assert.ok(!none.includes('saves'));
  assert.equal(show('EffortReduction',{effort:null},'en'),'');
});
test('unknown chat time and applied edits are separate in both locales',()=>{
  const unknown={pipeline_seconds:null,audit_operations:null,editor_operations:null,simulated_seconds:null,total_seconds:null,operations:[]};
  const b={pipeline_seconds:40,audit_operations:1,editor_operations:1,simulated_seconds:10,total_seconds:50,
    operations:[{stage:'audit',edit_id:'e',chunk_id:'c',before:'was',after:'is'}]};
  const effort={sides:{a:unknown,b}};
  for(const [locale,label] of [['ru','Время не установлено'],['en','Time not established']]) {
    const html=show('ProcessingTime',{effort},locale);
    assert.equal(html.split(label).length-1,1);
    assert.ok(html.includes('<del>was</del>') && html.includes('<ins>is</ins>'));
    assert.ok(html.includes('50'));
    const precise=show('ProcessingTime',{effort:{sides:{a:unknown,b:{...b,pipeline_seconds:116.042259,total_seconds:221.042259}}}},locale);
    assert.ok(precise.includes('>116<') && precise.includes('>221<') && !precise.includes('116.04'));
    assert.ok(!html.includes('remaining candidates'));
  }
});
test('source references show found counts, wrong labels and collections in both locales',()=>{
  const result={status:'checked',quran:{found:5,total:5,label_differs:1,items:[
      {quote:'استعينوا بالصبر والصلاة',status:'found',ayah:'2:153',surah_name:'البقرة',label:'محمد : 31',label_status:'label_differs',verse_text:'يا أيها الذين آمنوا استعينوا'}]},
    hadith:{found:20,total:20,by_collection:{'Sahih al-Bukhari':12,'Sahih Muslim':4},items:[
      {quote:'عجبا لأمر المؤمن',status:'fragment',candidate_count:1,candidates:[{id:'muslim:7500',collection:'Sahih Muslim',number:7500,
        text:'عجبا لأمر المؤمن',url:'https://example.org/7500',edition:'ara-muslim',retrieved_at:'2026-10-05',snapshot_sha256:'a'}]}]},official:{status:'requires_key',records:[]}};
  const ru=show('ReferenceEvidence',{result});
  assert.ok(ru.includes('Аяты Корана: найдено 5 из 5'));
  assert.ok(ru.includes('Хадисы: найдено 20 из 20'));
  assert.ok(ru.includes('Sahih al-Bukhari — 12'));
  assert.ok(ru.includes('Ошибка ссылки в оригинале: «محمد : 31», в Коране — 2:153'));
  assert.ok(!ru.includes('Sunnah.com'));
  const en=show('ReferenceEvidence',{result},'en');
  assert.ok(en.includes('Quran verses: 5 of 5 found') && en.includes('Hadith: 20 of 20 found'));
  assert.ok(show('ReferenceEvidence',{result:null}).includes('Сверка источников ещё не выполнена'));
});
