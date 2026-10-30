"""Finite observation oracles; supplied observations are not real cloud evidence.

These functions classify only the explicit fields below. They authenticate neither
an approval nor an observation and perform no provider calls or external effects.
"""
import hashlib
import math
import re
from decimal import Decimal, InvalidOperation
from fractions import Fraction

from .contracts import ContractError


def require(value, message):
    if not value:
        raise ContractError(message)


def boolean(value):
    require(type(value) is bool, 'observation must be a boolean')
    return value


def tick(value):
    require((type(value) is int or
             (type(value) is float and math.isfinite(value))) and value >= 0,
            'time must be a finite nonnegative number')
    return value


def content_identity(*, payloads, recorded_digests):
    """Different outputs are legal; misidentifying their actual bytes is not."""
    require(type(payloads) is list and type(recorded_digests) is list and
            len(payloads) == len(recorded_digests) and bool(payloads),
            'each observed output requires its own recorded identity')
    for payload, recorded in zip(payloads, recorded_digests):
        require(type(payload) is str and type(recorded) is str,
                'finite fixture encodes payloads as UTF-8 strings')
        actual = hashlib.sha256(payload.encode('utf-8')).hexdigest()
        require(actual == recorded, 'recorded content identity differs from observed bytes')
    return 'identified'


def approved_content(*, payload, approved_digest):
    require(type(payload) is str and type(approved_digest) is str,
            'payload and approved identity must be strings')
    require(hashlib.sha256(payload.encode('utf-8')).hexdigest() == approved_digest,
            'consumption substituted bytes outside the exact approved identity')
    return 'approved-content'


def classified_change(*, plan_digest, approved_plan_digest, irreversible,
                      irreversible_classified, protection_satisfied):
    require(type(plan_digest) is str and bool(plan_digest) and
            type(approved_plan_digest) is str and
            re.fullmatch(r'[0-9a-f]{64}', plan_digest) and
            re.fullmatch(r'[0-9a-f]{64}', approved_plan_digest),
            'exact plan SHA-256 identities required')
    boolean(irreversible); boolean(irreversible_classified); boolean(protection_satisfied)
    require(not irreversible or irreversible_classified,
            'irreversible effect was not classified before execution')
    require(plan_digest == approved_plan_digest and protection_satisfied,
            'execution lacks the exact approved plan or required protection')
    return 'authorized-in-fixture'


def outage_promise(*, outage_duration, approved_outage_limit, service_available,
                   reported_healthy):
    tick(outage_duration); tick(approved_outage_limit)
    boolean(service_available); boolean(reported_healthy)
    require(outage_duration <= approved_outage_limit,
            'observed outage violates the supplied approved recovery promise')
    require(not reported_healthy or service_available,
            'health report contradicts the observed unavailable service')
    return 'within-promise-honest'


def revocation_window(*, observed_at, revoke_deadline, write_allowed,
                      reported_revoked):
    tick(observed_at); tick(revoke_deadline)
    boolean(write_allowed); boolean(reported_revoked)
    require(not reported_revoked or not write_allowed,
            'revocation completion contradicts an observed allowed write')
    require(observed_at < revoke_deadline or not write_allowed,
            'write remains allowed at or beyond the supplied revocation deadline')
    return 'allowed-within-window' if write_allowed else 'observed-denied'


def dns_recovery(*, negative_cache_remaining, user_path_available,
                 reported_all_recovered):
    tick(negative_cache_remaining)
    boolean(user_path_available); boolean(reported_all_recovered)
    require(not reported_all_recovered or user_path_available,
            'all-users recovery report contradicts the observed failed path')
    # A positive remaining TTL alone is not a contract breach. This fixture does
    # not model resolver internals, serve-stale extensions or universal recovery.
    return 'recovered' if user_path_available else 'truthfully-not-recovered'


