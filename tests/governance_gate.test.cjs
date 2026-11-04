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
    '依据现行治理规范，修复提交与 PR 元数据校验边界。',
    '目标分支为 main，限定治理校验器、模板和回归文件，不改产品。',
    '保留独立审查要求，修复 footer、正文与 Markdown 注释解析。',
    '不涉及业务 API 迁移；若检查异常则拒绝此次门禁通过。',
    '已执行正常输入和违规输入的本地正反例校验。',
    '远端必需检查尚未配置，实际拒绝违规合并仍未验收。',
    '作者已复核提交与变更，独立审查尚未完成。',
    '合并前须完成检查器复核、CI 通过与远端规则验收。'
  ];
  let used=0;
  const filled=template.replace(/^(- [^\n]+[：:])\s*$/gmu,(_,field)=>field+' '+values[used++]);
  assert.equal(used,values.length,'官方模板字段数量发生变更');
  assert.deepEqual(gate.prBodyErrors(filled),[]);
  const empty=filled.replace(values[7],'');
  assert(gate.prBodyErrors(empty).some(e=>e.includes('合并条件及未解决阻断项')));
  const unfilled=filled.replace(values[0],'TODO: 本段稍后填写');
  assert(gate.prBodyErrors(unfilled).some(e=>e.includes('变更目标与依据')));
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

test('不兼容说明要求有效正文与正确分隔的 footer',()=>{
  const heading='feat(api)!: 变更旧版客户端的协议请求方式';
  const explanation='旧版客户端接入时必须按新的接口协议字段进行处理，否则会出现不兼容响应。';
  assert(gate.commitErrors(heading+'\n\n'+explanation+'\nBREAKING CHANGE: 变化')
    .some(e=>e.includes('footer')));
  assert(gate.commitErrors(heading+'\n\n'+explanation+'\n\nBREAKING CHANGE: 变化')
    .some(e=>e.includes('契约、影响和迁移')));
  const good=heading+'\n\n'+explanation+
    '\n\nBREAKING CHANGE: 请求接口不再接受旧版客户端的 legacyToken 字段，旧版调用会失败；客户端必须迁移到 Authorization 请求头并升级接入配置。';
  assert.deepEqual(gate.commitErrors(good),[]);
});

test('无叹号的破坏性 footer 也需校验，兼容双 token 并隔离代码示例',()=>{
  const title='feat(api): 调整旧版客户端的请求鉴权方式';
  const bang='feat(api)!: 调整旧版客户端的请求鉴权方式';
  const body='调整旧版客户端的请求鉴权流程，明确成功响应的字段与错误返回条件。';
  const good='鉴权接口不再接受旧版客户端的 legacyToken 字段；旧版请求会失败，客户端必须迁移到 Authorization 请求头完成升级。';
  assert(gate.commitErrors(title+'\n\n'+body+'\n\nBREAKING CHANGE: 变化').some(e=>e.includes('契约、影响和迁移')));
  assert.deepEqual(gate.commitErrors(title+'\n\n'+body+'\n\nBREAKING-CHANGE: '+good),[]);
  assert.deepEqual(gate.commitErrors(bang+'\n\n'+body+'\n\nBREAKING CHANGE: '+good),[]);
  assert.deepEqual(gate.commitErrors(bang+'\n\n'+body+'\n\nBREAKING-CHANGE: '+good),[]);
  assert(gate.commitErrors(bang+'\n\n'+body+'\n\n```text\nBREAKING CHANGE: '+good+'\n```').some(e=>e.includes('契约、影响和迁移')));
  assert.deepEqual(gate.commitErrors(title+'\n\n'+body+'\n\n```text\nBREAKING CHANGE: 变化\n```'),[]);
});
test('Markdown 行内代码与强调不能隐藏明确的模板和提交占位',()=>{
  const title='fix(governance): 修正检查器对占位内容的识别';
  assert(gate.commitErrors(title+'\n\n**TODO: 等待补充具体实现范围和实际验证结果**').some(e=>e.includes('占位')));
  assert(gate.commitErrors(title+'\n\n`TODO: 等待补充具体实现范围和实际验证结果`').some(e=>e.includes('占位')));
  const template=fs.readFileSync(path.join(__dirname,'..','.github','pull_request_template.md'),'utf8');
  const filled=template.replace(/^(- [^\n]+[：:])\s*$/gmu,'$1 已明确本次实际变更范围及验证条件，且记录具体兼容影响。');
  assert.deepEqual(gate.prBodyErrors(filled),[]);
  for(const placeholder of ['`TODO: 等待补充明确需求和准确规范版本`','**TODO: 等待补充明确需求和准确规范版本**']){
    const broken=filled.replace('变更目标与依据： 已明确本次实际变更范围及验证条件，且记录具体兼容影响。','变更目标与依据： '+placeholder);
    assert(gate.prBodyErrors(broken).some(e=>e.includes('变更目标与依据')),placeholder);
  }
});
test('文件路径识别不可见字符且允许正常空格和中文路径',()=>{
  const pr={title:'fix(api): 修正 API 鉴权失败后的响应状态',body,head:{ref:'fix/api-response',sha:'same'}};
  const commits=[{sha:'same',commit:{message:commit}}];
  assert.deepEqual(gate.prErrors(pr,commits,[{filename:'docs/中文使用 说明.md'}]),[]);
  for(const mark of ['\u034f','\u00a0','\u200b']){
    const issues=gate.prErrors(pr,commits,[{filename:'src/字'+mark+'段.ts'}]);
    assert(issues.some(e=>e.includes('文件名')),mark.codePointAt(0));
  }
});
test('围栏代码内的 HTML 注释起始标记不得影响后续官方章节',()=>{
  const template=fs.readFileSync(path.join(__dirname,'..','.github','pull_request_template.md'),'utf8');
  const filled=template.replace(/^(- [^\n]+[：:])\s*$/gmu,'$1 已明确实际提交的具体处理范围、核验方法及兼容影响。');
  const inserted=filled.replace('## 规范、行为与影响','```html\n<!--\n```\n\n## 规范、行为与影响');
  assert.deepEqual(gate.prBodyErrors(inserted),[]);
  assert.deepEqual(gate.prBodyErrors(filled.replace('## 规范、行为与影响','~~~html\n<!--\n~~~\n\n## 规范、行为与影响')),[]);
});

