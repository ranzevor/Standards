'use strict';
const test = require('node:test');
const assert = require('node:assert/strict');
const {reviewErrors} = require('../.github/scripts/governance_review_gate.cjs');

const sha = 'a'.repeat(40);
const pr = {head: {sha}, user: {login: 'author'}};
const ordinary = [{filename: 'src/runner.py'}];
const sensitive = [{filename: '.github/workflows/quality.yml'}];
function review(id, state, options = {}) {
  return {
    id, state, commit_id: sha,
    author_association: 'COLLABORATOR',
    user: {login: 'reviewer', type: 'User'}, ...options
  };
}
test('没有审查或只有评论的普通 PR 不能合并', () => {
  assert.match(reviewErrors(pr, [], ordinary)[0], /至少需要一个/u);
  assert.equal(reviewErrors(pr, [review(1, 'COMMENTED')], ordinary).length, 1);
});
test('普通变更需要当前 HEAD 的有效独立批准', () => {
  assert.deepEqual(reviewErrors(pr, [review(1, 'APPROVED')], ordinary), []);
  assert.equal(reviewErrors(pr, [review(1, 'APPROVED', {commit_id: 'b'.repeat(40)})], ordinary).length, 1);
});
test('治理和发行路径至少一票，且由所有者参与审批', () => {
  assert.match(reviewErrors(pr, [], sensitive)[0], /至少需要一个/u);
  assert.match(reviewErrors(pr, [review(1, 'APPROVED')], sensitive)[0], /所有者/u);
  const owner = review(2, 'APPROVED', {
    user: {login: 'ranzevor', type: 'User'}, author_association: 'OWNER'
  });
  assert.deepEqual(reviewErrors(pr, [owner], sensitive), []);
  assert.match(reviewErrors(pr, [], [{filename: 'releases/current.json'}])[0], /至少需要一个/u);
});
test('GitHub Actions Bot 创建 PR 后，唯一开发者可自行审查并批准', () => {
  const botPr = {head: {sha}, user: {login: 'github-actions[bot]', type: 'Bot'}};
  const ownerApproval = review(1, 'APPROVED', {
    user: {login: 'ranzevor', type: 'User'}, author_association: 'OWNER'
  });
  assert.deepEqual(reviewErrors(botPr, [ownerApproval], ordinary), []);
  assert.deepEqual(reviewErrors(botPr, [ownerApproval], sensitive), []);
  const selfAuthored = {head: {sha}, user: {login: 'ranzevor', type: 'User'}};
  assert.match(reviewErrors(selfAuthored, [ownerApproval], ordinary)[0], /PR 作者不能审批/u);
  assert.match(reviewErrors(selfAuthored, [ownerApproval], sensitive)[0], /PR 作者不能审批/u);
});
test('作者自审、机器人及无写入关联资格的意见不能替代批准', () => {
  const changes = [
    {user: {login: 'AUTHOR', type: 'User'}},
    {user: {login: 'reviewer', type: 'Bot'}},
    {author_association: 'CONTRIBUTOR'},
    {author_association: 'NONE'}
  ];
  for (const change of changes) {
    assert.equal(reviewErrors(pr, [review(1, 'APPROVED', change)], ordinary).length, 1);
  }
});
test('拒绝审查优先于其他人批准，解除后仍需要有效批准', () => {
  const rejected = review(2, 'CHANGES_REQUESTED', {user: {login: 'blocker', type: 'User'}});
  assert.match(reviewErrors(pr, [review(1, 'APPROVED'), rejected], ordinary)[0], /CHANGES_REQUESTED/u);
  assert.deepEqual(reviewErrors(pr, [rejected, review(3, 'APPROVED', {user: {login: 'blocker', type: 'User'}})], ordinary), []);
  assert.equal(reviewErrors(pr, [rejected, review(3, 'DISMISSED', {user: {login: 'blocker', type: 'User'}})], ordinary).length, 1);
});
test('旧批准不遮蔽后续拒绝或 HEAD 更新', () => {
  const rows = [review(3, 'COMMENTED'), review(1, 'APPROVED'), review(2, 'CHANGES_REQUESTED')];
  assert.equal(reviewErrors(pr, rows, ordinary).length, 2);
  const changed = {head: {sha: 'c'.repeat(40)}, user: {login: 'author'}};
  assert.equal(reviewErrors(changed, [review(1, 'APPROVED')], ordinary).length, 1);
});
test('审查输入缺失必须失败', () => {
  assert.equal(reviewErrors({}, [review(1, 'APPROVED')], ordinary).length, 1);
  assert.equal(reviewErrors(pr, null, ordinary).length, 1);
  assert.equal(reviewErrors(pr, [review(1, 'APPROVED')], []).length, 1);
});

test('无权限的公开评论者不能通过 CHANGES_REQUESTED 使合法 PR 永久阻断', () => {
  const outsider = review(2, 'CHANGES_REQUESTED', {
    user: {login: 'random-contributor', type: 'User'},
    author_association: 'CONTRIBUTOR'
  });
  assert.deepEqual(reviewErrors(pr, [review(1, 'APPROVED'), outsider], ordinary), []);
});