def rootfs_write(*, root_readonly_promised, writes_to_root, write_succeeded,
                 approved_separate_volume):
    boolean(root_readonly_promised); boolean(writes_to_root)
    boolean(write_succeeded); boolean(approved_separate_volume)
    require(not (writes_to_root and approved_separate_volume),
            'a separate mount is not the root-filesystem write in this fixture')
    require(not (root_readonly_promised and writes_to_root and write_succeeded),
            'runtime root read-only promise was breached')
    require(not (write_succeeded and not writes_to_root and
                 not approved_separate_volume), 'unapproved separate-volume write')
    return 'write-boundary-preserved'


def completion_report(*, actually_complete, reported_complete):
    boolean(actually_complete); boolean(reported_complete)
    require(not reported_complete or actually_complete,
            'completion claim exceeds the observed completion stage')
    return 'complete' if actually_complete else 'truthfully-incomplete'


def proof_consumption(*, proof_required, proof_verified, consumption_allowed,
                      referrers_supported, discovery):
    boolean(proof_required); boolean(proof_verified); boolean(consumption_allowed)
    boolean(referrers_supported)
    require(type(discovery) is str and discovery in
            {'referrers-api', 'compatible-index', 'none'}, 'known proof discovery path required')
    require(discovery != 'referrers-api' or referrers_supported,
            'unsupported API cannot be the observed discovery path')
    require(not proof_verified or discovery != 'none',
            'verified proof requires an identified discovery path')
    require(not (proof_required and consumption_allowed and not proof_verified),
            'required proof is missing but consumption was allowed')
    return 'consumption-allowed' if consumption_allowed else 'consumption-blocked'


def withdrawal_consumption(*, payload, denied_digests, consumption_allowed,
                           retained_in_storage):
    require(type(payload) is str and type(denied_digests) is list and
            all(type(x) is str for x in denied_digests), 'finite content policy inputs')
    boolean(consumption_allowed); boolean(retained_in_storage)
    actual = hashlib.sha256(payload.encode('utf-8')).hexdigest()
    require(not (actual in denied_digests and consumption_allowed),
            'withdrawn content was consumed contrary to the supplied deny policy')
    # Retention is deliberately not a rejection condition.
    return 'withdrawal-policy-preserved'


def secret_refresh(*, published_version, projected_version, consumer_version,
                   observed_at, refresh_deadline, reported_refreshed):
    require(all(type(v) is str and bool(v) for v in
                [published_version, projected_version, consumer_version]), 'exact version identities required')
    tick(observed_at); tick(refresh_deadline); boolean(reported_refreshed)
    changed = consumer_version == published_version
    require(not reported_refreshed or changed,
            'consumer refresh claim exceeds its observed version')
    require(observed_at < refresh_deadline or changed,
            'consumer still uses old value at the supplied refresh deadline')
    # Projected files and process environments are deliberately not equated.
    return 'consumer-refreshed' if changed else 'consumer-refresh-pending'


def rotation_stage(*, notification_received, candidate_created, target_set,
                   target_tested, current_promoted, consumers_updated,
                   old_revoked, reported_stage):
    for value in [notification_received, candidate_created, target_set,
                  target_tested, current_promoted, consumers_updated, old_revoked]:
        boolean(value)
    require(not current_promoted or (target_set and target_tested),
            'CURRENT promoted before target change and test')
    required = {
        'awaiting': [True],
        'notification': [notification_received],
        'candidate': [candidate_created],
        'target-set': [target_set],
        'current': [candidate_created, target_set, target_tested, current_promoted],
        'complete': [candidate_created, target_set, target_tested, current_promoted,
                     consumers_updated, old_revoked],
    }
    require(type(reported_stage) is str and reported_stage in required,
            'known rotation observation stage required')
    require(all(required[reported_stage]), 'rotation report exceeds its actual stage')
    return reported_stage


