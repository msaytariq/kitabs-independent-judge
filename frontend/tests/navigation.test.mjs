import test from 'node:test';
import assert from 'node:assert/strict';
import {createRequire} from 'node:module';
import {initialMode} from '../src/features/comparison/helpers.mjs';
const require=createRequire(import.meta.url);
const {React,render}=require('./render.cjs');
function show(name,props,locale='en'){
  const {JudgeLocale}=require('../src/features/comparison/JudgeLocale.tsx');
  const Component=require(`../src/features/comparison/${name}.tsx`)[name];
  return render(React.createElement(JudgeLocale,{initial:locale},React.createElement(Component,props)));
}
const side=(score,quote)=>({score,status:'assessed',explanation_en:'Reason',explanation_ru:'Причина',
  evidence:quote?[{id:'e1',source_quote:'المصدر',translation_quote:quote,kind:'defect',verified:true,explanation_en:'Why so',explanation_ru:'Почему так'}]:[]});
const error={id:'c1',side:'a',category:'unit_omitted',verified:true,source_quote:'نص',translation_quote:'—',explanation_en:'Text is omitted',explanation_ru:'Пропуск'};
const rubric={version:'paired-rubric-v3',winner:'b',totals:{a:2,b:4},unique_defects:{a:3,b:0},
  criteria:[{criterion:'accuracy',a:side(2,'Wrong text'),b:side(4)}]};
const jury={version:'points-v1',winner:'b',totals:{a:36,b:94},rows:[
  {key:'accuracy',kind:'criterion',a:25,b:75,level:{a:2,b:4}},
  {key:'critical',kind:'critical',a:2,b:0,errors:{a:[error],b:[]}},
  {key:'quran',kind:'coverage',a:0,b:100,found:{a:0,b:17},total:17}]};
const summary={en:['Translation B is better: 94 against 36 points.'],ru:['Перевод B лучше: 94 против 36 баллов.'],ar:['الترجمة B أفضل: 94 مقابل 36 نقطة.']};
const second={agree:true,first:{model:'judge-one',totals:{a:36,b:94},winner:'b'},second:{model:'judge-two',totals:{a:71,b:100},winner:'b'},rows:[]};
const edition={rows:[{key:'typeset',a:null,b:'done'}],checks:{a:0,b:1},total:1,in_total:false,download:'/api/pipeline-b/x/typeset.pdf'};

test('the header shows the Kitabs.ai logo, the site link and the contact email',()=>{
  const html=show('JudgeHeader',{});
  assert.match(html,/<img[^>]+src="\/kitabs-logo\.png"[^>]+alt="Kitabs\.ai"/);
  assert.ok(html.includes('<a href="https://kitabs.ai">https://kitabs.ai</a>'));
  // The email is in regular weight, apart from the bold site link.
  assert.ok(html.includes('<a class="contact-email" href="mailto:m.sayfuddin@kitabs.ai">m.sayfuddin@kitabs.ai</a>'));
  assert.ok(html.includes('Independent Judge') && html.includes('عربي'));
  assert.ok(show('JudgeHeader',{},'ar').includes('المحكِّم المستقل'));
});

test('the page opens on the saved example unless the address names own materials',()=>{
  assert.equal(initialMode(''),'example');
  assert.equal(initialMode('#example=2-tarbiya'),'example');
  assert.equal(initialMode('#scope=abc123'),'own');
});

