import test from 'node:test';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const {React,render}=require('./render.cjs');
const {JudgeLocale}=require('../src/features/comparison/JudgeLocale.tsx');
const check={version:'takhrij-v1',total:3,
  a:{delivered:1,wrong:1,items:[{kind:'quran',reference:'Quran 30:21',status:'correct'},
    {kind:'quran',reference:'Quran 16:42',status:'wrong'},{kind:'hadith',reference:"Sunan an-Nasa'i 3053",status:'missing'},
    {kind:'collection',reference:'Sahih Muslim',status:'missing'}]},
  b:{delivered:3,wrong:0,items:[{kind:'quran',reference:'Quran 30:21',status:'correct'},
    {kind:'hadith',reference:"Sunan an-Nasa'i 3053",status:'as_in_source'},{kind:'collection',reference:'Sahih Muslim',status:'correct'}]}};
const page=(locale,element)=>render(React.createElement(JudgeLocale,{initial:locale},element));
test('the takhrij check lists wrong and missing references for each translation',()=>{
  const {TakhrijCheck}=require('../src/features/comparison/TakhrijCheck.tsx');
  const html=page('en',React.createElement(TakhrijCheck,{check}));
  // Hadith takhrij and verse references are two separate checks.
  assert.ok(html.includes('Hadith takhrij check') && html.includes('Verse reference check'));
  assert.ok(html.indexOf('Quran 16:42') > html.indexOf('Verse reference check'));
  assert.ok(html.indexOf('Sahih Muslim') < html.indexOf('Verse reference check'));
  assert.ok(html.includes('Quran 16:42') && html.includes('Wrong'));
  assert.ok(html.includes('Missing') && html.includes('Sahih Muslim'));
  assert.ok(html.includes('As in the source'));
  assert.equal(render(React.createElement(TakhrijCheck,{check:null})),'');
});
test('the takhrij row shows correct and wrong references',()=>{
  const {RubricTable}=require('../src/features/comparison/RubricTable.tsx');
  const result={version:'rubric-v1',winner:'b',totals:{a:2,b:4},unique_defects:{a:0,b:0},criteria:[]};
  const jury={version:'points-v1',winner:'b',totals:{a:0,b:100},rows:[{key:'takhrij',kind:'takhrij',a:0,b:100,
    delivered:{a:1,b:3},wrong:{a:1,b:0},total:3}]};
  const html=page('en',React.createElement(RubricTable,{result,jury}));
  assert.ok(html.includes('Hadith takhrij: collections and hadith numbers'));
  assert.ok(html.includes('1 of 3') && html.includes('wrong: 1'));
  const arabicHtml=page('ar',React.createElement(RubricTable,{result,jury}));
  assert.ok(arabicHtml.includes('خاطئة: 1'));
});
