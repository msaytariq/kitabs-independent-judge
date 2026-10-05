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
test('paired table shows uncertainty and source evidence without a composite grade',()=>{
  const s={score:null,status:'unstable',pass_scores:[2,4],coverage:['partial','partial'],
    explanations:[],evidence:[{id:'x',source_quote:'المصدر',translation_quote:'Translation',kind:'defect',
      verified:true,explanation_en:'Reason',explanation_ru:'Причина',pass:1}]};
  const html=show('PairedTable',{result:{advantage:'none',criteria:[{criterion:'accuracy',a:s,b:s}],unique_defects:{a:1,b:1}}});
  assert.ok(html.includes('Неустойчиво'));
  assert.ok(html.includes('المصدر') && html.includes('Причина'));
  assert.ok(!html.includes('70%') && !html.includes('100'));
  assert.ok(!html.includes('<details open'));
  const conflict=show('PairedTable',{result:{advantage:'none',criteria:[{criterion:'accuracy',a:{...s,pass_scores:[2,2],evidence_conflict:true},b:s}],unique_defects:{a:0,b:1}}},'en');
  assert.ok(conflict.includes('The passes reached opposite conclusions on the same quotation.'));
  const unlocated=show('PairedTable',{result:{advantage:'none',criteria:[{criterion:'accuracy',a:{...s,pass_scores:[5,5],instability:'evidence_not_located'},b:s}],unique_defects:{a:0,b:0}}},'en');
  assert.ok(unlocated.includes('One pass cited a quotation that is not in the text.'));
  const changed=show('PairedTable',{result:{advantage:'none',criteria:[{criterion:'accuracy',a:{...s,instability:'score_changed'},b:s}],unique_defects:{a:0,b:0}}});
  assert.ok(changed.includes('Оценка изменилась после перестановки A и B.'));
});
test('unknown chat time and applied edits are separate in both locales',()=>{
  const unknown={pipeline_seconds:null,audit_operations:null,editor_operations:null,simulated_seconds:null,total_seconds:null,operations:[]};
  const b={pipeline_seconds:40,audit_operations:1,editor_operations:1,simulated_seconds:10,total_seconds:50,
    operations:[{stage:'audit',edit_id:'e',chunk_id:'c',before:'was',after:'is'}]};
  const effort={sides:{a:unknown,b}};
  for(const [locale,label] of [['ru','Время не установлено'],['en','Time not established']]) {
    const html=show('ProcessingTime',{effort},locale);
    assert.ok(html.includes(label));
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
