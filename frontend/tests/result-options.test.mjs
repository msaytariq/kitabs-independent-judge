import test from 'node:test';
import assert from 'node:assert/strict';
import {render} from './render-component.mjs';

test('forecast renders calculated percent, uncertainty and no time-entry controls',()=>{
  const html=render('../src/features/comparison/EffortSummary.tsx','EffortSummary',{effort:{
    reduction_percent:75,edit_reduction_percent:75,sensitivity_percent:[60,85],
    sides:{a:{edits:40,units:120,excluded:2},b:{edits:10,units:30,excluded:0}}}});
  assert.match(html,/75%/);
  assert.match(html,/Прогноз/);
  assert.match(html,/60.*85/);
  assert.doesNotMatch(html,/<input|<form|<select|<details open/);
});

test('missing assessment has no zero-percent savings claim',()=>{
  const html=render('../src/features/comparison/EffortSummary.tsx','EffortSummary',{effort:{
    reduction_percent:null,edit_reduction_percent:null,sensitivity_percent:null,
    sides:{a:{edits:null,units:null,excluded:0},b:{edits:null,units:null,excluded:0}}}});
  assert.match(html,/Недостаточно данных/);
  assert.doesNotMatch(html,/>0%/);
});

test('saved examples can be shown without enabling paid evaluation',()=>{
  const html=render('../src/features/comparison/CompareButton.tsx','CompareButton',{
    kind:'example',hasReport:false,enabled:false,busy:false,hasJob:false,running:false,checking:false,onClick:()=>{}});
  assert.doesNotMatch(html,/disabled/);
  assert.match(html,/Показать сравнение/);
});

test('new scopes require enabled judge and cannot repeat a terminal job',()=>{
  for(const [enabled,hasJob] of [[false,false],[true,true]]) {
    const html=render('../src/features/comparison/CompareButton.tsx','CompareButton',{
      kind:'scope',hasReport:false,enabled,busy:false,hasJob,running:false,checking:false,onClick:()=>{}});
    assert.match(html,/disabled/);
  }
});
