'use strict';
const test=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const cp=require('node:child_process');
const root=path.join(__dirname,'..');
const gate=path.join(root,'.github','scripts','governance_gate.cjs');
const mockSource="'use strict';\nconst mode=process.env.GOV_TEST_MODE;\nconst body=\"## 背景与目标\\n当前提交缺少元数据合规检查。\\n## 变更范围与实现\\n添加严格的中文提交标题和PR结构检查。\\n## 兼容性与风险\\n不影响业务代码；合并前仍然需要独立审查。\\n## 实际验证\\n已经执行符合规定和失败输入的合成正反例检查。\\n## 未完成事项\\n远端的规则与必需状态检查仍需配置和验证。\";\nconst validMessage=\"fix(api): 修正调用失败后的权限状态处理\\n\\n权限失败将终止本次请求，不再继续执行下游业务操作。\\n回归验证受保护路径、失败响应与已有正常流程，兼容当前请求契约。\";\nglobalThis.fetch=async function(url,opts){\nif(opts.headers.Authorization!=='Bearer synthetic-token') throw new Error('unexpected auth');\nconst path=new URL(url).pathname;\nif(mode==='api-fail') return {ok:false,status:403};\nif(path.endsWith('/pulls/9')){const readNo=(globalThis.govReadCount=(globalThis.govReadCount||0)+1);const edited=readNo>1;return {ok:true,json:async()=>({title:mode==='bad-title'||(mode==='title-edited'&&edited)?'fix(api): fix auth bug':'fix(api): 修正调用失败后的权限状态处理',body:mode==='body-edited'&&edited?body+' 编辑后改变正文的当前内容。':body,head:{sha:'abc',ref:'fix/api-state'},base:{ref:'main',sha:mode==='base-edited'&&edited?'main-base-new':mode==='base-stale'?'main-base-new':'main-base-old'}})};}\nif(path.endsWith('/pulls/9/commits')) return {ok:true,json:async()=>[{sha:'abc',commit:{message:mode==='bad-commit'?'fix(api): fix auth bug':validMessage}}]};\nif(path.endsWith('/pulls/9/files')) return {ok:true,json:async()=>mode==='no-files'?[]:[{filename:'src/api.ts'}]};\nreturn {ok:false,status:404};\n};";
const modes=[
  ['pass',0,'PASS:'],
  ['stale',1,'PR HEAD 已变化'],
  ['bad-title',1,'PR：'],
  ['bad-commit',1,'提交'],
  ['no-files',1,'PR 缺少可核验的非空差异'],
  ['title-edited',1,'PR 标题或正文在校验期间改变'],
  ['body-edited',1,'PR 标题或正文在校验期间改变'],
  ['base-edited',1,'PR HEAD 或目标基线在校验期间改变'],
  ['base-stale',1,'PR 目标分支在事件后改变'],
  ['api-fail',1,'GitHub API 返回 403']
];
test('读取 GitHub 实时 PR、完整提交列表并拒绝过时事件或无效响应',()=>{
  const work=fs.mkdtempSync(path.join(os.tmpdir(),'governance-check-'));
  try{
    const helper=path.join(work,'mock-api.cjs');
    const event=path.join(work,'event.json');
    fs.writeFileSync(helper,mockSource,{encoding:'utf8'});
    for(const [mode,expected,diagnostic] of modes){
      fs.writeFileSync(event,JSON.stringify({
        repository:{full_name:'ranzevor/Standards'},
        pull_request:{number:9,head:{sha:mode==='stale'?'old':'abc'},base:{ref:'main',sha:'main-base-old'}}
      }),{encoding:'utf8'});
      const result=cp.spawnSync(process.execPath,['--require',helper,gate,'pr'],{
        cwd:root,encoding:'utf8',timeout:15000,
        env:{...process.env,GOV_TEST_MODE:mode,GITHUB_EVENT_PATH:event,GITHUB_TOKEN:'synthetic-token'}
      });
      assert.equal(result.status,expected,mode+': '+result.stdout+result.stderr);
      assert.ok((result.stdout+result.stderr).includes(diagnostic),mode+': '+result.stdout+result.stderr);
    }
  }finally{
    fs.rmSync(work,{recursive:true,force:true});
  }
});

test('已安装的本地钩子只执行 Git 私有目录中的受信校验器',()=>{
  const work=fs.mkdtempSync(path.join(os.tmpdir(),'governance-hook-'));
  const run=(command,args)=>cp.spawnSync(command,args,{cwd:work,encoding:'utf8',timeout:15000});
  try{
    assert.equal(run('git',['init','-q']).status,0);
    const script=path.join(work,'.github','scripts');
    fs.mkdirSync(path.join(script,'vendor'),{recursive:true});
    fs.copyFileSync(gate,path.join(script,'governance_gate.cjs'));
    fs.copyFileSync(path.join(root,'.github','scripts','vendor','commonmark-0.29.2.min.cjs'),
      path.join(script,'vendor','commonmark-0.29.2.min.cjs'));
    const install=run(process.execPath,[path.join(root,'governance','install_commit_hook.cjs')]);
    assert.equal(install.status,0,install.stdout+install.stderr);
    const common=run('git',['rev-parse','--git-common-dir']).stdout.trim();
    const expected=path.resolve(work,common,'standards-hooks');
    const configured=run('git',['config','--local','--get','core.hooksPath']);
    assert.equal(configured.stdout.trim(),expected);
    for(const [key,value] of [['user.name','Test Maintainer'],['user.email','maintainer@example.test']]){
      assert.equal(run('git',['config',key,value]).status,0);
    }
    fs.writeFileSync(path.join(script,'governance_gate.cjs'),"process.exit(23);\n");
    fs.writeFileSync(path.join(script,'vendor','commonmark-0.29.2.min.cjs'),"process.exit(24);\n");
    const good='fix(governance): 拒绝在工作树执行未审查代码\n\n提交检查使用 Git 私有目录内经审查的脚本和依赖，不能通过修改工作树中的文件改变实际执行代码。';
    const valid=run('git',['-c','commit.gpgsign=false','commit','--allow-empty','-m',good]);
    assert.equal(valid.status,0,valid.stdout+valid.stderr);
    const invalid=run('git',['-c','commit.gpgsign=false','commit','--allow-empty','-m','fix(api): fix login error']);
    assert.notEqual(invalid.status,0,invalid.stdout+invalid.stderr);
    assert((invalid.stdout+invalid.stderr).includes('提交'),'钩子必须仍然执行校验');
  }finally{
    fs.rmSync(work,{recursive:true,force:true});
  }
});
