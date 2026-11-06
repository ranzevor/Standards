'use strict';
const fs=require('node:fs');
const commonmark=require('./vendor/commonmark-0.29.2.min.cjs');

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
function visibleInlineText(node){
  const fragments=[];
  const walker=node.walker();
  let event;
  while((event=walker.next())){
    if(!event.entering) continue;
    const child=event.node;
    if(child.type==='text'||child.type==='code') fragments.push(child.literal);
    else if(child.type==='softbreak'||child.type==='linebreak') fragments.push('\n');
    else if(child.type==='html_inline'
      && (/^<(?:br|hr)(?:\s+[^<>]*?)?\s*\/?>$/iu.test(child.literal)
        || /^<\/?(?:p|div|li|tr|h[1-6])\s*>$/iu.test(child.literal)))
      fragments.push('\n');
  }
  return fragments.join('');
}
function markdownVisibleLines(rawLines){
  const lines=rawLines.map(()=>'');
  const ast=new commonmark.Parser().parse(rawLines.join('\n'));
  const walker=ast.walker();
  let event;
  while((event=walker.next())){
    if(!event.entering) continue;
    const node=event.node;
    if(node.type!=='paragraph'&&node.type!=='heading') continue;
    let value=visibleInlineText(node);
    if(!value) continue;
    const rootItem=node.parent.type==='item'
      && node.parent.parent.type==='list'
      && node.parent.parent.parent.type==='document';
    if(rootItem){
      // A setext underline can turn a list item's first paragraph into a heading.
      // Its text is still the top-level field; further paragraphs belong to it.
      value=(node.parent.firstChild===node?'- ':'  ')+value;
    }else if(node.type==='heading'&&node.parent.type==='document'){
      // Nested headings never satisfy the PR section contract.
      value='#'.repeat(node.level)+' '+value;
    }
    const start=node.sourcepos[0][0]-1;
    const rootHeading=node.type==='heading'&&node.parent.type==='document';
    const firstItemBlock=rootItem&&node.parent.firstChild===node;
    const codeSpanOnly=node.type==='paragraph'&&node.firstChild
      && node.firstChild.type==='code'&&!node.firstChild.next;
    for(const [offset,part] of value.split('\n').entries()){
      const index=start+offset;
      if(index>=lines.length) break;
      let text=rootItem&&offset>0?'  '+part:part;
      // Literal headings or field markers in a paragraph are not Markdown structure.
      if(!rootHeading) text=text.replace(/^(\s*)(#{2,3})(?=[ \t])/u,'$1\\$2');
      if(!firstItemBlock||offset>0)
        text=text.replace(/^(\s*)([-*])(?=[ \t])/u,'$1\\$2');
      // A footer token must start a real top-level paragraph in the source.
      // Inline formatting or block quotes cannot create Conventional Commit tokens.
      const footerToken=/^(?:BREAKING CHANGE|[A-Za-z][A-Za-z0-9-]*)(?::[ \t]*|[ \t]+#)/u;
      if(!isPlaceholderLine(text)&&footerToken.test(text.trimStart())
        && (node.type!=='paragraph'||node.parent.type!=='document'
          ||!footerToken.test(rawLines[index]||''))){
        text='\\'+text;
      }
      // Keep literal inline code visible to the placeholder check, not the footer parser.
      if(codeSpanOnly&&footerToken.test(text.trim())){
        const tick=String.fromCharCode(96);
        text=tick+text+tick;
      }
      lines[index]+=(lines[index]?' ':'')+text;
    }
  }
  return lines;
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
  const renderedLines=prVisibleStructure(rawBody).lines;
  const {entries,footerStart}=parseFooters(visibleLines);
  const footers=entries.filter(f=>f.token==='BREAKING CHANGE'||f.token==='BREAKING-CHANGE');
  // Footer 的源码边界仍由原始行确定；正文长度按 AST 渲染结果计算。
  const bodyBeforeFooters=lines.slice(1,footerStart+1).join("\n");
  const visibleBody=prVisibleStructure(bodyBeforeFooters).lines.join("\n").trim();
  const m=/^(feat|fix|docs|refactor|perf|test|build|ci|chore|style|revert)\([^)]+\)(!)?: /u.exec(lines[0]);
  if(rawBody!==rawBody.normalize("NFC")) errors.push("提交正文必须采用 NFC 规范化文本");
  if((rawBody&&hasInvisibleChars(rawBody,true))||hasInvisibleChars(renderedLines.join('\n'),true))
    errors.push("提交正文包含控制字符、非普通空格或不可见 Unicode 字符");
  if(m&&/^(?:feat|fix|refactor|perf)$/u.test(m[1])){
    if(lines[1]!==""||visibleBody.replace(/\s/gu,"").length<24)
      errors.push("实质功能或缺陷变更需要空行分隔的可见、有效正文");
  }
  if(visibleLines.some(isPlaceholderLine)||renderedLines.some(isPlaceholderLine))
    errors.push("提交正文包含未填写的占位内容");
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

function prVisibleStructure(body){
  const root=new commonmark.Parser().parse(body);
  const lines=[],headings=[];
  const walker=root.walker();
  let event;
  while((event=walker.next())){
    if(!event.entering) continue;
    const node=event.node;
    if(node.type!=='paragraph'&&node.type!=='heading') continue;
    const value=visibleInlineText(node);
    if(node.type==='heading'&&node.parent.type==='document'
      &&(node.level===2||node.level===3)){
      headings.push({h:value.trim(),i:lines.length});
    }
    // 可见换行并不与 Markdown 源码的物理行一一对应。
    lines.push(...value.split('\n'));
  }
  return {lines,headings};
}
function markdownTemplateFields(body){
  const root=new commonmark.Parser().parse(body);
  const guidance='按变更实际涉及的对象填写。不适用时说明具体原因；无需为填写模板额外建立日志、快照、证据目录或 CI 制品。不能以字段齐全代替实际审查，也不能将尚未执行的验证写为已通过。';
  const guidanceTail=new RegExp([...guidance.replace(/\s/gu,'')].join('\\s*')+'\\s*$','u');
  const sections=new Map();
  let section=null,sectionLevel=0;
  for(let block=root.firstChild;block;block=block.next){
    if(block.type==='heading'){
      const heading=visibleInlineText(block).trim();
      const official=['目标、基线与候选','规范、行为与影响','验证','审查与合并前置'].includes(heading);
      if(section&&block.level>sectionLevel&&!(official&&block.level===3)) continue;
      section=block.level===2||block.level===3?heading:null;
      sectionLevel=block.level;
      if(section&&!sections.has(section)) sections.set(section,[]);
      continue;
    }
    if(block.type!=='list'||!section) continue;
    for(let item=block.firstChild;item;item=item.next){
      const first=item.firstChild;
      if(!first||(first.type!=='paragraph'&&first.type!=='heading')) continue;
      const text=visibleInlineText(first);
      const firstLine=text.split('\n')[0];
      const colon=firstLine.search(/[：:]/u);
      if(colon<0) continue;
      const label=firstLine.slice(0,colon).trim();
      const details=[text.slice(colon+1)];
      const collect=node=>{
        if(node.type==='paragraph'||node.type==='heading'){
          details.push(visibleInlineText(node));
          return;
        }
        if(node.type==='code_block'||node.type==='html_block') return;
        for(let child=node.firstChild;child;child=child.next) collect(child);
      };
      for(let child=first.next;child;child=child.next) collect(child);
      // 模板固定填写说明不是字段答案；即使误删空行导致懒续行也不可代填。
      const value=details.join('\n').replace(guidanceTail,'').trim();
      sections.get(section).push({label,value});
    }
  }
  return sections;
}
function prBodyErrors(body) {
  const errors=[];
  if(typeof body!=="string") return ["PR 正文缺少有效内容"];
  if(body!==body.normalize("NFC")) errors.push("PR 正文必须采用 NFC 规范化文本");
  const {lines,headings}=prVisibleStructure(body);
  const visibleBody=lines.join("\n");
  if(hasInvisibleChars(body,true)||hasInvisibleChars(visibleBody,true))
    errors.push("PR 正文包含控制字符、非普通空格或不可见 Unicode 字符");
  if(visibleBody.replace(/\s/gu,"").length<85) errors.push("PR 正文缺少有信息量的变更说明");
  if(lines.some(isPlaceholderLine)) errors.push("PR 正文包含未填模板占位");
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
    const recordsBySection=markdownTemplateFields(body);
    for(const [sectionName,fields] of Object.entries(templateFields)){
      const matching=headings.filter(x=>x.h===sectionName);
      if(!matching.length){errors.push("PR 缺少官方模板章节："+sectionName);continue;}
      if(matching.length!==1){errors.push("PR 官方模板章节重复："+sectionName);continue;}
      const records=recordsBySection.get(sectionName)||[];
      for(const aliases of fields){
        const label=aliases[0];
        const matches=records.filter(record=>aliases.includes(record.label));
        if(!matches.length){errors.push("PR 缺少官方模板字段："+label);continue;}
        if(matches.length!==1){errors.push("PR 官方模板字段重复："+label);continue;}
        const value=matches[0].value;
        if(value.replace(/[\s#*|>-]/gu,"").length<8||value.split("\n").some(isPlaceholderLine))
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
