'use strict';
const fs=require('node:fs');

const INVALID_TEXT_CHAR=/[\p{Cc}\p{Cf}\p{Zs}\p{Zl}\p{Zp}\p{Default_Ignorable_Code_Point}]/u;
function hasInvisibleChars(value,multiline=false){
  const normalized=multiline?value.replace(/\r\n/gu,"\n"):value;
  return INVALID_TEXT_CHAR.test(normalized.replace(multiline?/[ \t\n]/gu:/ /gu,""));
}
function markdownPlainText(value){
  return value.trim()
    .replace(/^(?:\s*>\s*)+/u,"")
    .replace(/^\s{0,3}#{1,6}\s+/u,"")
    .replace(/^\s*(?:[-*+]\s+(?:\[[ xX]\]\s*)?|\d+[.)]\s+)/u,"")
    .replace(/!\[([^\]]*)\]\([^)]+\)/gu,"$1")
    .replace(/\[([^\]]+)\]\([^)]+\)/gu,"$1")
    .replace(/[*_`~]/gu,"").trim();
}
function isPlaceholderLine(value){
  return /^(?:TODO|TBD|FIXME|待补充|占位|暂无内容|待填写|在此填写|请填写|placeholder)(?:\s*[:：-].*)?$/iu.test(markdownPlainText(value));
}
function indentationColumns(space,start=0){
  let column=start;
  for(const char of space) column+=char==='\t'?4-column%4:1;
  return column;
}
function markdownVisibleLines(rawLines){
  let fenceChar='',fenceMin=0,fenceBase=0,inComment=false,indentedCode=false,previousBlank=true;
  const listStack=[];
  return rawLines.map(line=>{
    if(fenceChar){
      const close=/^([ \t]*)(\x60{3,}|~{3,})[ \t]*$/u.exec(line);
      if(close&&close[2][0]===fenceChar&&close[2].length>=fenceMin){
        const column=indentationColumns(close[1]);
        if(column>=fenceBase&&column<=fenceBase+3){
          fenceChar='';fenceMin=0;previousBlank=true;indentedCode=false;
        }
      }
      return '';
    }
    if(!inComment){
      if(!line.trim()){previousBlank=true;return '';}
      const leading=/^[ \t]*/u.exec(line)[0];
      const indent=indentationColumns(leading);
      const marker=/^([ \t]*)([-*+]|\d{1,9}[.)])([ \t]+)/u.exec(line);
      let listParent=-1;
      if(marker){
        for(let i=listStack.length-1;i>=0;i--){
          const base=listStack[i].contentIndent;
          if(indent>=base&&indent<=base+3){listParent=i;break;}
        }
      }
      if(marker&&(listParent>=0||indent<=3)){
        const markerEnd=indent+marker[2].length;
        const contentColumn=indentationColumns(marker[3],markerEnd);
        listStack.length=listParent+1;
        listStack.push({contentIndent:contentColumn-markerEnd>4?markerEnd+1:contentColumn});
      }else{
        while(listStack.length&&indent<listStack[listStack.length-1].contentIndent) listStack.pop();
        const base=listStack.length?listStack[listStack.length-1].contentIndent:0;
        if(indent>=base+4&&(previousBlank||indentedCode)){
          indentedCode=true;return '';
        }
      }
      indentedCode=false;
      previousBlank=false;
      const base=listStack.length?listStack[listStack.length-1].contentIndent:0;
      const opener=/^([ \t]*)(\x60{3,}|~{3,})/u.exec(line);
      if(opener&&indent>=base&&indent<=base+3){
        fenceChar=opener[2][0];fenceMin=opener[2].length;fenceBase=base;
        return '';
      }
    }
    let visible='';
    for(let i=0;i<line.length;){
      if(inComment){
        const close=line.indexOf('-->',i);
        if(close<0)break;
        inComment=false;i=close+3;continue;
      }
      if(line.charCodeAt(i)===96){
        let size=1;
        while(line.charCodeAt(i+size)===96) size++;
        let cursor=i+size,end=-1;
        while(cursor<line.length){
          const next=line.indexOf(String.fromCharCode(96),cursor);
          if(next<0) break;
          let closing=1;
          while(line.charCodeAt(next+closing)===96) closing++;
          if(closing===size){end=next+closing;break;}
          cursor=next+closing;
        }
        if(end>=0){visible+=line.slice(i,end);i=end;continue;}
      }
      if(line.startsWith('<!--',i)){
        let slashes=0;
        for(let j=i-1;j>=0&&line.charCodeAt(j)===92;j--) slashes++;
        if(slashes%2===0){inComment=true;i+=4;continue;}
      }
      visible+=line[i++];
    }
    return visible;
  });
}
function parseFooters(lines){
  const entries=[];
  let footerStart=lines.length,active=null;
  for(let i=0;i<lines.length;i++){
    const marker=/^(BREAKING CHANGE|[A-Za-z][A-Za-z0-9-]*)(?::[ \t]*|[ \t]+#)(.*)$/u.exec(lines[i]);
    if(footerStart===lines.length){
      if(!marker||(i>0&&lines[i-1].trim())) continue;
      footerStart=i;
    }
    if(marker){
      if(active) entries.push(active);
      active={token:marker[1],start:i,content:[marker[2]]};
    }else if(active) active.content.push(lines[i]);
  }
  if(active) entries.push(active);
  return {entries,footerStart};
}
function titleErrors(value) {
  const errors=[];
  if(typeof value!=="string"||!value.trim()) return ["提交或 PR 标题为空"];
  if(value!==value.normalize("NFC")) errors.push("标题必须采用 NFC 规范化文本");
  if(hasInvisibleChars(value)) errors.push("标题包含控制字符、非普通空格或不可见 Unicode 字符");
  const m=/^(feat|fix|docs|refactor|perf|test|build|ci|chore|style|revert)\(([a-z][a-z0-9]*(?:[-/][a-z0-9]+)*)\)(!)?: ([^\r\n]+)$/u.exec(value);
  if(!m) return [...errors,"标题须采用 type(scope): 简体中文具体变更主题"];
  const subject=m[4];
  if(m[2].length>36) errors.push("scope 过长");
  if(subject.length<8||subject.length>105) errors.push("主题没有清晰的长度边界");
  if(subject!==subject.trim()||/\s{2,}/u.test(subject)) errors.push("主题存在首尾或连续空白");
  if((subject.match(/\p{Script=Han}/gu)||[]).length<4) errors.push("主题中文行为或对象描述不足");
  if(/^(?:更新|优化|修复|调整|完善|修改|改进|处理|整理)(?:项目|代码|文件|问题|功能|内容|配置|逻辑|文档|测试|流程|实现)?$/u.test(subject)) errors.push("主题使用空泛描述");
  if(/\[(?:skip ci|ci skip)\]|\b(?:WIP|FIXME|TODO|TBD)\b/iu.test(subject)) errors.push("主题含跳过检查或占位标记");
  return errors;
}

function commitErrors(message) {
  if(typeof message!=="string"||!message) return ["提交消息为空"];
  const lines=message.replace(/\r\n/gu,"\n").split("\n");
  const errors=titleErrors(lines[0]).map(e=>"提交："+e);
  const rawBody=lines.slice(1).join("\n");
  const visibleLines=markdownVisibleLines(lines.slice(1));
  const {entries,footerStart}=parseFooters(visibleLines);
  const footers=entries.filter(f=>f.token==='BREAKING CHANGE'||f.token==='BREAKING-CHANGE');
  const textLines=visibleLines.slice(0,footerStart);
  const visibleBody=textLines.join("\n").trim();
  const m=/^(feat|fix|docs|refactor|perf|test|build|ci|chore|style|revert)\([^)]+\)(!)?: /u.exec(lines[0]);
  if(rawBody!==rawBody.normalize("NFC")) errors.push("提交正文必须采用 NFC 规范化文本");
  if(rawBody&&hasInvisibleChars(rawBody,true)) errors.push("提交正文包含控制字符、非普通空格或不可见 Unicode 字符");
  if(m&&/^(?:feat|fix|refactor|perf)$/u.test(m[1])){
    if(lines[1]!==""||visibleBody.replace(/\s/gu,"").length<24)
      errors.push("实质功能或缺陷变更需要空行分隔的可见、有效正文");
  }
  if(visibleLines.some(isPlaceholderLine)) errors.push("提交正文包含未填写的占位内容");
  const validBreakStarts=new Set(footers.map(f=>f.start));
  if(visibleLines.some((line,i)=>/^BREAKING(?: CHANGE|-CHANGE):/u.test(line)&&!validBreakStarts.has(i)))
    errors.push("不兼容变更 footer 必须与正文以空行分隔");
  if((m&&m[2])||footers.length){
    const message="不兼容变更必须具体说明契约、影响和迁移方式";
    // Conventional Commits 允许通过标题 ! 标记而不重复 BREAKING CHANGE footer。
    const explanations=footers.length?footers.map(f=>f.content.join("\n").trim()):[visibleBody];
    for(const details of explanations){
      // 固定关键词不能判断不同技术领域的迁移说明是否完整。
      if(details.replace(/\s/gu,"").length<35) errors.push(message);
    }
  }
  return errors;
}

function prBodyErrors(body) {
  const errors=[];
  if(typeof body!=="string") return ["PR 正文缺少有效内容"];
  if(body!==body.normalize("NFC")) errors.push("PR 正文必须采用 NFC 规范化文本");
  if(hasInvisibleChars(body,true)) errors.push("PR 正文包含控制字符、非普通空格或不可见 Unicode 字符");
  const lines=markdownVisibleLines(body.split(/\r?\n/u));
  const visibleBody=lines.join("\n");
  if(visibleBody.replace(/\s/gu,"").length<85) errors.push("PR 正文缺少有信息量的变更说明");
  if(lines.some(isPlaceholderLine)) errors.push("PR 正文包含未填模板占位");
  const headings=[];
  for(let i=0;i<lines.length;i++){
    const m=/^#{2,3}\s+(.+?)\s*$/u.exec(lines[i]);
    if(m) headings.push({h:m[1],i});
  }
  // 优先使用精简模板字段；旧版 PR 的同义字段仍可用于兼容读取。
  const templateFields={
    "目标、基线与候选":[
      ["变更目标与依据","需求/条款ID及准确版本"],
      ["本次范围及目标分支","本次范围与明确不改范围"]
    ],
    "规范、行为与影响":[
      ["具体变更及可观察行为","正文、来源、依赖、示例与检查变更"],
      ["兼容性、迁移或恢复影响","使用者可观察变化及兼容/迁移影响"]
    ],
    "验证":[
      ["实际验证结果与结论","输入、环境、命令、退出码、预期/实际及证据"],
      ["尚未验证的范围或已知问题","未执行、部分执行或不适用范围及原因"]
    ],
    "审查与合并前置":[
      ["作者自查与独立审查状态","独立审查绑定的候选、范围和开放发现"],
      ["合并条件及未解决阻断项","合并前需重新确认的目标 HEAD、必需检查和阻断项"]
    ]
  };
  if(headings.some(x=>Object.hasOwn(templateFields,x.h))){
    for(const [sectionName,fields] of Object.entries(templateFields)){
      const section=headings.find(x=>x.h===sectionName);
      if(!section){errors.push("PR 缺少官方模板章节："+sectionName);continue;}
      const next=headings.find(x=>x.i>section.i);
      const sectionLines=lines.slice(section.i+1,next?next.i:lines.length);
      for(const aliases of fields){
        let index=-1,fieldPattern;
        for(const field of aliases){
          const escaped=Array.from(field,ch=>"\\^$.*+?()[]{}|".includes(ch)?"\\"+ch:ch).join("");
          const pattern=new RegExp("^\\s*[-*]\\s*"+escaped+"[：:]\\s*(.*)$","u");
          const found=sectionLines.findIndex(line=>pattern.test(line));
          if(found>=0){index=found;fieldPattern=pattern;break;}
        }
        const label=aliases[0];
        if(index<0){errors.push("PR 缺少官方模板字段："+label);continue;}
        const contents=[fieldPattern.exec(sectionLines[index])[1]];
        for(let j=index+1;j<sectionLines.length;j++){
          if(/^\s*[-*]\s*[^：:\n]+[：:]/u.test(sectionLines[j])) break;
          if(!sectionLines[j].trim()) continue;
          if(!/^\s{2,}\S/u.test(sectionLines[j])) break;
          contents.push(sectionLines[j]);
        }
        const value=contents.join("\n").trim();
        if(value.replace(/[\s#*`>|-]/gu,"").length<8||value.split("\n").some(isPlaceholderLine))
          errors.push("PR 官方模板字段缺少有效说明："+label);
      }
    }
  }else{
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
        const text=lines.slice(x.i+1,next?next.i:lines.length).join("").replace(/[\s#*`>\-|]/gu,"");
        return text.length>=12;
      })) errors.push("PR 章节缺少有效内容："+label);
    }
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
    for(const f of files) if(!f||typeof f.filename!=="string"||f.filename!==f.filename.normalize("NFC")||hasInvisibleChars(f.filename)) errors.push("文件名存在无效或不可见字符");
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
    if(event.pull_request.base && live.base && (live.base.ref!==event.pull_request.base.ref || (event.pull_request.base.sha && live.base.sha!==event.pull_request.base.sha))) throw new Error('PR 目标分支在事件后改变');
    const [commits,files]=await Promise.all([ghList(prefix+'/commits',token),ghList(prefix+'/files',token)]);
    const latest=await ghGet(prefix,token);
    if(latest.head.sha!==live.head.sha || (latest.base&&live.base&&(latest.base.ref!==live.base.ref||latest.base.sha!==live.base.sha))) throw new Error('PR HEAD 或目标基线在校验期间改变');
    if(latest.title!==live.title || latest.body!==live.body) throw new Error('PR 标题或正文在校验期间改变');
    errors=prErrors(latest,commits,files);
  }else throw new Error('不支持的检查模式');
  for(const problem of errors) console.error('FAIL: '+problem);
  if(errors.length) process.exitCode=1;
  else console.log('PASS: 提交与 PR 元数据校验通过');
}
module.exports={titleErrors,commitErrors,prBodyErrors,branchErrors,prErrors};
if(require.main===module) main().catch(e=>{console.error('FAIL: '+e.message);process.exitCode=1;});