def scoped_completion(*, observations, reported_complete_scopes):
    require(type(observations) is dict and bool(observations) and
            all(type(k) is str and k and type(v) is str and
                v in {'complete', 'pending', 'unknown'} for k, v in observations.items()),
            'named independent completion observations required')
    require(type(reported_complete_scopes) is list and
            all(type(k) is str and k in observations for k in reported_complete_scopes) and
            len(reported_complete_scopes) == len(set(reported_complete_scopes)),
            'completion claim scope must be explicit and unique')
    require(all(observations[k] == 'complete' for k in reported_complete_scopes),
            'completion claim includes a pending or unknown scope')
    return 'scoped-report-consistent'


def incident_facts(*, silence_active, failure_observed, incident_recorded,
                   reported_resolved):
    for value in [silence_active, failure_observed, incident_recorded, reported_resolved]:
        boolean(value)
    require(not failure_observed or (incident_recorded and not reported_resolved),
            'notification suppression erased or falsely closed the observed incident')
    return 'incident-facts-preserved'


def backup_scope(*, backed_objects, claimed_objects, required_objects):
    for values in [backed_objects, claimed_objects, required_objects]:
        require(type(values) is list and all(type(v) is str and v for v in values) and
                len(values) == len(set(values)), 'unique backup object identities required')
    require(set(claimed_objects) <= set(backed_objects),
            'backup completeness claim exceeds the backed object set')
    require(set(required_objects) <= set(backed_objects),
            'backup omitted a required object in its selected scope')
    return 'backup-scope-consistent'


def cost_value(text):
    # A deliberately finite fixture representation, not a currency-wide rule.
    require(type(text) is str and 0 < len(text) <= 200,
            'fixture cost must be a bounded decimal string')
    try:
        value = Decimal(text)
    except InvalidOperation as exc:
        raise ContractError('invalid decimal cost') from exc
    require(value.is_finite() and value >= 0, 'finite nonnegative cost required')
    digits = value.as_tuple()
    require(len(digits.digits) <= 128 and -12 <= digits.exponent <= 12,
            'fixture cost representation exceeds documented digit/scale bounds')
    return Fraction(value)


def retirement_resources(*, resources, claimed_deleted, reported_total_cost):
    require(type(resources) is list and type(claimed_deleted) is list and
            all(type(v) is str and v for v in claimed_deleted) and
            len(claimed_deleted) == len(set(claimed_deleted)), 'unique resource/deletion scopes required')
    seen = set()
    actual_total = Fraction(0)
    for row in resources:
        require(type(row) is dict and set(row) ==
                {'id', 'present', 'owner', 'observed_cost', 'recorded_cost'}, 'finite resource fields required')
        require(type(row['id']) is str and row['id'] and row['id'] not in seen,
                'unique resource identity required')
        seen.add(row['id']); boolean(row['present'])
        require(type(row['owner']) is str, 'resource owner must be a string')
        require(not row['present'] or bool(row['owner'].strip()),
                'retained resource has no recorded owner')
        require(not (row['present'] and row['id'] in claimed_deleted),
                'physical deletion claim contradicts retained resource')
        values = [cost_value(row[key]) for key in ['observed_cost', 'recorded_cost']]
        require(values[0] == values[1], 'retained or delayed cost was not accurately recorded')
        actual_total += values[0]
    require(set(claimed_deleted) <= seen, 'deletion claim references an unobserved resource')
    reported = cost_value(reported_total_cost)
    require(reported == actual_total,
            'reported total cost differs from the supplied observed scope')
    return 'retirement-state-and-cost-consistent'


def external_exit(*, active_integrations, reported_fully_retired):
    boolean(reported_fully_retired)
    require(type(active_integrations) is list, 'active integration observations required')
    seen = set()
    for row in active_integrations:
        require(type(row) is dict and set(row) == {'id', 'authorized', 'owner'},
                'exact integration observation fields required')
        require(type(row['id']) is str and row['id'] and row['id'] not in seen,
                'unique integration identity required')
        seen.add(row['id']); boolean(row['authorized'])
        require(type(row['owner']) is str and row['owner'].strip() and row['authorized'],
                'active integration lacks current authorization or owner')
    require(not reported_fully_retired or not active_integrations,
            'complete external retirement claimed while integrations remain active')
    return 'external-exit-scope-consistent'



