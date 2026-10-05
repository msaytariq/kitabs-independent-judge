import test from 'node:test';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
const require = createRequire(import.meta.url);
const {React,render} = require('./render.cjs');
function component(name, props, locale='en') {
  const {JudgeLocale} = require('../src/features/comparison/JudgeLocale.tsx');
  const Component = require(`../src/features/comparison/${name}.tsx`)[name];
  return render(React.createElement(JudgeLocale,{initial:locale},React.createElement(Component,props)));
}
const side = total => ({total,accuracy:90,terminology:95,readability:90,apparatus:50,
  apparatus_correctness:null,excluded:0,finding_ids:[],inventory:{}});
const ratings = (a,b,winner) => ({sides:{a:side(a),b:side(b)},winner,version:'test'});

test('quality table permits A, B or tie without promotional conclusions',()=>{
  for(const [a,b,winner,label] of [[80,70,'a','Text A has the higher index'],[70,80,'b','Text B has the higher index'],[80,80,'tie','The displayed indices are equal']]) {
    const html=component('QualityTable',{ratings:ratings(a,b,winner)});
    assert.ok(html.includes(label));
    assert.ok(html.includes('Structural apparatus'));
    assert.ok(html.includes('Scientific correctness is not assessed'));
    assert.ok(!html.includes('KITABS wins'));
  }
});
test('missing assessment is not displayed as a zero or a tie',()=>{
  const html=component('QualityTable',{ratings:ratings(null,null,null)});
  assert.ok(html.includes('Not assessed'));
  assert.ok(!html.includes('indices are equal'));
});
test('Russian locale translates the complete quality table',()=>{
  const html=component('QualityTable',{ratings:ratings(80,70,'a')},'ru');
  assert.ok(html.includes('Точность'));
  assert.ok(html.includes('Структурный аппарат'));
  assert.ok(!html.includes('Structural apparatus'));
});
test('effort labels hypothesis and keeps unknown prior work separate',()=>{
  const s={prior_decisions:null,remaining_candidates:12,remaining_estimated_seconds:60,prior_estimated_seconds:null};
  const html=component('DecisionSummary',{effort:{sides:{a:s,b:s},seconds_per_decision:5}});
  assert.ok(html.includes('assuming 5 seconds per decision'));
  assert.ok(html.includes('60'));
  assert.ok(html.includes('Unknown'));
  assert.ok(!html.includes('<input'));
});
test('input parity and embedded KITABS launch appear without an external handoff',()=>{
  const html=component('OwnMaterials',{draft:null,busy:false,intake:()=>{},prepare:()=>{},clearDraft:()=>{}});
  assert.ok(html.includes('URL'));
  assert.ok(html.includes('Process B on Kitabs.ai') && html.includes('Start processing on Kitabs.ai'));
  assert.ok(!html.includes('https://app.kitabs.ai/workspace'));
  assert.ok(html.includes('Autopilot'));
  assert.ok(html.includes('18,000'));
  assert.ok(!html.includes('minutes'));
});

test('jury result keeps evidence and methodology collapsed and uses both languages',()=>{
  const s={prior_decisions:null,remaining_candidates:0,remaining_estimated_seconds:0};
  const view={id:'fixture',ratings:ratings(70,70,'tie'),decision_effort:{sides:{a:s,b:s}},
    summary:{measured:true,source_chars:1800,source_pages:1,findings:[]},scope:{hashes:{source:'s',a:'a',b:'b'}},
    run:{id:'run',model:'fixture',code_sha:'abc'},hadith:null};
  const html=component('JuryResult',{view});
  assert.ok(html.includes('Evidence and explanations'));
  assert.ok(!html.includes('<details open'));
  assert.ok(html.includes('Method and provenance'));
  assert.ok(!html.includes('Точность'));
  const failed=component('JuryResult',{view:{...view,rubric:null,rubric_protocol:true}});
  assert.ok(failed.includes('The assessment did not finish.'));
  assert.ok(!failed.includes('different protocol'));
  assert.ok(!failed.includes('reverse order'));
});

test('intake errors respect language and do not expose unsupported Russian server text in English',()=>{
  const {intakeError}=require('../src/shared/i18n/intake.ts');
  assert.match(intakeError('scope_too_large','', 'en'),/18,000/);
  assert.match(intakeError('private_url','', 'ru'),/локальн/);
  assert.ok(!/[А-Яа-я]/.test(intakeError('unexpected','Русский серверный текст','en')));
});
