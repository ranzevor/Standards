"""L4 数据安全规范机制、验收及场景覆盖校验。"""
import sys
if sys.flags.optimize: raise RuntimeError("Validation requires assertions enabled; do not use -O or -OO")
import re
from checks.retained_content.profile_integrity import mechanism_parts
from checks.retained_content.observability_content_validation import OBSERVABILITY_ID, assert_observability_complete
from checks.retained_content.version_rollback_validation import VERSION_ROLLBACK_ID, assert_version_rollback_complete

SECURITY_ID = "STD-L4-DATABASE-011"
AI_AGENT_BASELINE_ID = "STD-L4-AI-AGENT-001"
MODEL_INFERENCE_ID = "STD-L4-AI-AGENT-014"
PROMPT_INJECTION_ID = "STD-L4-AI-AGENT-011"
CONTEXT_COMPACTION_ID = "STD-L4-AI-AGENT-007"
RETRIEVAL_PROVENANCE_ID = "STD-L4-AI-AGENT-012"
MEMORY_LIFECYCLE_ID = "STD-L4-AI-AGENT-010"
MCP_TOOL_CONTRACT_ID = "STD-L4-AI-AGENT-009"
AGENT_ACTION_AUTH_ID = "STD-L4-AI-AGENT-004"
EXECUTION_ISOLATION_ID = "STD-L4-AI-AGENT-008"
AGENT_COMMUNICATION_ID = "STD-L4-AI-AGENT-006"
AGENT_ORCHESTRATION_ID = "STD-L4-AI-AGENT-005"
CLOUD_IAM_ID = "STD-L4-CLOUD-005"
CLOUD_NETWORK_ID = "STD-L4-CLOUD-004"
CLOUD_HOST_ID = "STD-L4-CLOUD-002"
CLOUD_IAC_ID = "STD-L4-CLOUD-007"
CLOUD_CI_ID = "STD-L4-CLOUD-001"
CLOUD_SUPPLY_ID = "STD-L4-CLOUD-011"
CLOUD_SECRETS_ID = "STD-L4-CLOUD-013"
CLOUD_ROLLOUT_ID = "STD-L4-CLOUD-006"
CLOUD_CAPACITY_ID = "STD-L4-CLOUD-009"
CLOUD_OBSERVE_ID = "STD-L4-CLOUD-012"
CLOUD_DR_ID = "STD-L4-CLOUD-008"
CLOUD_COST_ID = "STD-L4-CLOUD-010"
BAD = {"", "undefined", "null", "none", "n/a", "todo", "tbd", "待定", "待补充", "—"}
SCENARIOS = re.compile(r"^\| ([^|\n]+) \| (§[^|\n]+) \| ([^|\n]+) \|$", re.M)

def assert_ai_agent_baseline_complete(entry, body):
    parts = mechanism_parts(body)
    assert (entry['mechanism_count'],entry['static_failure_scenarios']) in {(37,46),(38,47)}, 'AI exact retained/extended profile'
    assert len(parts) == entry["mechanism_count"], "AI mechanisms"
    for index, (num, mechanism, acceptance) in enumerate(parts, 1):
        assert num == f"{index:02}", ("AI mechanism order", index)
        assert mechanism.strip().lower() not in BAD, ("AI mechanism", index)
        assert acceptance.strip().lower() not in BAD, ("AI acceptance", index)
    marker = f"## 四、{entry['static_failure_scenarios']} 项静态失败输入与预期判定\n"
    assert body.count(marker) == 1, "AI failure section"
    fragment = body.split(marker, 1)[1]
    assert "\n## 五、专题与 L5/L6 继承边界" in fragment, "AI failure end"
    fragment = fragment.split("\n## 五、专题与 L5/L6 继承边界", 1)[0]
    rows = SCENARIOS.findall(fragment)
    assert len(rows) == entry["static_failure_scenarios"] and len(rows) > len(parts), "AI scenarios"
    for i, (failure, refs, expected) in enumerate(rows, 1):
        assert failure.strip().lower() not in BAD, ("AI failure", i)
        assert expected.strip().lower() not in BAD, ("AI expectation", i)
        found = re.findall(r"§(\d{2})", refs)
        assert found and all(1 <= int(value) <= len(parts) for value in found), ("AI references", i)
        if i <= 37:
            assert found == [f"{i:02}"], ("AI direct reference", i)
        elif i <= 46:
            assert len(set(found)) >= 2, ("AI compound reference", i)
        else:
            assert found == [f'{i-9:02}'], ('AI appended direct reference',i)