def rotation_interruption(*, service_available, controlled_recovery,
                          outage_duration, approved_outage_limit,
                          reported_cutover_complete):
    boolean(service_available); boolean(controlled_recovery)
    boolean(reported_cutover_complete)
    require(service_available or controlled_recovery,
            'rotation outage has no supplied controlled cutover/recovery')
    outage_promise(outage_duration=outage_duration,
                   approved_outage_limit=approved_outage_limit,
                   service_available=service_available,
                   reported_healthy=reported_cutover_complete)
    return 'cutover-complete' if reported_cutover_complete else 'cutover-observation-pending'


def termination_accounting(*, accepted_operations, completed_operations,
                           recoverable_operations, reported_clean_completion,
                           forced_kill):
    boolean(reported_clean_completion); boolean(forced_kill)
    for values in (accepted_operations, completed_operations, recoverable_operations):
        require(type(values) is list and all(type(v) is str and v for v in values)
                and len(values) == len(set(values)), 'unique supplied operation identities required')
    require(set(completed_operations) <= set(accepted_operations)
            and set(recoverable_operations) <= set(accepted_operations),
            'completion/recovery evidence refers to an unaccepted operation')
    require(set(accepted_operations) <= set(completed_operations) | set(recoverable_operations),
            'accepted operation has neither completion nor durable recovery observation')
    require(not reported_clean_completion or set(accepted_operations) <= set(completed_operations),
            'clean completion claim includes work still requiring recovery')
    # A forced signal alone is deliberately not a lost-work predicate.
    return ('termination-complete-accounted' if set(accepted_operations) <= set(completed_operations)
            else 'recovery-pending')


def writer_admission(*, protocol, authorized_writers, observed_writers,
                     coordination_verified):
    require(type(protocol) is str and protocol in {'single-writer', 'coordinated-multiwriter'},
            'known supplied writer protocol required')
    boolean(coordination_verified)
    for values in (authorized_writers, observed_writers):
        require(type(values) is list and all(type(v) is str and v for v in values)
                and len(values) == len(set(values)), 'unique writer identities required')
    require(bool(authorized_writers), 'writer authority scope must be explicit')
    require(protocol != 'single-writer' or len(authorized_writers) == 1,
            'single-writer scope declares more than one current writer')
    require(protocol != 'coordinated-multiwriter' or coordination_verified,
            'multiple writers lack supplied supported coordination evidence')
    require(set(observed_writers) <= set(authorized_writers),
            'observed write is outside the supplied current writer authority')
    return 'writer-protocol-preserved'


ORACLES = {
    'rotation-interruption': rotation_interruption,
    'termination-accounting': termination_accounting,
    'writer-admission': writer_admission,
    'content-identity': content_identity,
    'approved-content': approved_content,
    'classified-change': classified_change,
    'outage-promise': outage_promise,
    'revocation-window': revocation_window,
    'dns-recovery': dns_recovery,
    'rootfs-write': rootfs_write,
    'completion-report': completion_report,
    'proof-consumption': proof_consumption,
    'withdrawal-consumption': withdrawal_consumption,
    'secret-refresh': secret_refresh,
    'rotation-stage': rotation_stage,
    'scoped-completion': scoped_completion,
    'incident-facts': incident_facts,
    'backup-scope': backup_scope,
    'retirement-resources': retirement_resources,
    'external-exit': external_exit,
}


def evaluate(name, observation):
    require(type(name) is str and name in ORACLES, 'unknown finite oracle')
    require(type(observation) is dict, 'observation object required')
    try:
        return ORACLES[name](**observation)
    except TypeError as exc:
        raise ContractError('observation fields do not match the finite oracle') from exc
