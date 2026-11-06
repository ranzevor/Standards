'use strict';
const fs=require('node:fs');
const path=require('node:path');
const {execFileSync}=require('node:child_process');

const git=(args,cwd)=>execFileSync('git',args,{cwd,encoding:'utf8'}).trim();
const root=fs.realpathSync(git(['rev-parse','--show-toplevel'],process.cwd()));
const common=fs.realpathSync(path.resolve(root,git(['rev-parse','--git-common-dir'],root)));
const target=path.join(common,'standards-hooks');
const vendor=path.join(target,'vendor');
fs.mkdirSync(vendor,{recursive:true});
fs.copyFileSync(path.join(root,'.github','scripts','governance_gate.cjs'),
  path.join(target,'governance_gate.cjs'));
fs.copyFileSync(path.join(root,'.github','scripts','vendor','commonmark-0.29.2.min.cjs'),
  path.join(vendor,'commonmark-0.29.2.min.cjs'));
const hook=path.join(target,'commit-msg');
fs.writeFileSync(hook,
  '#!/bin/sh\nset -eu\nnode "$(dirname "$0")/governance_gate.cjs" message-file "$1"\n',
  {mode:0o755});
fs.chmodSync(hook,0o755);
execFileSync('git',['config','--local','core.hooksPath',target],{cwd:root});