test('多个标准 footer 连续排列时不得漏检破坏性变更',()=>{
  const title='feat(api): 调整旧版客户端的请求鉴权方式';
  const description='调整旧版客户端的请求鉴权流程，明确成功响应的字段与错误返回条件。';
  const prefix=title+'\n\n'+description+'\n\nRefs: #123\n';
  const good='鉴权接口不再接受旧版客户端的 legacyToken 字段，旧版请求会失败；客户端必须迁移到 Authorization 请求头完成升级。';
  assert(gate.commitErrors(prefix+'BREAKING CHANGE: 变化').some(e=>e.includes('契约、影响和迁移')));
  assert.deepEqual(gate.commitErrors(prefix+'BREAKING CHANGE: '+good),[]);
  assert.deepEqual(gate.commitErrors(prefix+'BREAKING-CHANGE: '+good),[]);
  assert(gate.commitErrors(title+'\n\n'+description+'\nBREAKING-CHANGE: 变化').some(e=>e.includes('footer')));
  assert.deepEqual(gate.commitErrors(title+'\n\n'+description+'\n\nRefs: #123'),[]);
  assert.deepEqual(gate.commitErrors(prefix+'~~~text\nBREAKING CHANGE: 变化\n~~~'),[]);
});

test('标题叹号允许由正文交代破坏性契约而无需重复尾注',()=>{
  const title='feat(api)!: 移除旧版客户端的访问凭据接口';
  const details='旧版客户端访问凭据接口已移除，继续请求将失败，必须迁移到 Authorization 请求头并升级客户端鉴权流程。';
  assert.deepEqual(gate.commitErrors(title+'\n\n'+details),[]);
  assert(gate.commitErrors(title+'\n\n旧版接口已移除，客户端使用方式发生变化。').some(e=>e.includes('契约、影响和迁移')));
});

test('普通提交 footer 不能代替功能性正文',()=>{
  const title='feat(api): 增加客户端的匿名请求处理模式';
  const refs='Refs: #123, #124, #125, #126, #127, #128, #129';
  assert(gate.commitErrors(title+'\n\n'+refs).some(e=>e.includes('有效正文')));
  assert.deepEqual(gate.commitErrors(title+'\n\n新增匿名请求模式，并明确未登录客户端对应的响应行为与访问控制边界。\n\n'+refs),[]);
});

test('行内代码及反斜线转义的注释标记不得隐藏后续章节',()=>{
  const template=fs.readFileSync(path.join(__dirname,'..','.github','pull_request_template.md'),'utf8');
  const filled=template.replace(/^(- [^\n]+[：:])\s*$/gmu,'$1 已明确当前变更的行为、兼容影响及实际验证结论。');
  for(const literal of ['`<!--`','\\<!--','``<!--``']){
    const inserted=filled.replace('## 规范、行为与影响','- 行内说明：'+literal+' 是示例文本，不应影响后面的章节。\n\n## 规范、行为与影响');
    assert.deepEqual(gate.prBodyErrors(inserted),[],literal);
  }
  const hidden=filled.replace('## 规范、行为与影响','<!-- 隐藏这一章\n## 规范、行为与影响');
  assert(gate.prBodyErrors(hidden).some(e=>e.includes('官方模板章节')));
});

