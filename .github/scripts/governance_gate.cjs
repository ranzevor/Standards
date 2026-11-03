'use strict';
const fs=require('node:fs');
function titleErrors(value) {
  const errors=[];
  if(typeof value!=="string"||!value.trim()) return ["提交或 PR 标题为空"];
  if(value!==value.normalize("NFC")) errors.push("标题必须采用 NFC 规范化文本");
  if(/[\p{Cc}\p{Cf}\p{Zl}\p{Zp}]/u.test(value)) errors.push("标题存在控制字符或不可见格式字符");
  const m=/^(feat|fix|docs|refactor|perf|test|build|ci|chore|style|revert)\(([a-z][a-z0-9]*(?:[-/][a-z0-9]+)*)\)(!)?: ([^\r\n]+)$/u.exec(value);
  if(!m) return [...errors,"标题须采用 type(scope): 简体中文具体变更主题"];
  const subject=m[4];
  if(m[2].length>36) errors.push("scope 过长");
  if(subject.length<8||subject.length>105) errors.push("主题没有清晰的长度边界");
  if(subject!==subject.trim()||/\s{2,}/u.test(subject)) errors.push("主题存在首尾或连续空白");
  if((subject.match(/\p{Script=Han}/gu)||[]).length<4) errors.push("主题中文行为或对象描述不足");
  if(/^(?:更新|优化|修复|调整|完善|修改|改进|处理|整理)(?:项目|代码|文件|问题|功能|内容|配置|逻辑|文档|测试|流程|实现)?$/u.test(subject)) errors.push("主题使用空泛描述");
  if(!/(?:修正|修复|新增|补充|恢复|拒绝|禁止|校验|限制|重构|隔离|核实|记录|明确|实现|保护|升级|替换|避免|适配|保留|验证|支持|建立|接入|覆盖|清理|启用|切换|阻断|拆分|调整|更新|改进|完善|改为|移除|消除|识别|纠正|公开|固定|收敛|提取|增加|删除)/u.test(subject)) errors.push("主题缺少具体的中文变更行为");
  if(/\[(?:skip ci|ci skip)\]|\b(?:WIP|FIXME|TODO|TBD)\b/iu.test(subject)) errors.push("主题含跳过检查或占位标记");
  return errors;
}

function commitErrors(message) {
  if(typeof message!=="string"||!message) return ["提交消息为空"];
  const lines=message.replace(/\r\n/g,"\n").split("\n");
  const errors=titleErrors(lines[0]).map(e=>"提交："+e);
  const body=lines.slice(1).join("\n").trim();
  const m=/^(feat|fix|docs|refactor|perf|test|build|ci|chore|style|revert)\([^)]+\)(!)?: /u.exec(lines[0]);
  if(m&&/^(?:feat|fix|refactor|perf)$/u.test(m[1])) {
    if(lines[1]!==""||body.replace(/\s/gu,"").length<24) errors.push("实质功能或缺陷变更需要空行分隔的有效正文");
  }
  if(body&&/^(?:TODO|TBD|待补充|占位|暂无内容|待填写)$/imu.test(body)) errors.push("提交正文存在模板占位");
  if(m&&m[2]&&!/(?:^|\n)BREAKING CHANGE:\s*.*\p{Script=Han}/u.test(body)) errors.push("不兼容变更缺少中文 BREAKING CHANGE 说明");
  return errors;
}

