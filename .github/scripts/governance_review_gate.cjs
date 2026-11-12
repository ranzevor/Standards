'use strict';
const fs = require('node:fs');

const DECISIONS = new Set(['APPROVED', 'CHANGES_REQUESTED', 'DISMISSED']);
const ELIGIBLE = new Set(['OWNER', 'MEMBER', 'COLLABORATOR']);
const SENSITIVE = /^(?:\.github\/|governance\/|checks\/|registry\/|releases\/current\.json$|tools\/(?:publish_release|verify_release|build_release_bundle|install_skill)\.py$|tests\/test_(?:governance_gate|release_publication)\.py$)/u;

function reviewErrors(pr, reviews, files) {
  if (!pr || !pr.head || typeof pr.head.sha !== 'string'
      || !pr.user || typeof pr.user.login !== 'string'
      || !Array.isArray(reviews) || !Array.isArray(files)
      || files.length < 1 || files.some(file => !file || typeof file.filename !== 'string')) {
    return ['PR 审查输入缺少当前 HEAD、作者、完整变更或实际审查记录'];
  }
  const current = new Map();
  for (const review of [...reviews].sort((a, b) => a.id - b.id)) {
    if (!review || !review.user || typeof review.user.login !== 'string'
        || !Number.isSafeInteger(review.id) || !DECISIONS.has(review.state)) continue;
    current.set(review.user.login.toLowerCase(), review);
  }
  const errors = [];
  const blocking = [...current.values()].filter(row => row.state === 'CHANGES_REQUESTED');
  if (blocking.length) {
    errors.push('存在未解除的 CHANGES_REQUESTED 审查：'
      + blocking.map(row => row.user.login).join('、'));
  }
  const author = pr.user.login.toLowerCase();
  const approvals = [...current.values()].filter(review =>
    review.state === 'APPROVED'
    && review.commit_id === pr.head.sha
    && review.user.login.toLowerCase() !== author
    && review.user.type === 'User'
    && ELIGIBLE.has(review.author_association));
  const sensitive = files.some(row => SENSITIVE.test(row.filename));
  const needed = sensitive ? 2 : 1;
  if (approvals.length < needed) {
    errors.push('当前 PR HEAD 需要 ' + needed + ' 个不同的有效非作者批准，实际只有 '
      + approvals.length + ' 个；旧提交、作者自审、机器人评论及无资格审查不计入');
  }
  return errors;
}
function headers(token) {
  return {
    Accept: 'application/vnd.github+json',
    'X-GitHub-Api-Version': '2022-11-28',
    Authorization: 'Bearer ' + token
  };
}
async function get(path, token) {
  const response = await fetch('https://api.github.com' + path, {headers: headers(token)});
  if (!response.ok) throw new Error('GitHub API 返回 ' + response.status + '：' + path);
  return response.json();
}
async function list(path, token) {
  const all = [];
  for (let page = 1; page <= 11; page++) {
    const response = await fetch('https://api.github.com' + path
      + '?per_page=100&page=' + page, {headers: headers(token)});
    if (!response.ok) throw new Error('GitHub API 返回 ' + response.status + '：' + path);
    const rows = await response.json();
    if (!Array.isArray(rows)) throw new Error('GitHub API 未返回完整列表：' + path);
    all.push(...rows);
    if (rows.length < 100) return all;
  }
  throw new Error('审查或变更文件超出可完整读取的范围，拒绝合并');
}
async function main() {
  const event = JSON.parse(fs.readFileSync(process.env.GITHUB_EVENT_PATH, 'utf8'));
  const repo = event.repository && event.repository.full_name;
  const incoming = event.pull_request;
  const token = process.env.GITHUB_TOKEN;
  if (!token || typeof repo !== 'string'
      || !/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/u.test(repo)
      || !incoming || !Number.isSafeInteger(incoming.number) || incoming.number < 1
      || !incoming.head || typeof incoming.head.sha !== 'string') {
    throw new Error('缺少有效的 PR 事件、仓库身份或只读权限');
  }
  const path = '/repos/' + repo + '/pulls/' + incoming.number;
  const live = await get(path, token);
  if (live.head.sha !== incoming.head.sha) {
    throw new Error('PR HEAD 与事件不一致，拒绝使用过时审查结果');
  }
  const [reviews, files] = await Promise.all([
    list(path + '/reviews', token), list(path + '/files', token)
  ]);
  const latest = await get(path, token);
  if (latest.head.sha !== live.head.sha
      || latest.base.ref !== live.base.ref
      || latest.base.sha !== live.base.sha) {
    throw new Error('审查期间 PR 候选或目标基线改变');
  }
  const errors = reviewErrors(latest, reviews, files);
  for (const error of errors) console.error('FAIL: ' + error);
  if (errors.length) process.exitCode = 1;
  else console.log('PASS: 当前 HEAD 具备必要独立审查且无未解除拒绝意见');
}

module.exports = {reviewErrors};
if (require.main === module) main().catch(error => {
  console.error('FAIL: ' + error.message);
  process.exitCode = 1;
});