def assert_model_inference_complete(entry, body):
    parts = mechanism_parts(body)
    assert len(parts) == entry["mechanism_count"] == 35, "inference mechanisms"
    for index, (num, mechanism, acceptance) in enumerate(parts, 1):
        assert num == f"{index:02}", ("inference mechanism index", index)
        assert mechanism.strip().lower() not in BAD, ("inference mechanism", index)
        assert acceptance.strip().lower() not in BAD, ("inference acceptance", index)
    marker = "## 四、47 项静态失败输入及预期检查\n"
    assert body.count(marker) == 1, "inference failure section"
    section = body.split(marker, 1)[1]
    end = "\n## 五、真实集成与变更控制"
    assert end in section, "inference failure section end"
    rows = SCENARIOS.findall(section.split(end, 1)[0])
    assert len(rows) == entry["static_failure_scenarios"] == 47, "inference scenarios"
    for index, (failure, links, expected) in enumerate(rows, 1):
        assert failure.strip().lower() not in BAD, ("inference failure", index)
        assert expected.strip().lower() not in BAD, ("inference expected", index)
        refs = re.findall(r"§(\d{2})", links)
        assert refs and all(1 <= int(num) <= len(parts) for num in refs), ("inference references", index)
        if index <= len(parts):
            assert refs == [f"{index:02}"], ("inference direct reference", index)
        else:
            assert len(set(refs)) >= 2, ("inference compound reference", index)



def assert_prompt_injection_complete(entry, body):
    parts = mechanism_parts(body)
    assert len(parts) == entry["mechanism_count"] == 42, "injection mechanisms"
    for index, (num, mechanism, acceptance) in enumerate(parts, 1):
        assert num == f"{index:02}", ("injection mechanism id", index)
        assert mechanism.strip().lower() not in BAD, ("injection mechanism", index)
        assert acceptance.strip().lower() not in BAD, ("injection acceptance", index)
    marker = "## 四、54 条静态失败输入及预期检查\n"
    assert body.count(marker) == 1, "injection scenario heading"
    chunk = body.split(marker, 1)[1]
    end_marker = "\n## 五、分层验证、适用裁剪与真实结果"
    assert end_marker in chunk, "injection scenario end"
    rows = SCENARIOS.findall(chunk.split(end_marker, 1)[0])
    assert len(rows) == entry["static_failure_scenarios"] == 54, "injection scenario count"
    for index, (failure, refs_text, expected) in enumerate(rows, 1):
        assert failure.strip().lower() not in BAD, ("injection failure", index)
        assert expected.strip().lower() not in BAD, ("injection expectation", index)
        refs = re.findall(r"§(\d{2})", refs_text)
        assert refs and all(1 <= int(ref) <= len(parts) for ref in refs), ("injection references", index)
        if index <= len(parts):
            assert refs == [f"{index:02}"], ("injection direct mapping", index)
        else:
            assert len(set(refs)) >= 2, ("injection compound mapping", index)