function prBodyErrors(body) {
  if(typeof body!=="string"||body.replace(/\s/gu,"").length<85) return ["PR 正文缺少有信息量的变更说明"];
  const errors=[];
  if(/(?:^|\n)\s*(?:TODO|TBD|待补充|在此填写|请填写|placeholder)\s*(?:\n|$)/imu.test(body)) errors.push("PR 正文包含模板占位");
  const headings=[];
  const lines=body.split(/\r?\n/u);
  for(let i=0;i<lines.length;i++){const m=/^#{2,3}\s+(.+?)\s*$/u.exec(lines[i]);if(m) headings.push({h:m[1],i});}
  const groups={
    "背景与目标":/(?:背景|目标|动机)/u,
    "修改范围与实现":/(?:范围|修改|实现|变更|实施内容|修复内容)/u,
    "兼容性与风险":/(?:兼容|风险|影响|验收边界|适用边界)/u,
    "实际验证":/(?:验证|测试|回归|检查结果)/u,
    "未完成事项":/(?:未完成|待办|剩余|当前状态|已知问题|阻碍)/u
  };
  for(const [label,pattern] of Object.entries(groups)){
    const hits=headings.filter(x=>pattern.test(x.h));
    if(!hits.length){errors.push("PR 缺少可定位章节："+label);continue;}
    if(!hits.some(x=>{
      const next=headings.find(y=>y.i>x.i);
      const content=lines.slice(x.i+1,next?next.i:lines.length).join("").replace(/[\s#*`>\-|]/gu,"");
      return content.length>=10;
    })) errors.push("PR 章节缺少有效内容："+label);
  }
  return errors;
}

function branchErrors(name) {
  if(typeof name!=="string"||!/^(?:feat|fix|docs|refactor|perf|test|build|ci|chore|style|revert|release|hotfix|feature|maintenance|quality|archive|automation|data|content|diagnostic|dependabot)\/[a-z0-9][a-z0-9._/-]{2,95}$/u.test(name))
    return ["PR 源分支命名缺少明确用途前缀与具体对象"];
  return [];
}

function prErrors(pr,commits,files) {
  const errors=titleErrors(pr&&pr.title).map(e=>"PR："+e);
  errors.push(...prBodyErrors(pr&&pr.body).map(e=>"PR："+e));
  errors.push(...branchErrors(pr&&pr.head&&pr.head.ref).map(e=>"PR："+e));
  if(!Array.isArray(commits)||!commits.length) errors.push("PR 缺少可核验提交列表");
  else {
    for(const item of commits){
      const message=item&&item.commit&&item.commit.message;
      errors.push(...commitErrors(message).map(e=>(item&&item.sha?item.sha.slice(0,12):"未知提交")+" "+e));
    }
    if(pr&&pr.head&&pr.head.sha&&commits[commits.length-1].sha!==pr.head.sha) errors.push("提交列表末尾与当前 HEAD 不一致");
  }
  if(!Array.isArray(files)||!files.length) errors.push("PR 缺少可核验的非空差异");
  else {
    if(files.length>500) errors.push("PR 变更超过 500 文件，必须拆分独立审查范围");
    for(const f of files) if(!f||typeof f.filename!=="string"||/[\p{Cc}\p{Cf}]/u.test(f.filename)) errors.push("文件名存在无效或不可见字符");
  }
  return errors;
}
async function ghList(path,token) {
  const all=[];
  for(let page=1;page<=11;page++){
    const response=await fetch('https://api.github.com'+path+(path.includes('?')?'&':'?')+'per_page=100&page='+page,{headers:{
      'Accept':'application/vnd.github+json',
      'X-GitHub-Api-Version':'2022-11-28',
      'Authorization':'Bearer '+token
    }});
    if(!response.ok) throw new Error('GitHub API 返回 '+response.status+'，查询：'+path);
    const list=await response.json();
    if(!Array.isArray(list)) throw new Error('GitHub API 响应不是列表');
    all.push(...list);
    if(list.length<100) return all;
  }
  throw new Error('提交或文件列表超出可验证范围');
}
async function ghGet(path,token) {
  const response=await fetch('https://api.github.com'+path,{headers:{
    'Accept':'application/vnd.github+json',
    'X-GitHub-Api-Version':'2022-11-28',
    'Authorization':'Bearer '+token
  }});
  if(!response.ok) throw new Error('GitHub API 返回 '+response.status+'，查询：'+path);
  return response.json();
}
async function main(){
  const mode=process.argv[2];
  let errors=[];
  if(mode==='message-file'){
    if(!process.argv[3]) throw new Error('缺少 commit-msg 文件参数');
    errors=commitErrors(fs.readFileSync(process.argv[3],'utf8'));
  }else if(mode==='preflight-json'){
    if(!process.argv[3]) throw new Error('缺少 PR 预检 JSON 文件参数');
    const input=JSON.parse(fs.readFileSync(process.argv[3],'utf8'));
    errors=prErrors(input.pull_request,input.commits,input.files);
  }else if(mode==='pr'){
    const event=JSON.parse(fs.readFileSync(process.env.GITHUB_EVENT_PATH,'utf8'));
    if(!event.pull_request||!event.repository) throw new Error('事件缺少 PR 身份');
    const token=process.env.GITHUB_TOKEN;
    if(!token) throw new Error('缺少 GitHub 读取令牌');
    const repo=event.repository.full_name;
    if(!/^[A-Za-z0-9_.-]+\/[A-Za-z0-9_.-]+$/u.test(repo)) throw new Error('仓库身份无效');
    const n=event.pull_request.number;
    if(!Number.isSafeInteger(n)||n<=0) throw new Error('PR 编号无效');
    const prefix='/repos/'+repo+'/pulls/'+n;
    const live=await ghGet(prefix,token);
    if(live.head.sha!==event.pull_request.head.sha) throw new Error('PR HEAD 已变化，拒绝使用过时数据');
    const [commits,files]=await Promise.all([ghList(prefix+'/commits',token),ghList(prefix+'/files',token)]);
    errors=prErrors(live,commits,files);
  }else throw new Error('不支持的检查模式');
  for(const problem of errors) console.error('FAIL: '+problem);
  if(errors.length) process.exitCode=1;
  else console.log('PASS: 提交与 PR 元数据校验通过');
}
module.exports={titleErrors,commitErrors,prBodyErrors,branchErrors,prErrors};
if(require.main===module) main().catch(e=>{console.error('FAIL: '+e.message);process.exitCode=1;});
