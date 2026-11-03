'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const gate=require('../.github/scripts/governance_gate.cjs');
const body="## 背景与目标\n需要阻断不合规范的变更入口。\n## 变更范围与实现\n添加提交主题和 PR 元数据验证，且验证源为准确的提交对象。\n## 兼容性与风险\n不改变产品功能；尚需配置必需检查才能阻断合并。\n## 实际验证\n完成了符合要求与违规请求的本地正反例测试。\n## 未完成事项\n尚需核对远端检查来源并配置有效的 GitHub 规则。";
const commit="feat(governance): 新增提交和PR元数据的规则校验\n\n针对提交与PR的格式和说明不足增加严格检查。\n验证合规中文主题、缺失范围与控制字符反例，保留既有业务功能。";
test('合法中文主题及技术标识混用',()=>{
  assert.deepEqual(gate.titleErrors('fix(references): 核实⑨的官方出处与早期站内用例'),[]);
  assert.deepEqual(gate.titleErrors('fix(api): 修正 API 鉴权失败后的响应状态'),[]);
});
test('拒绝纯英文、无scope、空泛中文和不可见字符',()=>{
  for(const title of ['fix(api): fix login error','fix: 修复用户验证状态错误','fix(api): 优化代码','fix(api): 修复鉴权\u200b状态转移错误'])
    assert.notEqual(gate.titleErrors(title).length,0,title);
});
test('重要提交缺正文以及不兼容说明缺失',()=>{
  assert.deepEqual(gate.commitErrors(commit),[]);
  assert.notEqual(gate.commitErrors('feat(auth): 新增账户权限校验流程').length,0);
  assert.notEqual(gate.commitErrors('feat(api)!: 调整客户端消息契约\n\n调整旧版客户端的协议读取行为并要求迁移。').length,0);
});
test('PR 正文必须包含实质章节',()=>{
  assert.deepEqual(gate.prBodyErrors(body),[]);
  assert.notEqual(gate.prBodyErrors('## 背景与目标\n修复问题').length,0);
});
test('PR 分支和 HEAD 一致性',()=>{
  assert.deepEqual(gate.branchErrors('feat/governance-pr-metadata-gate'),[]);
  assert.notEqual(gate.branchErrors('my-work').length,0);
  const issues=gate.prErrors({title:'fix(api): 修正 API 鉴权失败后的响应状态',body,head:{ref:'fix/api-response',sha:'def'}},[{sha:'abc',commit:{message:commit}}],[{filename:'src/api.py'}]);
  assert(issues.some(x=>x.includes('HEAD')));
});


test('模板占位及代码围栏、HTML 注释伪章节不得充当 PR 实际验证',()=>{
  const sample="## 背景与目标\n需要阻断不合规范的变更入口。\n## 变更范围与实现\n添加提交主题和 PR 元数据验证，且验证源为准确的提交对象。\n## 兼容性与风险\n不改变产品功能；尚需配置必需检查才能阻断合并。\n## 实际验证\n完成了符合要求与违规请求的本地正反例测试。\n## 未完成事项\n尚需核对远端检查来源并配置有效的 GitHub 规则。";
  assert.deepEqual(gate.prBodyErrors(sample),[]);
  assert(gate.prBodyErrors(sample.replace("需要阻断不合规范的变更入口。","TODO: 补充本次具体网页行为目标。")).some(x=>x.includes('占位')));
  assert(gate.prBodyErrors(sample.replace("## 实际验证","```md\n## 实际验证\n```\n## 运行情况")).some(x=>x.includes('实际验证')));
  assert(gate.prBodyErrors(sample.replace("## 实际验证","<!--\n## 实际验证\n-->\n## 运行情况")).some(x=>x.includes('实际验证')));
});


test('精确中文行为词不受有限动词白名单误拦截',()=>{
  assert.deepEqual(gate.titleErrors('fix(governance): 将治理文件逐项纳入项目文件安全白名单'),[]);
  assert.deepEqual(gate.titleErrors('fix(governance): 复用既有PR矩阵完成无令牌提交核验'),[]);
  assert.deepEqual(gate.titleErrors('fix(governance): 核对提交元数据与当前交付边界'),[]);
});