test('the verdict card gives the totals, the winner, critical errors, the second judge and the PDF',()=>{
  const html=show('VerdictCard',{jury,summary,second,edition});
  assert.ok(html.includes('Translation B is better'));
  assert.ok(html.includes('Total, 0–100') && html.includes('>36<') && html.includes('>94<'));
  assert.ok(html.includes('Critical errors') && html.includes('>2<') && html.includes('>0<'));
  assert.ok(html.includes('Second judge') && html.includes('>71<') && html.includes('>100<') && html.includes('Same winner: B'));
  assert.ok(html.includes('href="/api/pipeline-b/x/typeset.pdf"') && html.includes('Download the typeset book B (PDF)'));
  assert.ok(html.includes('Translation B is better: 94 against 36 points.'));
  const ar=show('VerdictCard',{jury,summary,second,edition},'ar');
  assert.ok(ar.includes('الترجمة B أفضل: 94 مقابل 36 نقطة.') && !ar.includes('Translation B is better'));
  const bare=show('VerdictCard',{jury:{...jury,rows:[jury.rows[0]]},summary:null,second:null,edition:null});
  assert.ok(!bare.includes('Critical errors') && !bare.includes('Second judge') && !bare.includes('typeset.pdf'));
});

test('the result opens with the verdict, then sections in a fixed order behind a section menu',()=>{
  const view={id:'x',rubric,jury,jury_summary:summary,second_judge:second,edition,
    case_study:{a:[{id:'d1',criterion:'accuracy',source_quote:'م',translation_quote:'t',explanation_en:'Bad',explanation_ru:'Плохо'}],b:[],kitabs_corrections:[]},
    summary:{source_chars:1800,source_pages:1,findings:[]},scope:{hashes:{source:'s'}},run:{id:'r',model:'m',code_sha:'abc'},hadith:null};
  const html=show('JuryResult',{view});
  assert.match(html,/<nav[^>]+aria-label="Result sections"/);
  const ids=[...html.matchAll(/<section[^>]+id="(result-[a-z]+)"/g)].map(m=>m[1]);
  assert.deepEqual(ids,['result-summary','result-scores','result-errors','result-sources','result-edition','result-method']);
  for(const id of ids) assert.ok(html.includes(`href="#${id}"`));
  for(const label of ['Result','Scores','Errors','Sources','Edition','Method']) assert.ok(html.includes(`>${label}</a>`));
  const order=['Translation B is better','Measure, points 0–100','Second judge: bias check','What the judge caught','Sources in the original','Readiness for publication','Method and provenance'];
  const at=order.map(text=>html.indexOf(text));
  assert.ok(at.every(i=>i>=0),JSON.stringify(at));
  assert.deepEqual([...at].sort((x,y)=>x-y),at);
  const plain=show('JuryResult',{view:{...view,case_study:null}});
  assert.ok(!plain.includes('id="result-errors"') && !plain.includes('href="#result-errors"'));
  assert.ok(show('JuryResult',{view},'ar').includes('أقسام النتيجة'));
});

test('the reasons open in a full-width row under the measure, not inside a narrow cell',()=>{
  const html=show('RubricTable',{result:rubric,jury});
  assert.ok(!/<td[^>]*>(?:(?!<\/td>).)*<details/s.test(html),'no details inside a table cell');
  assert.match(html,/<button[^>]+aria-expanded="false"[^>]+aria-controls="why-accuracy"[^>]*>Why<\/button>/);
  assert.match(html,/<tr[^>]+id="why-accuracy"[^>]+hidden=""/);
  assert.ok(html.includes('colSpan="3"') || html.includes('colspan="3"'));
  assert.ok(html.includes('Wrong text') && html.includes('Why so'));
  assert.match(html,/aria-controls="why-critical"[^>]*>Which errors<\/button>/);
  assert.ok(html.includes('Text is omitted'));
  assert.ok(!html.includes('aria-controls="why-quran"'));
  assert.match(html,/<td class="bad"><strong class="points">2<\/strong><\/td><td><strong class="points">0<\/strong><\/td>/);
  assert.match(html,/<tr class="total-row">/);
  assert.match(html,/<details class="table-notes"><summary>How to read the table<\/summary>/);
  assert.ok(html.indexOf('100 — no defects')>html.indexOf('How to read the table'));
  assert.ok(html.indexOf('In Kitabs.ai, a person corrects each critical error')<html.indexOf('How to read the table'));
});

