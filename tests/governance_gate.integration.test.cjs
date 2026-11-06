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
    const hooks=run('git',['rev-parse','--git-path','hooks']);
    assert.equal(hooks.status,0);
    const dir=path.resolve(work,hooks.stdout.trim());
    assert.equal(dir,path.join(work,'.git','hooks'));
    assert.equal(run('git',['config','--get','core.hooksPath']).status,1);
    assert.match(fs.readFileSync(path.join(dir,'commit-msg'),'utf8'),
      /standards-governance: managed commit-msg/u);
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

const validHookMessage='fix(governance): 修正已安装钩子的权限隔离规则\n\n提交检查只执行 Git 私有目录里的校验器，工作树变更不会覆盖现有提交检查或降低门禁强度。';
function hookFixture(){
  const work=fs.mkdtempSync(path.join(os.tmpdir(),'governance-hook-cases-'));
  const run=(command,args,cwd=work)=>cp.spawnSync(command,args,{cwd,encoding:'utf8',timeout:15000});
  assert.equal(run('git',['init','-q']).status,0);
  for(const [key,value] of [['user.name','Test Maintainer'],['user.email','maintainer@example.test']])
    assert.equal(run('git',['config',key,value]).status,0);
  const script=path.join(work,'.github','scripts');
  fs.mkdirSync(path.join(script,'vendor'),{recursive:true});
  fs.copyFileSync(gate,path.join(script,'governance_gate.cjs'));
  fs.copyFileSync(path.join(root,'.github','scripts','vendor','commonmark-0.29.2.min.cjs'),
    path.join(script,'vendor','commonmark-0.29.2.min.cjs'));
  const install=(cwd=work)=>run(process.execPath,[path.join(root,'governance','install_commit_hook.cjs')],cwd);
  const commit=(message=validHookMessage,cwd=work)=>
    run('git',['-c','commit.gpgsign=false','commit','--allow-empty','-m',message],cwd);
  return {work,run,script,install,commit,close:()=>fs.rmSync(work,{recursive:true,force:true})};
}

test('保留 Git 私有目录已有的非 commit-msg 钩子，且拒绝覆盖独立 commit-msg',()=>{
  const env=hookFixture();
  try{
    const hooks=path.join(env.work,'.git','hooks');
    const preCommit=path.join(hooks,'pre-commit');
    const prePush=path.join(hooks,'pre-push');
    fs.writeFileSync(preCommit,'#!/bin/sh\nexit 43\n',{mode:0o755});
    fs.writeFileSync(prePush,'#!/bin/sh\nexit 44\n',{mode:0o755});
    const result=env.install();
    assert.equal(result.status,0,result.stderr);
    assert.equal(env.run('git',['config','--get','core.hooksPath']).status,1);
    assert.equal(fs.readFileSync(prePush,'utf8'),'#!/bin/sh\nexit 44\n');
    const denied=env.commit();
    assert.notEqual(denied.status,0,'原有 pre-commit 必须继续拦截提交');
    fs.rmSync(preCommit);
    assert.equal(env.commit().status,0);
  }finally{env.close();}
  const conflict=hookFixture();
  try{
    const hook=path.join(conflict.work,'.git','hooks','commit-msg');
    fs.writeFileSync(hook,'#!/bin/sh\nexit 45\n',{mode:0o755});
    const result=conflict.install();
    assert.notEqual(result.status,0);
    assert.match(result.stderr,/独立 commit-msg/);
    assert.equal(fs.readFileSync(hook,'utf8'),'#!/bin/sh\nexit 45\n');
    assert.notEqual(conflict.commit().status,0);
  }finally{conflict.close();}
});

test('工作树旧钩子冲突时拒绝覆盖，审查迁移到 Git 私有路径后保留原门禁',()=>{
  const env=hookFixture();
  try{
    const legacy=path.join(env.work,'.githooks');
    fs.mkdirSync(legacy);
    fs.writeFileSync(path.join(legacy,'pre-commit'),'#!/bin/sh\nexit 46\n',{mode:0o755});
    assert.equal(env.run('git',['config','core.hooksPath','.githooks']).status,0);
    const refused=env.install();
    assert.notEqual(refused.status,0);
    assert.match(refused.stderr,/迁移/);
    assert.equal(env.run('git',['config','--get','core.hooksPath']).stdout.trim(),'.githooks');
    const privateHook=path.join(env.work,'.git','hooks','pre-commit');
    fs.renameSync(path.join(legacy,'pre-commit'),privateHook);
    assert.equal(env.run('git',['config','--unset','core.hooksPath']).status,0);
    assert.equal(env.install().status,0);
    assert.notEqual(env.commit().status,0,'迁移后的既有检查必须仍生效');
    fs.rmSync(privateHook);
    assert.equal(env.commit().status,0);
  }finally{env.close();}
});

