'use strict';
const fs=require('node:fs');
const path=require('node:path');
const {execFileSync,spawnSync}=require('node:child_process');
const {randomUUID}=require('node:crypto');

const git=(args,cwd)=>execFileSync('git',args,{cwd,encoding:'utf8'}).trim();
const gitOptional=(args,cwd)=>{
  const result=spawnSync('git',args,{cwd,encoding:'utf8'});
  if(result.error) throw result.error;
  if(result.status===1) return null;
  if(result.status!==0) throw new Error(result.stderr.trim()||'Git 配置读取失败');
  return result.stdout.trim();
};
const inside=(candidate,base)=>candidate===base||candidate.startsWith(base+path.sep);
const shellQuote=value=>"'"+value.replace(/'/gu,"'\"'\"'")+"'";
const knownHooks=new Set([
  'applypatch-msg','pre-applypatch','post-applypatch','pre-commit','pre-merge-commit',
  'prepare-commit-msg','commit-msg','post-commit','pre-rebase','post-checkout',
  'post-merge','pre-push','pre-receive','update','proc-receive','post-receive',
  'post-update','push-to-checkout','pre-auto-gc','post-rewrite','sendemail-validate',
  'reference-transaction','fsmonitor-watchman','post-index-change'
]);
const managedHook=/# standards-governance: managed commit-msg/u;
const legacyHook='#!/bin/sh\nset -eu\nnode "$(dirname "$0")/governance_gate.cjs" message-file "$1"\n';

function activeHooks(dir){
  if(!fs.existsSync(dir)) return [];
  if(!fs.statSync(dir).isDirectory()) throw new Error('生效钩子路径不是目录：'+dir);
  return fs.readdirSync(dir).filter(name=>knownHooks.has(name)
    &&(fs.lstatSync(path.join(dir,name)).isFile()
      ||fs.lstatSync(path.join(dir,name)).isSymbolicLink()));
}
function install(){
  const root=fs.realpathSync(git(['rev-parse','--show-toplevel'],process.cwd()));
  const common=fs.realpathSync(path.resolve(root,git(['rev-parse','--git-common-dir'],root)));
  const gitDir=fs.realpathSync(git(['rev-parse','--absolute-git-dir'],root));
  const configured=gitOptional(['config','--path','--get','core.hooksPath'],root);
  const hooksDir=path.resolve(root,configured===null?
    git(['rev-parse','--git-path','hooks'],root):configured);
  // A worktree-controlled symlink must not be trusted as a Git-private hooks path.
  const trusted=[common,gitDir].some(base=>inside(hooksDir,base))
    &&(!fs.existsSync(hooksDir)
      ||[common,gitDir].some(base=>inside(fs.realpathSync(hooksDir),base)));
  const hooks=activeHooks(hooksDir);
  if(trusted){
    for(const name of hooks){
      const source=path.join(hooksDir,name);
      if(fs.lstatSync(source).isSymbolicLink()
        &&![common,gitDir].some(base=>inside(fs.realpathSync(source),base))){
        throw new Error('Git 私有钩子链接指向外部路径：'+name+'；请先审查并迁移到 Git 私有目录。');
      }
    }
  }
  if(!trusted&&hooks.length){
    throw new Error('当前工作树钩子路径包含已有钩子（'+hooks.join('、')+'）；请先审查并迁移到 Git 私有钩子目录，不能自动复制或停用。');
  }
  if(trusted&&hooks.includes('commit-msg')){
    const hookPath=path.join(hooksDir,'commit-msg');
    const stat=fs.lstatSync(hookPath);
    const source=stat.isSymbolicLink()?'':fs.readFileSync(hookPath,'utf8');
    if(!managedHook.test(source)&&source!==legacyHook){
      throw new Error('Git 私有目录已有独立 commit-msg 钩子；请先审查并整合，安装器不会覆盖。');
    }
  }
  const stage=fs.mkdtempSync(path.join(gitDir,'standards-hooks-'));
  let active=false;
  try{
    const src=path.join(root,'.github','scripts');
    fs.mkdirSync(path.join(stage,'vendor'));
    fs.copyFileSync(path.join(src,'governance_gate.cjs'),path.join(stage,'governance_gate.cjs'));
    fs.copyFileSync(path.join(src,'vendor','commonmark-0.29.2.min.cjs'),
      path.join(stage,'vendor','commonmark-0.29.2.min.cjs'));
    const content='#!/bin/sh\n# standards-governance: managed commit-msg\nset -eu\nexec node '
      +shellQuote(path.join(stage,'governance_gate.cjs').replace(/\\/gu,'/'))+' message-file "$1"\n';
    if(trusted){
      fs.mkdirSync(hooksDir,{recursive:true});
      const temporary=path.join(hooksDir,'.standards-commit-msg-'+randomUUID());
      try{
        fs.writeFileSync(temporary,content,{mode:0o755,flag:'wx'});
        fs.chmodSync(temporary,0o755);
        fs.renameSync(temporary,path.join(hooksDir,'commit-msg'));
        active=true;
      }finally{if(fs.existsSync(temporary)) fs.rmSync(temporary,{force:true});}
    }else{
      const hook=path.join(stage,'commit-msg');
      fs.writeFileSync(hook,content,{mode:0o755,flag:'wx'});
      fs.chmodSync(hook,0o755);
      const scope=gitOptional(['config','--bool','--get','extensions.worktreeConfig'],root)==='true'
        ?'--worktree':'--local';
      const previous=gitOptional(['config',scope,'--get','core.hooksPath'],root);
      let updated=false;
      try{
        git(['config',scope,'--replace-all','core.hooksPath',stage],root);
        updated=true;
        const effective=gitOptional(['config','--path','--get','core.hooksPath'],root);
        if(effective!==stage) throw new Error('安装后 core.hooksPath 生效配置不属于受信钩子目录');
        active=true;
      }catch(error){
        if(updated){
          if(previous===null) git(['config',scope,'--unset-all','core.hooksPath'],root);
          else git(['config',scope,'--replace-all','core.hooksPath',previous],root);
        }
        throw error;
      }
    }
  }finally{
    if(!active){
      const effective=gitOptional(['config','--path','--get','core.hooksPath'],root);
      if(effective!==stage) fs.rmSync(stage,{recursive:true,force:true});
    }
  }
}
try{install();}catch(error){console.error(error.message);process.exitCode=1;}
