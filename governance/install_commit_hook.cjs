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
const managedHook=/^#!\/bin\/sh\n# standards-governance: managed commit-msg\nset -eu\nexec node ('(?:[^'\n]|'"'"')*') message-file "\$1"\n$/u;
const legacyHook='#!/bin/sh\nset -eu\nnode "$(dirname "$0")/governance_gate.cjs" message-file "$1"\n';

// 校验所有已经存在的路径组件，防止符号链接将钩子重定向到工作树。
function privateHooksPath(candidate,roots){
  const base=roots.find(root=>inside(candidate,root));
  if(!base) return false;
  let current=base;
  for(const component of path.relative(base,candidate).split(path.sep).filter(Boolean)){
    current=path.join(current,component);
    const stat=fs.lstatSync(current,{throwIfNoEntry:false});
    if(!stat) break;
    if(stat.isSymbolicLink()) throw new Error('Git 私有钩子路径含符号链接：'+current+'；请先审查并迁移。');
    if(!stat.isDirectory()) throw new Error('Git 私有钩子路径存在非目录组件：'+current);
  }
  return true;
}
function hookContent(script){
  return '#!/bin/sh\n# standards-governance: managed commit-msg\nset -eu\nexec node '
    +shellQuote(script.replace(/\\/gu,'/'))+' message-file "$1"\n';
}
function isManagedHook(source,roots){
  const match=managedHook.exec(source);
  if(!match) return false;
  const quoted=match[1];
  const sourcePath=quoted.slice(1,-1).replace(/'"'"'/gu,"'");
  if(shellQuote(sourcePath)!==quoted) return false;
  const script=path.resolve(sourcePath.replace(/\//gu,path.sep));
  const stage=path.dirname(script);
  if(path.basename(script)!=='governance_gate.cjs'
    ||!/^standards-hooks-[a-zA-Z0-9_-]+$/u.test(path.basename(stage))
    ||!privateHooksPath(stage,roots)) return false;
  const existing=fs.lstatSync(script,{throwIfNoEntry:false});
  return (!existing||existing.isFile())&&source===hookContent(script);
}

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
  const worktreeHooks=gitOptional(['config','--bool','--get','extensions.worktreeConfig'],root)==='true'
    ?gitOptional(['config','--worktree','--get','core.hooksPath'],root):null;
  if(inside(hooksDir,path.join(common,'worktrees'))
    &&!(worktreeHooks!==null&&inside(hooksDir,gitDir))){
    throw new Error('共享钩子路径指向会随关联工作树删除的 Git 目录；请改用共同 Git 目录。');
  }
  const privateRoots=[common,gitDir];
  const trusted=privateHooksPath(hooksDir,privateRoots);
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
    if(!isManagedHook(source,privateRoots)&&source!==legacyHook){
      throw new Error('Git 私有目录已有独立 commit-msg 钩子或修改过的 commit-msg 钩子；请先审查并整合，安装器不会覆盖。');
    }
  }
  const stage=fs.mkdtempSync(path.join(common,'standards-hooks-'));
  let active=false;
  try{
    const src=path.join(root,'.github','scripts');
    fs.mkdirSync(path.join(stage,'vendor'));
    fs.copyFileSync(path.join(src,'governance_gate.cjs'),path.join(stage,'governance_gate.cjs'));
    fs.copyFileSync(path.join(src,'vendor','commonmark-0.29.2.min.cjs'),
      path.join(stage,'vendor','commonmark-0.29.2.min.cjs'));
    const content=hookContent(path.join(stage,'governance_gate.cjs'));
    if(trusted){
      fs.mkdirSync(hooksDir,{recursive:true});
      privateHooksPath(hooksDir,privateRoots);
      const temporary=path.join(hooksDir,'.standards-commit-msg-'+randomUUID());
      try{
        fs.writeFileSync(temporary,content,{mode:0o755,flag:'wx'});
        fs.chmodSync(temporary,0o755);
        privateHooksPath(hooksDir,privateRoots);
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