test('工作树级 core.hooksPath 优先级和关联工作树安装后实际执行受信钩子',()=>{
  const env=hookFixture();
  const linked=path.join(env.work,'linked');
  try{
    fs.writeFileSync(path.join(env.work,'seed.txt'),'seed\n');
    assert.equal(env.run('git',['add','.github','seed.txt']).status,0);
    const first=env.run('git',['-c','commit.gpgsign=false','commit','-q','-m','test(governance): 创建关联工作树的测试基线']);
    assert.equal(first.status,0,first.stderr);
    const added=env.run('git',['worktree','add','-q','-b','test/worktree-config',linked]);
    assert.equal(added.status,0,added.stderr);
    assert.equal(env.run('git',['config','extensions.worktreeConfig','true']).status,0);
    assert.equal(env.run('git',['config','--worktree','core.hooksPath','.githooks'],linked).status,0);
    const installed=env.install(linked);
    assert.equal(installed.status,0,installed.stderr);
    const effective=env.run('git',['config','--get','core.hooksPath'],linked).stdout.trim();
    assert.ok(effective.startsWith(path.join(env.work,'.git','standards-hooks-')),effective);
    assert.equal(env.run('git',['config','--worktree','--get','core.hooksPath'],linked).stdout.trim(),effective);
    assert.equal(env.run('git',['config','--get','core.hooksPath']).status,1,'不覆盖主工作树配置');
    assert.equal(env.commit(validHookMessage,linked).status,0);
    fs.mkdirSync(path.join(linked,'.githooks'));
    fs.writeFileSync(path.join(linked,'.githooks','commit-msg'),'#!/bin/sh\nexit 47\n',{mode:0o755});
    assert.equal(env.commit(validHookMessage,linked).status,0,'不能重新执行工作树中的钩子');
    assert.notEqual(env.commit('fix(api): fix login bug',linked).status,0);
  }finally{
    if(fs.existsSync(linked)) env.run('git',['worktree','remove','--force',linked]);
    env.close();
  }
});

test('工作树现有 commit-msg 钩子不得在安装成功时被静默停用',()=>{
  const env=hookFixture();
  try{
    assert.equal(env.run('git',['config','extensions.worktreeConfig','true']).status,0);
    assert.equal(env.run('git',['config','--worktree','core.hooksPath','.githooks']).status,0);
    const legacy=path.join(env.work,'.githooks');
    fs.mkdirSync(legacy);
    fs.writeFileSync(path.join(legacy,'commit-msg'),'#!/bin/sh\nexit 48\n',{mode:0o755});
    const refused=env.install();
    assert.notEqual(refused.status,0);
    assert.equal(env.run('git',['config','--get','core.hooksPath']).stdout.trim(),'.githooks');
    fs.rmSync(path.join(legacy,'commit-msg'));
    const installed=env.install();
    assert.equal(installed.status,0,installed.stderr);
    assert.notEqual(env.run('git',['config','--get','core.hooksPath']).stdout.trim(),'.githooks');
    assert.equal(env.commit().status,0);
    assert.notEqual(env.commit('fix(api): fix login bug').status,0);
  }finally{env.close();}
});

test('重装失败不替换旧版校验器；下一次真实提交仍使用完整旧版',()=>{
  const env=hookFixture();
  try{
    assert.equal(env.install().status,0);
    assert.equal(env.commit().status,0);
    const hook=path.join(env.work,'.git','hooks','commit-msg');
    const previous=fs.readFileSync(hook,'utf8');
    fs.writeFileSync(path.join(env.script,'governance_gate.cjs'),'process.exit(49);\n');
    fs.rmSync(path.join(env.script,'vendor','commonmark-0.29.2.min.cjs'));
    const failed=env.install();
    assert.notEqual(failed.status,0);
    assert.equal(fs.readFileSync(hook,'utf8'),previous);
    assert.equal(env.commit().status,0,'失败重装后，旧版仍接受合法提交');
    assert.notEqual(env.commit('fix(api): fix login bug').status,0,'失败重装后，旧版仍拒绝违规提交');
  }finally{env.close();}
});

test('成功重装只在准备完整版本后更新已启用钩子',()=>{
  const env=hookFixture();
  try{
    assert.equal(env.install().status,0);
    assert.equal(env.commit().status,0);
    fs.writeFileSync(path.join(env.script,'governance_gate.cjs'),'process.exit(50);\n');
    const installed=env.install();
    assert.equal(installed.status,0,installed.stderr);
    assert.notEqual(env.commit().status,0,'成功重装必须执行新版校验器');
  }finally{env.close();}
});

