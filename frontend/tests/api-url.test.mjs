import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {createRequire} from 'node:module';
const require=createRequire(import.meta.url);
require('./render.cjs');
test('the public build reaches the API and reports under its base path',()=>{
  process.env.NEXT_PUBLIC_BASE_PATH='/judge';
  const {apiUrl}=require('../src/shared/api/base.ts');
  assert.equal(apiUrl('/api/examples'),'/judge/api/examples');
  const {reportUrl}=require('../src/shared/api/comparison.ts');
  assert.equal(reportUrl({kind:'example',id:'x'}),'/judge/api/examples/x/report.html');
  delete process.env.NEXT_PUBLIC_BASE_PATH;
  assert.equal(apiUrl('/api/examples'),'/api/examples');
});
test('every API client sends requests through apiUrl',()=>{
  for(const name of ['comparison','runs','pipeline','editorial']){
    const source=fs.readFileSync(new URL(`../src/shared/api/${name}.ts`,import.meta.url),'utf8');
    assert.ok(source.includes("from './base'"),name);
    assert.ok(!/fetch\((?!apiUrl\()/.test(source),name);
  }
});