def assert_context_compaction_complete(entry, body):
    parts = mechanism_parts(body)
    assert len(parts) == entry["mechanism_count"] == 40, "context mechanisms"
    for index, (number, contract, acceptance) in enumerate(parts, 1):
        assert number == f"{index:02}", ("context mechanism id", index)
        assert contract.strip().lower() not in BAD, ("context mechanism", index)
        assert acceptance.strip().lower() not in BAD, ("context acceptance", index)
    marker = "## 四、52 项静态失败输入及预期检查\n"
    assert body.count(marker) == 1, "context scenario section"
    text = body.split(marker, 1)[1]
    end = "\n## 五、验证方法、适用裁剪与项目交付边界"
    assert end in text, "context scenario section end"
    cases = SCENARIOS.findall(text.split(end, 1)[0])
    assert len(cases) == entry["static_failure_scenarios"] == 52, "context scenarios"
    for i, (failure, refs, expectation) in enumerate(cases, 1):
        assert failure.strip().lower() not in BAD, ("context failure", i)
        assert expectation.strip().lower() not in BAD, ("context expectation", i)
        values = re.findall(r"§(\d{2})", refs)
        assert values and all(1 <= int(x) <= len(parts) for x in values), ("context references", i)
        if i <= len(parts):
            assert values == [f"{i:02}"], ("context direct reference", i)
        else:
            assert len(set(values)) >= 2, ("context compound reference", i)


def assert_retrieval_provenance_complete(entry, body):
    mechanisms = mechanism_parts(body)
    assert len(mechanisms) == entry["mechanism_count"] == 40, "retrieval mechanisms"
    for index, (number, contract, acceptance) in enumerate(mechanisms, 1):
        assert number == f"{index:02}", ("retrieval mechanism id", index)
        assert contract.strip().lower() not in BAD, ("retrieval mechanism", index)
        assert acceptance.strip().lower() not in BAD, ("retrieval acceptance", index)
    marker = "## 四、52 项静态失败输入及预期检查\n"
    assert body.count(marker) == 1, "retrieval scenario section"
    segment = body.split(marker, 1)[1]
    end = "\n## 五、验证层级、最小适用及复核触发"
    assert end in segment, "retrieval scenario end"
    rows = SCENARIOS.findall(segment.split(end, 1)[0])
    assert len(rows) == entry["static_failure_scenarios"] == 52, "retrieval scenarios"
    for index, (failure, refs, expected) in enumerate(rows, 1):
        assert failure.strip().lower() not in BAD, ("retrieval failure", index)
        assert expected.strip().lower() not in BAD, ("retrieval expected", index)
        numbers = re.findall(r"§(\d{2})", refs)
        assert numbers and all(1 <= int(n) <= len(mechanisms) for n in numbers), ("retrieval references", index)
        if index <= len(mechanisms):
            assert numbers == [f"{index:02}"], ("retrieval direct mapping", index)
        else:
            assert len(set(numbers)) >= 2, ("retrieval composite mapping", index)


def assert_memory_lifecycle_complete(entry, body):
    mechanisms = mechanism_parts(body)
    assert len(mechanisms) == entry["mechanism_count"] == 40, "memory mechanisms"
    for index, (number, mechanism, acceptance) in enumerate(mechanisms, 1):
        assert number == f"{index:02}", ("memory mechanism id", index)
        assert mechanism.strip().lower() not in BAD, ("memory mechanism", index)
        assert acceptance.strip().lower() not in BAD, ("memory acceptance", index)
    marker = "## 四、52 项静态失败输入及预期检查\n"
    assert body.count(marker) == 1, "memory scenario section"
    fragment = body.split(marker, 1)[1]
    terminator = "\n## 五、静态评测、真实能力与 L5/L6 验收"
    assert terminator in fragment, "memory scenario section end"
    scenarios = SCENARIOS.findall(fragment.split(terminator, 1)[0])
    assert len(scenarios) == entry["static_failure_scenarios"] == 52, "memory scenario count"
    for index, (failure, refs, expected) in enumerate(scenarios, 1):
        assert failure.strip().lower() not in BAD, ("memory failure", index)
        assert expected.strip().lower() not in BAD, ("memory expectation", index)
        numbers = re.findall(r"§(\d{2})", refs)
        assert numbers and all(1 <= int(v) <= len(mechanisms) for v in numbers), ("memory scenario references", index)
        if index <= len(mechanisms):
            assert numbers == [f"{index:02}"], ("memory direct reference", index)
        else:
            assert len(set(numbers)) >= 2, ("memory compound reference", index)


