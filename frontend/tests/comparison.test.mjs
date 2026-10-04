import test from 'node:test';
import assert from 'node:assert/strict';
import { referenceFromHash, countLabel } from '../src/features/comparison/helpers.mjs';
import { fullRanges } from '../src/shared/utils/textRanges.mjs';

test('whole-input selections use Unicode code points and preserve hashes', () => {
  assert.deepEqual(fullRanges({source:{text:'أ😀ب',sha256:'original'}}),
    {source:{start:0,end:3,text_sha256:'original'}});
});
test('old review links are preserved and new selections restore the right screen', () => {
  assert.deepEqual(referenceFromHash('#example=pilot-v2'), {kind:'example',id:'pilot-v2'});
  assert.deepEqual(referenceFromHash('#scope=abc123'), {kind:'scope',id:'abc123'});
  assert.deepEqual(referenceFromHash('#25c238541399415c87973ff3a1c2326a'),
    {kind:'legacy',id:'25c238541399415c87973ff3a1c2326a'});
  assert.equal(referenceFromHash('#example=../../private'), null);
});
test('missing assessment never displays as zero errors', () => {
  assert.equal(countLabel(null), 'не оценено');
  assert.equal(countLabel(0), '0');
  assert.equal(countLabel(4), '4');
});
