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
test('rubric table shows a grade in every cell, a total and a winner',()=>{
  const side=(score)=>({score,status:'assessed',explanation_en:'Reason',explanation_ru:'Причина',
    evidence:[{id:'x',source_quote:'المصدر',translation_quote:'Translation',kind:'defect',verified:true,explanation_en:'Why',explanation_ru:'Почему так'}]});
  const result={version:'rubric-v1',winner:'b',totals:{a:2.5,b:4},unique_defects:{a:3,b:0},
    criteria:[{criterion:'accuracy',a:side(2),b:side(4)},{criterion:'terminology',a:side(3),b:side(4)},
      {criterion:'apparatus',a:{...side(null),status:'not_applicable',evidence:[]},b:{...side(null),status:'not_applicable',evidence:[]}}]};
  const ru=show('RubricTable',{result});
  assert.ok(ru.includes('Лучше перевод B'));
  assert.ok(ru.includes('2 / 5') && ru.includes('4 / 5'));
  assert.ok(ru.includes('Итог') && ru.includes('2,5 / 5') && ru.includes('4,0 / 5'));
  assert.ok(ru.includes('Ошибки с цитатами: A — 3; B — 0'));
  assert.ok(ru.includes('المصدر') && ru.includes('Почему так'));
  for(const word of ['Неустойчиво','Не оценено','Проходы','Unstable']) assert.ok(!ru.includes(word));
  assert.ok(!ru.includes('<details open'));
  const en=show('RubricTable',{result:{...result,winner:'tie',totals:{a:3,b:3}}},'en');
  assert.ok(en.includes('The translations are equal') && en.includes('3.0 / 5'));
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
test('official hadith evidence retains scholar attribution and unknown access',()=>{
  const record={text:'Arabic text',english_text:'English text',grade:'Scholar: Sahih',
    url:'https://sunnah.com/bukhari:13',snapshot_sha256:'a'.repeat(64),retrieved_at:'2026-10-05'};
  const html=show('HadithEvidence',{result:{status:'checked',detection:'marked',items:[],official:{status:'checked',records:[
    {quote:'Quotation',candidate_id:'bukhari:13',status:'review',record}]}}});
  assert.ok(html.includes('Scholar: Sahih'));
  assert.ok(html.includes('Есть расхождения'));
  assert.ok(html.includes('https://sunnah.com/bukhari:13'));
  const missing=show('HadithEvidence',{result:null});
  assert.ok(missing.includes('Не сверено'));
});