def assert_mcp_tool_contract_complete(entry, body):
    mechanisms = mechanism_parts(body)
    assert (entry['mechanism_count'],entry['static_failure_scenarios']) in {(40,52),(43,55)}, 'MCP exact retained/extended profile'
    assert len(mechanisms) == entry["mechanism_count"], "MCP mechanisms"
    for index, (number, contract, acceptance) in enumerate(mechanisms, 1):
        assert number == f"{index:02}", ("MCP mechanism id", index)
        assert contract.strip().lower() not in BAD, ("MCP mechanism", index)
        assert acceptance.strip().lower() not in BAD, ("MCP acceptance", index)
    marker = f"## 四、{entry['static_failure_scenarios']} 条静态失败输入与预期检查\n"
    assert body.count(marker) == 1, "MCP scenario heading"
    fragment = body.split(marker, 1)[1]
    end = "\n## 五、分层互通与业务验收"
    assert end in fragment, "MCP scenario end"
    rows = SCENARIOS.findall(fragment.split(end, 1)[0])
    assert len(rows) == entry["static_failure_scenarios"], "MCP scenario count"
    for index, (failure, refs, expected) in enumerate(rows, 1):
        assert failure.strip().lower() not in BAD, ("MCP failure", index)
        assert expected.strip().lower() not in BAD, ("MCP expected", index)
        numbers = re.findall(r"§(\d{2})", refs)
        assert numbers and all(1 <= int(n) <= len(mechanisms) for n in numbers), ("MCP references", index)
        if index <= 40:
            assert numbers == [f"{index:02}"], ("MCP direct reference", index)
        elif index <= 52:
            assert len(set(numbers)) >= 2, ("MCP composite", index)
        else:
            assert numbers == [f'{index-12:02}'], ('MCP appended direct reference',index)


def assert_agent_action_authorization_complete(entry, body):
    mechanisms = mechanism_parts(body)
    assert len(mechanisms) == entry["mechanism_count"] == 40, "agent authorization mechanisms"
    for i, (number, mechanism, acceptance) in enumerate(mechanisms, 1):
        assert number == f"{i:02}", ("agent authorization numbering", i)
        assert mechanism.strip().lower() not in BAD, ("agent authorization mechanism", i)
        assert acceptance.strip().lower() not in BAD, ("agent authorization acceptance", i)
    marker = "## 四、52 条静态失败输入与预期判定\n"
    assert body.count(marker) == 1, "agent authorization scenario section"
    fragment = body.split(marker, 1)[1]
    end = "\n## 五、验证层级与真实业务条件"
    assert end in fragment, "agent authorization scenario end"
    rows = SCENARIOS.findall(fragment.split(end, 1)[0])
    assert len(rows) == entry["static_failure_scenarios"] == 52, "agent authorization scenarios"
    for index, (failure, refs, expected) in enumerate(rows, 1):
        assert failure.strip().lower() not in BAD, ("agent failure", index)
        assert expected.strip().lower() not in BAD, ("agent expected", index)
        values = re.findall(r"§(\d{2})", refs)
        assert values and all(1 <= int(n) <= len(mechanisms) for n in values), ("agent references", index)
        if index <= len(mechanisms):
            assert values == [f"{index:02}"], ("agent direct mapping", index)
        else:
            assert len(set(values)) >= 2, ("agent compound mapping", index)



def assert_execution_isolation_complete(entry, body):
    mechanisms = mechanism_parts(body)
    assert len(mechanisms) == entry["mechanism_count"] == 40, "execution mechanisms"
    for i, (number, mechanism, acceptance) in enumerate(mechanisms, 1):
        assert number == f"{i:02}", ("execution mechanism id", i)
        assert mechanism.strip().lower() not in BAD, ("execution mechanism", i)
        assert acceptance.strip().lower() not in BAD, ("execution acceptance", i)
    marker = "## 四、52 条静态失败输入及预期检查\n"
    assert body.count(marker) == 1, "execution scenario section"
    fragment = body.split(marker, 1)[1]
    end = "\n## 五、分层验收与失效恢复"
    assert end in fragment, "execution scenario end"
    scenarios = SCENARIOS.findall(fragment.split(end, 1)[0])
    assert len(scenarios) == entry["static_failure_scenarios"] == 52, "execution scenario count"
    for i, (failure, refs, expected) in enumerate(scenarios, 1):
        assert failure.strip().lower() not in BAD, ("execution failure input", i)
        assert expected.strip().lower() not in BAD, ("execution expected", i)
        numbers = re.findall(r"§(\d{2})", refs)
        assert numbers and all(1 <= int(v) <= 40 for v in numbers), ("execution references", i)
        if i <= 40:
            assert numbers == [f"{i:02}"], ("execution direct reference", i)
        else:
            assert len(set(numbers)) >= 2, ("execution compound reference", i)

