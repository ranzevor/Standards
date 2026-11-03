'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
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