test('the public screen opens on the Example tab with the Kitabs.ai header',()=>{
  const {JudgeScreen}=require('../src/features/comparison/JudgeScreen.tsx');
  const html=render(React.createElement(JudgeScreen));
  assert.ok(html.includes('kitabs-logo.png') && html.includes('mailto:m.sayfuddin@kitabs.ai'));
  assert.match(html,/<button[^>]*aria-pressed="true"[^>]*>Example<\/button>/);
  assert.ok(html.indexOf('>Example</button>')<html.indexOf('>Your materials</button>'));
  assert.ok(!html.includes('brand-mark'));
});

test('a select list draws its arrow away from the edge, on the left side in Arabic',async()=>{
  const {readFileSync}=await import('node:fs');
  const css=readFileSync(new URL('../src/features/comparison/comparison.css',import.meta.url),'utf8');
  assert.match(css,/\.comparison-screen select\{[^}]*appearance:none[^}]*padding-inline-end:44px[^}]*background-position:right 16px center/);
  assert.match(css,/:root\[dir=rtl\] \.comparison-screen select\{background-position:left 16px center\}/);
});

test('the score table and the method section link the full method on GitHub',()=>{
  const url='https://github.com/msaytariq/kitabs-independent-judge/blob/main/docs/rating-method.md';
  const link=new RegExp(`<a[^>]+href="${url.replace(/[.]/g,'\\.')}"[^>]*>Method: criteria, levels 1–5 and formulas</a>`);
  const table=show('RubricTable',{result:rubric,jury});
  assert.match(table,link);
  assert.ok(table.indexOf(url)<table.indexOf('How to read the table'),'the link is visible above the folded notes');
  const view={id:'x',rubric,jury,summary:{source_chars:1800,source_pages:1,findings:[]},scope:{hashes:{source:'s'}},run:{id:'r',model:'m',code_sha:'abc'},hadith:null};
  const method=show('JuryResult',{view}).split('id="result-method"')[1];
  assert.match(method,link);
  assert.ok(show('RubricTable',{result:rubric,jury},'ru').includes('Методика: критерии, уровни 1–5 и формулы (на английском)'));
  assert.ok(show('RubricTable',{result:rubric,jury},'ar').includes('المنهجية: المعايير والمستويات 1–5 والصيغ (بالإنجليزية)'));
});

test('under the table, a plain text tells how the total is made, with the numbers of this example',()=>{
  const plain={...jury,totals:{a:13,b:88}};
  const html=show('RubricTable',{result:rubric,jury:plain});
  const block=html.indexOf('How the total is made');
  assert.ok(block>0 && block<html.indexOf('Errors with quotations'),'the explanation is right under the table');
  assert.ok(block<html.indexOf('<details class="table-notes">'),'the explanation is not folded');
  assert.ok(html.includes('Total = the mean of all rows: A — 25 ÷ 2 = 13; B — 175 ÷ 2 = 88.'));
  assert.ok(html.includes('The higher total wins.') && html.includes('Critical errors and the second judge are not part of the total.'));
  assert.match(html,/Accuracy<br\/><small class="row-source">AI judge<\/small>/);
  assert.match(html,/Quran verses in the translation<br\/><small class="row-source">Count<\/small>/);
  assert.match(html,/Critical errors, count<br\/><small class="row-source">Not in the total<\/small>/);
  const ru=show('RubricTable',{result:rubric,jury:plain},'ru');
  assert.ok(ru.includes('Как получается итог') && ru.includes('Итог = среднее всех строк: A — 25 ÷ 2 = 13; B — 175 ÷ 2 = 88.') && ru.includes('ИИ-судья'));
  const ar=show('RubricTable',{result:rubric,jury:plain},'ar');
  assert.ok(ar.includes('كيف يُحسب المجموع') && ar.includes('المحكِّم الآلي') && ar.includes('يفوز المجموع الأعلى.'));
});