test('当前官方 PR 模板完整填写合法且空字段或占位不允许通过',()=>{
  const template=fs.readFileSync(path.join(__dirname,'..','.github','pull_request_template.md'),'utf8');
  const values=[
    '按照本次治理审查结论修正已定位的五项实现缺陷。',
    '目标为 main 分支，基线和候选分别与当前审查的提交绑定。',
    '仅修改治理元数据检查及隔离回归，不修改产品业务规则。',
    '核对提交消息、真实差异、测试用例和现有入口依赖。',
    '旧模板继续兼容，新增校验不调整现有运行服务和数据结构。',
    '解析失败阻断，修改后的候选重新运行检查且保留已有成果。',
    'Node 回归与合成接口测试均使用隔离输入，输出符合预期。',
    '之前识别出模板不兼容，加入合法原模板作为修复回归。',
    '远端规则暂未调整，新增工作流仍需实际触发验证。',
    '原始输出保留于独立验证环境和关联 CI 检查。',
    '作者自查限定于本次治理检查器和测试文件的准确差异。',
    '独立审查尚未再次进行，审查缺陷需要新候选复核。',
    '所有引入的代码和测试均使用当前仓库已有技术来源。',
    '未引入凭据、个人数据或不相关项目的审查记录。',
    '该候选仅修复实现缺陷，不代表已完成远端强制配置。',
    '合并前重验准确 HEAD、validate 和 verify，检查审查阻断项。'
  ];
  let used=0;
  const filled=template.replace(/^(- [^\n]+[：:])\s*$/gmu,(_,field)=>field+' '+values[used++]);
  assert.equal(used,values.length,'官方模板字段数量发生变更');
  assert.deepEqual(gate.prBodyErrors(filled),[]);
  const empty=filled.replace(values[15],'');
  assert(gate.prBodyErrors(empty).some(e=>e.includes('合并前需重新确认的目标 HEAD')));
  const unfilled=filled.replace(values[0],'TODO: 本段稍后填写');
  assert(gate.prBodyErrors(unfilled).some(e=>e.includes('需求/条款ID及准确版本')));
});

test('不可见 HTML 注释及占位内容不能充当有效提交正文',()=>{
  const heading='fix(governance): 拒绝被隐藏的提交正文内容';
  assert(gate.commitErrors(heading+'\n\n<!-- 这是全部隐藏的提交说明，正常阅读界面完全不可见。 -->')
    .some(e=>e.includes('有效正文')));
  assert(gate.commitErrors(heading+'\n\n正常变更已经写明了具体范围和实际影响，并记录检查结果。\nTODO: 后补')
    .some(e=>e.includes('占位')));
});

test('标题、提交正文及PR正文拒绝不可见Unicode并允许常规换行',()=>{
  const heading='fix(governance): 校验提交标题的字符可见性';
  for(const mark of ['\u00a0','\u034f','\u200b']){
    assert(gate.titleErrors(heading.replace('标题','标'+mark+'题'))
      .some(e=>e.includes('Unicode')),'标题不可见字符 '+mark.codePointAt(0));
    assert(gate.commitErrors(heading+'\n\n提交说明包含完整的验证信息和可回溯的具体影响。'+mark)
      .some(e=>e.includes('Unicode')),'提交正文不可见字符 '+mark.codePointAt(0));
    assert(gate.prBodyErrors(body.replace('需要阻断','需要'+mark+'阻断'))
      .some(e=>e.includes('Unicode')),'PR正文不可见字符 '+mark.codePointAt(0));
  }
  assert.deepEqual(gate.prBodyErrors(body.replace(/\n/gu,'\r\n')),[]);
});

test('破坏性变更说明需明确契约、影响及迁移而非笼统短句',()=>{
  const heading='feat(api)!: 变更旧版客户端的协议请求方式';
  const explanation='旧版客户端接入时必须按新的接口协议字段进行处理，否则会出现不兼容响应。';
  assert(gate.commitErrors(heading+'\n\n'+explanation+'\nBREAKING CHANGE: 变化')
    .some(e=>e.includes('契约、影响和迁移')));
  assert(gate.commitErrors(heading+'\n\n'+explanation+'\nBREAKING CHANGE: 请求协议调整了字段名称和请求方式，对旧版客户端将产生不兼容影响。')
    .some(e=>e.includes('契约、影响和迁移')));
  const good=heading+'\n\n'+explanation+
    '\nBREAKING CHANGE: 请求接口不再接受旧版客户端的 legacyToken 字段，旧版调用会失败；客户端必须迁移到 Authorization 请求头并升级接入配置。';
  assert.deepEqual(gate.commitErrors(good),[]);
});