def assert_agent_orchestration_complete(entry, body):
    """Validate orchestration mechanisms, control invariants and failure mappings."""
    mechanisms = mechanism_parts(body)
    assert len(mechanisms) == entry["mechanism_count"] == 36, "orchestration mechanisms"
    assert len(re.findall(r"^### §", body, re.M)) == 36, "orchestration malformed mechanism"
    for i, (number, mechanism, acceptance) in enumerate(mechanisms, 1):
        assert number == f"{i:02}", ("orchestration mechanism id", i)
        assert mechanism.strip().lower() not in BAD, ("orchestration mechanism", i)
        assert acceptance.strip().lower() not in BAD, ("orchestration acceptance", i)
    for heading in ("### 控制记录的最小语义", "### 状态转换不变量"):
        assert body.count(heading + "\n") == 1, ("orchestration control section", heading)
    prefix = body.split("\n## 二、", 1)[0]
    invariants = re.findall(r"^- I(\d+) ([^\n]+)$", prefix, re.M)
    assert [number for number, _ in invariants] == [str(i) for i in range(1, 7)], "orchestration invariants"
    assert all(value.strip().lower() not in BAD for _, value in invariants), "orchestration invariant content"
    records = prefix.split("### 控制记录的最小语义\n", 1)[1].split("### 状态转换不变量\n", 1)[0]
    for field in ("root_task_id", "plan_revision", "attempt_id", "control_epoch"):
        assert field in records, ("orchestration control field", field)
    marker = "## 四、48 条静态失败输入及预期检查\n"
    assert body.count(marker) == 1, "orchestration scenario section"
    tail = body.split(marker, 1)[1]
    end = "\n## 五、分层验证、恢复界面与变更触发"
    assert end in tail, "orchestration scenario end"
    section = tail.split(end, 1)[0]
    scenarios = SCENARIOS.findall(section)
    assert len(scenarios) == entry["static_failure_scenarios"] == 48, "orchestration scenario count"
    # Reject malformed rows that the strict regex would otherwise silently skip.
    assert len(re.findall(r"^\|", section, re.M)) == 50, "orchestration malformed table row"
    assert len({failure.strip() for failure, _, _ in scenarios}) == 48, "orchestration duplicate failure"
    for i, (failure, refs, expected) in enumerate(scenarios, 1):
        assert failure.strip().lower() not in BAD, ("orchestration failure", i)
        assert expected.strip().lower() not in BAD, ("orchestration expected", i)
        assert re.fullmatch(r"§\d{2}(?:、§\d{2})*", refs), ("orchestration reference syntax", i)
        values = re.findall(r"§(\d{2})", refs)
        assert all(1 <= int(value) <= 36 for value in values), ("orchestration reference range", i)
        assert len(set(values)) == len(values), ("orchestration repeated reference", i)
        if i <= 36:
            assert values == [f"{i:02}"], ("orchestration direct mapping", i)
        else:
            assert len(values) >= 2, ("orchestration compound mapping", i)