test('旧版 PR 模板保留语义兼容，但不强制失败记录或原始制品路径',()=>{
  const legacy=[
    '## 目标、基线与候选',
    '- 需求/条款ID及准确版本：依照当前治理规则处理元数据变更。',
    '- 本次范围与明确不改范围：仅改校验器和测试，产品逻辑保持原样。',
    '## 规范、行为与影响',
    '- 正文、来源、依赖、示例与检查变更：修改元数据检查和相关回归逻辑。',
    '- 使用者可观察变化及兼容/迁移影响：不涉及产品接口迁移，违规提交将被拒绝。',
    '## 验证',
    '- 输入、环境、命令、退出码、预期/实际及证据：执行 Node 正反例回归，结果通过。',
    '- 未执行、部分执行或不适用范围及原因：远端强制准入尚未完成实际部署。',
    '## 审查与合并前置',
    '- 独立审查绑定的候选、范围和开放发现：当前待独立审查者复核源码修改。',
    '- 合并前需重新确认的目标 HEAD、必需检查和阻断项：需确认 CI 通过且阻断项闭合。'
  ].join('\n');
  assert.deepEqual(gate.prBodyErrors(legacy),[]);
  assert(gate.prBodyErrors(legacy.replace('执行 Node 正反例回归，结果通过。','TODO: 等待完成验证')).length>0);
});

test('缩进代码与行内注释字面量不能误删合法 PR 章节或字段',()=>{
  const template=fs.readFileSync(path.join(__dirname,'..','.github','pull_request_template.md'),'utf8');
  const description='已明确当前变更的具体范围、兼容影响及实际验证结果。';
  const filled=template.replace(/^(- [^\n]+[：:])\s*$/gmu,'$1 '+description);
  const literal=filled.replace('变更目标与依据： '+description,'变更目标与依据： 解释字面量 `<!--` 及其后的真实 PR 解析逻辑。');
  assert.deepEqual(gate.prBodyErrors(literal),[]);
  const indented=filled.replace('## 规范、行为与影响','独立段落说明 Markdown 的解析范围。\n\n    <!--\n\n## 规范、行为与影响');
  assert.deepEqual(gate.prBodyErrors(indented),[]);
  const hidden=filled.replace('## 规范、行为与影响','<!--\n## 规范、行为与影响\n-->');
  assert(gate.prBodyErrors(hidden).some(e=>e.includes('官方模板章节')));
});

test('完整的不兼容说明不依赖固定关键词，缺少实质说明仍拒绝',()=>{
  const title='feat(api)!: 移除旧版客户端的访问凭据接口';
  const complete='旧客户端继续以 legacyToken 字段发起请求将收到 401 响应，接入方必须将凭据放到 Authorization 请求头，之后按原方式继续访问。';
  assert.deepEqual(gate.commitErrors(title+'\n\n'+complete),[]);
  assert(gate.commitErrors(title+'\n\n旧版接口已移除，客户端使用方式发生变化。').some(e=>e.includes('契约、影响和迁移')));
  assert(gate.commitErrors(title+'\n\nTODO: 等待补充具体的行为影响与操作步骤。').some(e=>e.includes('占位')));
});

test('列表字段缩进续行的可见占位必须被拒绝',()=>{
  const template=fs.readFileSync(path.join(__dirname,'..','.github','pull_request_template.md'),'utf8');
  const detail='已明确当前变更的具体范围、兼容影响和真实执行结果。';
  const filled=template.replace(/^(- [^\n]+[：:])\s*$/gmu,'$1 '+detail);
  const field='变更目标与依据： '+detail;
  const visible=filled.replace(field,field+'\n\n    TODO: 等待补充实际变更范围、受影响用户及恢复条件');
  assert(gate.prBodyErrors(visible).some(e=>e.includes('占位')));
  assert(gate.prBodyErrors(visible).some(e=>e.includes('变更目标与依据')));
  const code=filled.replace(field,field+'\n\n      TODO: 此行是缩进代码的示例内容');
  assert.deepEqual(gate.prBodyErrors(code),[]);
});

test('围栏关闭后紧接的缩进代码不得开启 HTML 注释',()=>{
  const template=fs.readFileSync(path.join(__dirname,'..','.github','pull_request_template.md'),'utf8');
  const filled=template.replace(/^(- [^\n]+[：:])\s*$/gmu,
    '$1 已明确当前变更的具体范围、兼容影响和真实执行结果。');
  const fence='\x60\x60\x60html\n<code>example</code>\n\x60\x60\x60\n';
  const code=filled.replace('## 规范、行为与影响',fence+'    <!--\n\n## 规范、行为与影响');
  assert.deepEqual(gate.prBodyErrors(code),[]);
  const comment=filled.replace('## 规范、行为与影响',fence+'<!--\n\n## 规范、行为与影响');
  assert(gate.prBodyErrors(comment).some(e=>e.includes('官方模板章节')));
});
