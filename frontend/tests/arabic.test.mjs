import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
const {React,render}=require('./render.cjs');
const {AR,arabic}=require('../src/shared/i18n/ar.ts');
function sources(dir){return fs.readdirSync(dir,{withFileTypes:true}).flatMap(e=>e.isDirectory()?sources(path.join(dir,e.name)):/\.tsx?$/.test(e.name)?[path.join(dir,e.name)]:[]);}
test('every plain interface text has an Arabic translation',()=>{
  const missing=[];
  for(const file of sources(new URL('../src',import.meta.url).pathname)){
    const text=fs.readFileSync(file,'utf8');
    for(const m of text.matchAll(/\bt\(\s*'((?:\\.|[^'])*)'\s*,/g)){
      const key=m[1].replace(/\\'/g,"'");
      if(!(key in AR)) missing.push(key);
    }
  }
  assert.deepEqual(missing,[]);
});
test('texts with values keep their numbers in Arabic',()=>{
  assert.equal(arabic('level 4 of 5'),'المستوى 4 من 5');
  assert.equal(arabic('17 of 17'),'17 من 17');
  assert.equal(arabic('B saves 77% of the editing time'),'توفِّر B نسبة 77٪ من زمن التحرير');
  assert.equal(arabic('Same winner: tie'),'الفائز نفسه: تعادل');
  assert.equal(arabic('Translation A'),'الترجمة A');
  assert.equal(arabic('An unknown sentence'),'An unknown sentence');
});
test('the Arabic table shows Arabic labels and the Arabic summary',()=>{
  const {JudgeLocale}=require('../src/features/comparison/JudgeLocale.tsx');
  const {RubricTable}=require('../src/features/comparison/RubricTable.tsx');
  const side=(score)=>({score,status:'assessed',explanation_en:'Reason',explanation_ru:'Причина',evidence:[]});
  const result={version:'rubric-v1',winner:'b',totals:{a:2,b:4},unique_defects:{a:1,b:0},criteria:[{criterion:'accuracy',a:side(2),b:side(4)}]};
  const jury={version:'points-v1',winner:'b',totals:{a:25,b:75},rows:[{key:'accuracy',kind:'criterion',a:25,b:75,level:{a:2,b:4}}]};
  const summary={en:['Translation B is better: 75 against 25 points.'],ru:['Перевод B лучше'],ar:['الترجمة B أفضل: 75 مقابل 25 نقطة.']};
  const html=render(React.createElement(JudgeLocale,{initial:'ar'},React.createElement(RubricTable,{result,jury,summary})));
  assert.ok(html.includes('الترجمة B أفضل') && html.includes('الدقة') && html.includes('المستوى 2 من 5'));
  assert.ok(html.includes('الترجمة B أفضل: 75 مقابل 25 نقطة.') && !html.includes('Перевод'));
});
