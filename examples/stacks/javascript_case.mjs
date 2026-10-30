import assert from 'node:assert/strict';
function quantity(value) {
  if (!Number.isSafeInteger(value) || value < 0) throw new TypeError('quantity');
  return value;
}
assert.equal(quantity(0), 0);
assert.equal(quantity(7), 7);
for (const value of [true, -1, 0.5, Number.MAX_SAFE_INTEGER + 1, null]) {
  assert.throws(() => quantity(value), TypeError);
}
function apply(states, result) {
  const current = states.get(result.id);
  if (!current || current.epoch !== result.epoch) return false;
  states.set(result.id, { ...current, value: result.value });
  return true;
}
const states = new Map([['a', { epoch: 2, value: 4 }], ['b', { epoch: 1, value: 9 }]]);
assert.equal(apply(states, { id: 'a', epoch: 1, value: 0 }), false);
assert.equal(states.get('a').value, 4);
assert.equal(apply(states, { id: 'a', epoch: 2, value: 5 }), true);
assert.equal(apply(states, { id: 'b', epoch: 1, value: 10 }), true);
console.log('javascript-contract-ok');