def assert_agent_communication_complete(entry, body):
    """Validate communication mechanisms, protocol invariants and failure mappings."""
    mechanisms = mechanism_parts(body)
    assert len(mechanisms) == entry["mechanism_count"] == 32, "communication mechanisms"
    assert len(re.findall(r"^### §", body, re.M)) == 32, "communication malformed mechanism"
    for i, (number, mechanism, acceptance) in enumerate(mechanisms, 1):
        assert number == f"{i:02}", ("communication mechanism id", i)
        assert mechanism.strip().lower() not in BAD, ("communication mechanism", i)
        assert acceptance.strip().lower() not in BAD, ("communication acceptance", i)
    for heading in ("### 最小关联记录", "### 协议不变量"):
        assert body.count(heading + "\n") == 1, ("communication control section", heading)
    prefix = body.split("\n## 二、", 1)[0]
    invariants = re.findall(r"^- I(\d+) ([^\n]+)$", prefix, re.M)
    assert [number for number, _ in invariants] == [str(i) for i in range(1, 7)], "communication invariants"
    assert all(value.strip().lower() not in BAD for _, value in invariants), "communication invariant content"
    records = prefix.split("### 最小关联记录\n", 1)[1].split("### 协议不变量\n", 1)[0]
    for field in ("root_task_id", "delegation_id", "caller_subject", "remote_service", "selected_interface", "remote_task_id", "followup_owner"):
        assert field in records, ("communication control field", field)
    marker = "## 四、42 条静态失败输入及预期检查\n"
    assert body.count(marker) == 1, "communication scenario section"
    tail = body.split(marker, 1)[1]
    end = "\n## 五、分层验证、例外与变更"
    assert end in tail, "communication scenario end"
    section = tail.split(end, 1)[0]
    scenarios = SCENARIOS.findall(section)
    assert len(scenarios) == entry["static_failure_scenarios"] == 42, "communication scenario count"
    # Reject malformed rows that the strict regex would otherwise silently skip.
    assert len(re.findall(r"^\|", section, re.M)) == 44, "communication malformed table row"
    assert len({failure.strip() for failure, _, _ in scenarios}) == 42, "communication duplicate failure"
    for i, (failure, refs, expected) in enumerate(scenarios, 1):
        assert failure.strip().lower() not in BAD, ("communication failure", i)
        assert expected.strip().lower() not in BAD, ("communication expected", i)
        assert re.fullmatch(r"§\d{2}(?:、§\d{2})*", refs), ("communication reference syntax", i)
        values = re.findall(r"§(\d{2})", refs)
        assert all(1 <= int(value) <= 32 for value in values), ("communication reference range", i)
        assert len(set(values)) == len(values), ("communication repeated reference", i)
        if i <= 32:
            assert values == [f"{i:02}"], ("communication direct mapping", i)
        else:
            assert len(values) >= 2, ("communication compound mapping", i)



def assert_cloud_database_contract(entry,body):
    parts = mechanism_parts(body)
    assert len(parts) == entry["mechanism_count"] == 48, "mechanism count"
    for i, (num, mechanism, acceptance) in enumerate(parts, 1):
        assert num == f"{i:02}", ("mechanism id", i)
        assert mechanism.strip().lower() not in BAD, ("mechanism body", i)
        assert acceptance.strip().lower() not in BAD, ("acceptance", i)
    groups = body.split("## 四、60 项静态失败输入及预期检查\n", 1)
    assert len(groups) == 2, "scenario heading"
    closing=[marker for marker in ('\n## 五、版本与独立验收\n','\n## 五、真实目标工具/API与验收产物合同\n') if marker in groups[1]]
    assert len(closing)==1 and groups[1].count(closing[0])==1, 'unique scenario closing'
    groups = groups[1].split(closing[0], 1)
    assert len(groups) == 2, "scenario closing"
    assert len(re.findall(r"^\|",groups[0],re.M))==80,"raw scenario row count"
    rows = SCENARIOS.findall(groups[0])
    assert len(rows) == entry["static_failure_scenarios"] == 60, "scenario count"
    for i, (input_, refs, check) in enumerate(rows, 1):
        assert input_.strip().lower() not in BAD, ("scenario input", i)
        assert check.strip().lower() not in BAD, ("scenario expectation", i)
        numbers = re.findall(r"§(\d{2})", refs)
        assert numbers and all(1 <= int(x) <= 48 for x in numbers), ("scenario ids", i)
        if i <= 48:
            assert numbers == [f"{i:02}"], ("direct case mapping", i)
        else:
            assert len(numbers) >= 2, ("compound case mapping", i)