test('Git 私有目录钩子符号链接不得重新指向工作树可执行文件',()=>{
  if(process.platform==='win32') return;
  const env=hookFixture();
  try{
    const privateHook=path.join(env.work,'.git','hooks','pre-commit');
    const untrusted=path.join(env.work,'pre-commit.sh');
    fs.writeFileSync(untrusted,'#!/bin/sh\nexit 51\n',{mode:0o755});
    fs.symlinkSync(untrusted,privateHook);
    const refused=env.install();
    assert.notEqual(refused.status,0);
    assert.match(refused.stderr,/链接指向外部路径/);
  }finally{env.close();}
});

test('不存在的钩子目录经外部符号链接父路径时拒绝安装，随后仍可安装受信钩子',()=>{
  if(process.platform==='win32') return;
  const env=hookFixture();
  try{
    const outside=path.join(env.work,'external-hooks');
    fs.mkdirSync(outside);
    fs.symlinkSync(outside,path.join(env.work,'.git','link'),'dir');
    assert.equal(env.run('git',['config','core.hooksPath','.git/link/nested']).status,0);
    const refused=env.install();
    assert.notEqual(refused.status,0);
    assert.match(refused.stderr,/符号链接/);
    assert.equal(fs.existsSync(path.join(outside,'nested')),false);
    assert.equal(env.run('git',['config','--unset','core.hooksPath']).status,0);
    assert.equal(env.install().status,0);
    assert.equal(env.commit().status,0);
    assert.notEqual(env.commit('fix(api): invalid login').status,0);
  }finally{env.close();}
});

test('即使符号链接指向 Git 私有目录，也拒绝通过可重定向的中间父路径安装',()=>{
  if(process.platform==='win32') return;
  const env=hookFixture();
  try{
    fs.symlinkSync(path.join(env.work,'.git','hooks'),path.join(env.work,'.git','link'),'dir');
    assert.equal(env.run('git',['config','core.hooksPath','.git/link/nested']).status,0);
    const refused=env.install();
    assert.notEqual(refused.status,0);
    assert.match(refused.stderr,/符号链接/);
  }finally{env.close();}
});

test('关联工作树安装共享钩子后删除该工作树，主仓库提交仍保留校验',()=>{
  const env=hookFixture();
  const linked=path.join(env.work,'linked');
  try{
    fs.writeFileSync(path.join(env.work,'seed.txt'),'seed\n');
    assert.equal(env.run('git',['add','.github','seed.txt']).status,0);
    const first=env.run('git',['-c','commit.gpgsign=false','commit','-q','-m','test(governance): 创建关联工作树的测试基线']);
    assert.equal(first.status,0,first.stderr);
    assert.equal(env.run('git',['worktree','add','-q','-b','test/shared-hooks',linked]).status,0);
    const installed=env.install(linked);
    assert.equal(installed.status,0,installed.stderr);
    const hook=fs.readFileSync(path.join(env.work,'.git','hooks','commit-msg'),'utf8');
    assert.ok(hook.includes(path.join(env.work,'.git','standards-hooks-')),'依赖必须位于共同 Git 目录');
    assert.ok(!hook.includes(path.join('.git','worktrees','linked','standards-hooks-')));
    assert.equal(env.run('git',['worktree','remove','--force',linked]).status,0);
    assert.equal(env.commit().status,0,'删除关联工作树后仍应接受合法提交');
    assert.notEqual(env.commit('fix(api): invalid login').status,0,'共享钩子仍应拒绝违规消息');
  }finally{
    if(fs.existsSync(linked)) env.run('git',['worktree','remove','--force',linked]);
    env.close();
  }
});

test('管理标记不能授权覆盖附加在 exec 前的独立检查',()=>{
  const env=hookFixture();
  try{
    assert.equal(env.install().status,0);
    const hook=path.join(env.work,'.git','hooks','commit-msg');
    const original=fs.readFileSync(hook,'utf8');
    const guarded=original.replace('set -eu\nexec node ','set -eu\nexit 58\nexec node ');
    assert.notEqual(guarded,original);
    fs.writeFileSync(hook,guarded);
    assert.notEqual(env.commit().status,0);
    const refused=env.install();
    assert.notEqual(refused.status,0);
    assert.match(refused.stderr,/修改过的 commit-msg/);
    assert.equal(fs.readFileSync(hook,'utf8'),guarded);
    assert.notEqual(env.commit().status,0,'附加的有效检查不得被移除');
  }finally{env.close();}
});

test('受管理钩子指向非标准执行文件时禁止重装覆盖',()=>{
  const env=hookFixture();
  try{
    assert.equal(env.install().status,0);
    const hook=path.join(env.work,'.git','hooks','commit-msg');
    const original=fs.readFileSync(hook,'utf8');
    const changed=original.replace(/standards-hooks-[^/']+\/governance_gate\.cjs/u,
      'standards-hooks-replaced/extra.cjs');
    assert.notEqual(changed,original);
    fs.writeFileSync(hook,changed);
    assert.notEqual(env.install().status,0);
    assert.equal(fs.readFileSync(hook,'utf8'),changed);
  }finally{env.close();}
});