DISPATCH={AI_AGENT_BASELINE_ID:assert_ai_agent_baseline_complete,MODEL_INFERENCE_ID:assert_model_inference_complete,PROMPT_INJECTION_ID:assert_prompt_injection_complete,CONTEXT_COMPACTION_ID:assert_context_compaction_complete,RETRIEVAL_PROVENANCE_ID:assert_retrieval_provenance_complete,MEMORY_LIFECYCLE_ID:assert_memory_lifecycle_complete,MCP_TOOL_CONTRACT_ID:assert_mcp_tool_contract_complete,AGENT_ACTION_AUTH_ID:assert_agent_action_authorization_complete,EXECUTION_ISOLATION_ID:assert_execution_isolation_complete,AGENT_COMMUNICATION_ID:assert_agent_communication_complete,AGENT_ORCHESTRATION_ID:assert_agent_orchestration_complete,OBSERVABILITY_ID:assert_observability_complete,VERSION_ROLLBACK_ID:assert_version_rollback_complete}
from checks.retained_content.ai_evaluation_content import ID as EVAL_ID,assert_evaluation_complete
DISPATCH[EVAL_ID]=assert_evaluation_complete
for ident in [SECURITY_ID,CLOUD_IAM_ID,CLOUD_NETWORK_ID,CLOUD_HOST_ID,CLOUD_IAC_ID,CLOUD_CI_ID,CLOUD_SUPPLY_ID,CLOUD_SECRETS_ID,CLOUD_ROLLOUT_ID,CLOUD_CAPACITY_ID,CLOUD_OBSERVE_ID,CLOUD_DR_ID,CLOUD_COST_ID]:DISPATCH[ident]=assert_cloud_database_contract

from checks.retained_content.profile_integrity import validate_body_identity
_RAW_DISPATCH=dict(DISPATCH)
def checked_dispatch(entry,body):
    validate_body_identity(entry,body)
    assert entry['id'] in _RAW_DISPATCH
    expected=entry['mechanism_count']
    headings=re.findall(r'^### §([^ ]+) [^\n]+$',body,re.M)
    assert headings==[f'{i:02}' for i in range(1,expected+1)],'complete exact mechanism headings'
    assert len(re.findall(r'^### §',body,re.M))==expected,'malformed extra heading'
    titles=re.findall(r'^### §[^ ]+ ([^\n]+)$',body,re.M)
    assert all(title.strip().lower() not in BAD for title in titles),'mechanism title placeholder'
    # Parse every contiguous technical scenario table, including repeated six-row groups.
    scenario=re.search(r'(?ms)^## 四[^\n]*失败[^\n]*\n(.*?)(?=^## 五)',body)
    assert scenario,'scenario bounds'
    failures=[];case_references=[]
    for line in scenario.group(1).splitlines():
        if not line.startswith('|'):continue
        if re.fullmatch(r'\|(?:[ :|-]+)\|',line):continue
        cells=[x.strip() for x in line.strip('|').split('|')]
        if len(cells)==3 and cells[0]=='失败输入' and '§' not in line:continue
        m=re.fullmatch(r'\| ([^|\n]+) \| (§[^|\n]+) \| ([^|\n]+) \|',line)
        assert m,'unparsed scenario row'
        failure,refs,outcome=m.groups()
        assert all(cell.strip().lower() not in BAD for cell in (failure,outcome)),'scenario field placeholder'
        failures.append(failure.strip())
        case_references.append(refs)
    assert len(failures)==entry['static_failure_scenarios'],'complete scenario row coverage'
    assert len(failures)==len(set(failures)),'duplicate failure input'
    # This exact failure-matrix contract uses local §NN identifiers. External
    # source chapters elsewhere in the document are not local clause references.
    for refs in case_references:
        assert re.fullmatch(r'§\d{2}(?:、§\d{2})*',refs),'exact case reference syntax'
        values=re.findall(r'§(\d{2})',refs)
        assert len(values)==len(set(values)) and all(1<=int(n)<=expected for n in values),'case references distinct/in bounds'
    _RAW_DISPATCH[entry['id']](entry,body)
DISPATCH={ident:checked_dispatch for ident in _RAW_DISPATCH}
