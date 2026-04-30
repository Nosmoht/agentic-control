CREATE TABLE project (
	id TEXT(36) NOT NULL, 
	title TEXT NOT NULL, 
	state TEXT DEFAULT 'idea' NOT NULL, 
	created_at TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	provider_binding TEXT, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_project_id_uuid_length CHECK (LENGTH(id) = 36), 
	CONSTRAINT ck_project_title_nonempty CHECK (LENGTH(title) >= 1), 
	CONSTRAINT ck_project_state_enum CHECK (state IN ('idea', 'candidate', 'active', 'dormant', 'archived'))
);
CREATE TABLE work_item (
	id TEXT(36) NOT NULL, 
	project_ref TEXT(36) NOT NULL, 
	title TEXT NOT NULL, 
	state TEXT DEFAULT 'proposed' NOT NULL, 
	priority TEXT DEFAULT 'med' NOT NULL, 
	plan_ref TEXT(36), 
	created_at TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT fk_work_item_project FOREIGN KEY(project_ref) REFERENCES project (id) ON DELETE RESTRICT, 
	CONSTRAINT ck_work_item_id_uuid_length CHECK (LENGTH(id) = 36), 
	CONSTRAINT ck_work_item_project_ref_uuid_length CHECK (LENGTH(project_ref) = 36), 
	CONSTRAINT ck_work_item_title_nonempty CHECK (LENGTH(title) >= 1), 
	CONSTRAINT ck_work_item_state_enum CHECK (state IN ('proposed', 'accepted', 'planned', 'ready', 'in_progress', 'waiting', 'blocked', 'completed', 'abandoned')), 
	CONSTRAINT ck_work_item_priority_enum CHECK (priority IN ('low', 'med', 'high'))
);
CREATE INDEX ix_work_item_project_ref ON work_item (project_ref);
CREATE INDEX ix_work_item_state ON work_item (state);
CREATE TABLE observation (
	id TEXT(36) NOT NULL, 
	source_ref TEXT(36), 
	body TEXT NOT NULL, 
	classification TEXT, 
	captured_at TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_observation_id_uuid_length CHECK (LENGTH(id) = 36), 
	CONSTRAINT ck_observation_body_nonempty CHECK (LENGTH(body) >= 1), 
	CONSTRAINT ck_observation_source_ref_uuid_length CHECK (source_ref IS NULL OR LENGTH(source_ref) = 36)
);
CREATE INDEX ix_observation_source_ref ON observation (source_ref);
CREATE TABLE decision (
	id TEXT(36) NOT NULL, 
	subject_ref TEXT(36) NOT NULL, 
	context TEXT NOT NULL, 
	decision TEXT NOT NULL, 
	consequence TEXT NOT NULL, 
	state TEXT DEFAULT 'proposed' NOT NULL, 
	created_at TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT fk_decision_subject FOREIGN KEY(subject_ref) REFERENCES work_item (id) ON DELETE RESTRICT, 
	CONSTRAINT ck_decision_id_uuid_length CHECK (LENGTH(id) = 36), 
	CONSTRAINT ck_decision_subject_ref_uuid_length CHECK (LENGTH(subject_ref) = 36), 
	CONSTRAINT ck_decision_context_nonempty CHECK (LENGTH(context) >= 1), 
	CONSTRAINT ck_decision_decision_nonempty CHECK (LENGTH(decision) >= 1), 
	CONSTRAINT ck_decision_consequence_nonempty CHECK (LENGTH(consequence) >= 1), 
	CONSTRAINT ck_decision_state_enum CHECK (state IN ('proposed', 'accepted', 'superseded', 'rejected'))
);
CREATE INDEX ix_decision_subject_ref ON decision (subject_ref);
CREATE TABLE run (
	id TEXT(36) NOT NULL, 
	work_item_ref TEXT(36) NOT NULL, 
	agent TEXT NOT NULL, 
	state TEXT DEFAULT 'created' NOT NULL, 
	budget_cap NUMERIC NOT NULL, 
	result_ref TEXT, 
	created_at TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT fk_run_work_item FOREIGN KEY(work_item_ref) REFERENCES work_item (id) ON DELETE RESTRICT, 
	CONSTRAINT ck_run_id_uuid_length CHECK (LENGTH(id) = 36), 
	CONSTRAINT ck_run_work_item_ref_uuid_length CHECK (LENGTH(work_item_ref) = 36), 
	CONSTRAINT ck_run_agent_nonempty CHECK (LENGTH(agent) >= 1), 
	CONSTRAINT ck_run_budget_cap_nonneg CHECK (budget_cap >= 0), 
	CONSTRAINT ck_run_state_enum CHECK (state IN ('created', 'running', 'paused', 'waiting', 'retrying', 'needs_reconciliation', 'completed', 'failed', 'aborted'))
);
CREATE INDEX ix_run_work_item_ref ON run (work_item_ref);
CREATE INDEX ix_run_state ON run (state);
CREATE TABLE artifact (
	id TEXT(36) NOT NULL, 
	origin_run_ref TEXT(36) NOT NULL, 
	kind TEXT NOT NULL, 
	path_or_ref TEXT NOT NULL, 
	provenance TEXT NOT NULL, 
	state TEXT DEFAULT 'registered' NOT NULL, 
	created_at TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT fk_artifact_origin_run FOREIGN KEY(origin_run_ref) REFERENCES run (id) ON DELETE RESTRICT, 
	CONSTRAINT ck_artifact_id_uuid_length CHECK (LENGTH(id) = 36), 
	CONSTRAINT ck_artifact_origin_run_ref_uuid_length CHECK (LENGTH(origin_run_ref) = 36), 
	CONSTRAINT ck_artifact_kind_nonempty CHECK (LENGTH(kind) >= 1), 
	CONSTRAINT ck_artifact_path_or_ref_nonempty CHECK (LENGTH(path_or_ref) >= 1), 
	CONSTRAINT ck_artifact_provenance_nonempty CHECK (LENGTH(provenance) >= 1), 
	CONSTRAINT ck_artifact_state_enum CHECK (state IN ('registered', 'available', 'consumed', 'superseded', 'archived'))
);
CREATE INDEX ix_artifact_origin_run_ref ON artifact (origin_run_ref);
CREATE INDEX ix_artifact_state ON artifact (state);
CREATE TABLE evidence (
	id TEXT(36) NOT NULL, 
	subject_ref TEXT NOT NULL, 
	kind TEXT NOT NULL, 
	source_ref TEXT(36), 
	captured_at TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	jsonl_blob_ref TEXT, 
	PRIMARY KEY (id), 
	CONSTRAINT ck_evidence_id_uuid_length CHECK (LENGTH(id) = 36), 
	CONSTRAINT ck_evidence_kind_nonempty CHECK (LENGTH(kind) >= 1), 
	CONSTRAINT ck_evidence_source_ref_uuid_length CHECK (source_ref IS NULL OR LENGTH(source_ref) = 36), 
	CONSTRAINT ck_evidence_subject_ref_prefix CHECK (subject_ref LIKE 'work_item:%' OR subject_ref LIKE 'run:%' OR subject_ref LIKE 'artifact:%' OR subject_ref LIKE 'decision:%'), 
	CONSTRAINT ck_evidence_subject_ref_format CHECK ((subject_ref LIKE 'work_item:%' AND LENGTH(subject_ref) = 46) OR (subject_ref LIKE 'run:%' AND LENGTH(subject_ref) = 40) OR (subject_ref LIKE 'artifact:%' AND LENGTH(subject_ref) = 45) OR (subject_ref LIKE 'decision:%' AND LENGTH(subject_ref) = 45))
);
CREATE INDEX ix_evidence_subject_ref ON evidence (subject_ref);
CREATE INDEX ix_evidence_kind ON evidence (kind);
CREATE TABLE run_attempt (
	id TEXT(36) NOT NULL, 
	run_ref TEXT(36) NOT NULL, 
	attempt_ordinal INTEGER NOT NULL, 
	agent TEXT NOT NULL, 
	model TEXT NOT NULL, 
	sandbox_profile TEXT NOT NULL, 
	prompt_hash TEXT(12) NOT NULL, 
	tool_allowlist TEXT DEFAULT '[]' NOT NULL, 
	logs_ref TEXT NOT NULL, 
	started_at TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	ended_at TEXT, 
	exit_code INTEGER, 
	PRIMARY KEY (id), 
	CONSTRAINT fk_run_attempt_run FOREIGN KEY(run_ref) REFERENCES run (id) ON DELETE RESTRICT, 
	CONSTRAINT uq_run_attempt_ordinal UNIQUE (run_ref, attempt_ordinal), 
	CONSTRAINT ck_run_attempt_id_uuid_length CHECK (LENGTH(id) = 36), 
	CONSTRAINT ck_run_attempt_run_ref_uuid_length CHECK (LENGTH(run_ref) = 36), 
	CONSTRAINT ck_run_attempt_ordinal_positive CHECK (attempt_ordinal >= 1), 
	CONSTRAINT ck_run_attempt_prompt_hash_length CHECK (LENGTH(prompt_hash) = 12), 
	CONSTRAINT ck_run_attempt_tool_allowlist_json CHECK (json_valid(tool_allowlist))
);
CREATE INDEX ix_run_attempt_run_ref ON run_attempt (run_ref);
CREATE INDEX ix_run_attempt_started_at ON run_attempt (started_at);
CREATE TABLE approval_request (
	id TEXT(36) NOT NULL, 
	subject_ref TEXT(36) NOT NULL, 
	risk_class TEXT NOT NULL, 
	question TEXT NOT NULL, 
	state TEXT DEFAULT 'waiting_for_approval' NOT NULL, 
	decider TEXT, 
	created_at TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	decided_at TEXT, 
	deadline TEXT, 
	run_attempt_ref TEXT(36), 
	PRIMARY KEY (id), 
	CONSTRAINT fk_approval_request_subject FOREIGN KEY(subject_ref) REFERENCES work_item (id) ON DELETE RESTRICT, 
	CONSTRAINT fk_approval_request_run_attempt FOREIGN KEY(run_attempt_ref) REFERENCES run_attempt (id) ON DELETE RESTRICT, 
	CONSTRAINT ck_approval_request_id_uuid_length CHECK (LENGTH(id) = 36), 
	CONSTRAINT ck_approval_request_subject_ref_uuid_length CHECK (LENGTH(subject_ref) = 36), 
	CONSTRAINT ck_approval_request_question_nonempty CHECK (LENGTH(question) >= 1), 
	CONSTRAINT ck_approval_request_risk_class_enum CHECK (risk_class IN ('low', 'medium', 'high', 'irreversible')), 
	CONSTRAINT ck_approval_request_state_enum CHECK (state IN ('waiting_for_approval', 'approved', 'rejected', 'timed_out_rejected', 'stale_waiting', 'abandoned'))
);
CREATE INDEX ix_approval_request_subject_ref ON approval_request (subject_ref);
CREATE INDEX ix_approval_request_state ON approval_request (state);
CREATE TABLE budget_ledger_entry (
	id TEXT(36) NOT NULL, 
	ts TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	scope TEXT NOT NULL, 
	run_attempt_ref TEXT(36) NOT NULL, 
	run_attempt_hash_anchor TEXT NOT NULL, 
	project_ref TEXT(36), 
	model TEXT NOT NULL, 
	pre_call_projection_usd NUMERIC NOT NULL, 
	actual_usd NUMERIC, 
	cache_hit INTEGER DEFAULT 0 NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT fk_budget_run_attempt FOREIGN KEY(run_attempt_ref) REFERENCES run_attempt (id) ON DELETE RESTRICT, 
	CONSTRAINT fk_budget_project FOREIGN KEY(project_ref) REFERENCES project (id) ON DELETE RESTRICT, 
	CONSTRAINT ck_budget_id_uuid_length CHECK (LENGTH(id) = 36), 
	CONSTRAINT ck_budget_run_attempt_ref_uuid_length CHECK (LENGTH(run_attempt_ref) = 36), 
	CONSTRAINT ck_budget_scope_enum CHECK (scope IN ('request', 'task', 'project_day', 'global_day')), 
	CONSTRAINT ck_budget_pre_call_projection_nonneg CHECK (pre_call_projection_usd >= 0), 
	CONSTRAINT ck_budget_actual_nonneg CHECK (actual_usd IS NULL OR actual_usd >= 0), 
	CONSTRAINT ck_budget_cache_hit_bool CHECK (cache_hit IN (0, 1)), 
	CONSTRAINT ck_budget_hash_anchor_length CHECK (LENGTH(run_attempt_hash_anchor) BETWEEN 12 AND 64)
);
CREATE INDEX ix_budget_run_attempt_ref ON budget_ledger_entry (run_attempt_ref);
CREATE INDEX ix_budget_ts ON budget_ledger_entry (ts);
CREATE INDEX ix_budget_scope_ts ON budget_ledger_entry (scope, ts);
CREATE TABLE tool_call_record (
	id TEXT(36) NOT NULL, 
	run_attempt_ref TEXT(36) NOT NULL, 
	tool_call_ordinal INTEGER NOT NULL, 
	tool_name TEXT NOT NULL, 
	input_hash TEXT(12) NOT NULL, 
	output_ref TEXT, 
	duration_ms INTEGER, 
	exit_code INTEGER, 
	idempotency_key TEXT, 
	effect_class TEXT NOT NULL, 
	started_at TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	ended_at TEXT, 
	PRIMARY KEY (id), 
	CONSTRAINT fk_tool_call_run_attempt FOREIGN KEY(run_attempt_ref) REFERENCES run_attempt (id) ON DELETE RESTRICT, 
	CONSTRAINT uq_tool_call_ordinal UNIQUE (run_attempt_ref, tool_call_ordinal), 
	CONSTRAINT ck_tool_call_id_uuid_length CHECK (LENGTH(id) = 36), 
	CONSTRAINT ck_tool_call_run_attempt_ref_uuid_length CHECK (LENGTH(run_attempt_ref) = 36), 
	CONSTRAINT ck_tool_call_ordinal_positive CHECK (tool_call_ordinal >= 1), 
	CONSTRAINT ck_tool_call_tool_name_nonempty CHECK (LENGTH(tool_name) >= 1), 
	CONSTRAINT ck_tool_call_input_hash_length CHECK (LENGTH(input_hash) = 12), 
	CONSTRAINT ck_tool_call_duration_nonneg CHECK (duration_ms IS NULL OR duration_ms >= 0), 
	CONSTRAINT ck_tool_call_idempotency_key_nonempty CHECK (idempotency_key IS NULL OR LENGTH(idempotency_key) >= 1), 
	CONSTRAINT ck_tool_call_effect_class_enum CHECK (effect_class IN ('natural', 'provider_keyed', 'local_only'))
);
CREATE INDEX ix_tool_call_run_attempt_effect ON tool_call_record (run_attempt_ref, effect_class);
CREATE UNIQUE INDEX uq_tool_call_idempotency_key ON tool_call_record (run_attempt_ref, idempotency_key) WHERE idempotency_key IS NOT NULL;
CREATE TABLE policy_decision (
	id TEXT(36) NOT NULL, 
	ts TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	policy TEXT NOT NULL, 
	subject_ref TEXT NOT NULL, 
	inputs TEXT DEFAULT '{}' NOT NULL, 
	output TEXT DEFAULT '{}' NOT NULL, 
	run_attempt_ref TEXT(36), 
	PRIMARY KEY (id), 
	CONSTRAINT fk_policy_decision_run_attempt FOREIGN KEY(run_attempt_ref) REFERENCES run_attempt (id) ON DELETE RESTRICT, 
	CONSTRAINT ck_policy_decision_id_uuid_length CHECK (LENGTH(id) = 36), 
	CONSTRAINT ck_policy_decision_policy_enum CHECK (policy IN ('admission', 'dispatch', 'budget_gate_override', 'hitl_trigger', 'tool_risk_match')), 
	CONSTRAINT ck_policy_decision_subject_ref_nonempty CHECK (LENGTH(subject_ref) >= 1), 
	CONSTRAINT ck_policy_decision_inputs_json CHECK (json_valid(inputs)), 
	CONSTRAINT ck_policy_decision_output_json CHECK (json_valid(output))
);
CREATE INDEX ix_policy_decision_run_attempt_policy ON policy_decision (run_attempt_ref, policy);
CREATE INDEX ix_policy_decision_subject_ref ON policy_decision (subject_ref);
CREATE TABLE sandbox_violation (
	id TEXT(36) NOT NULL, 
	run_attempt_ref TEXT(36) NOT NULL, 
	ts TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	category TEXT NOT NULL, 
	detail TEXT DEFAULT '{}' NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT fk_sandbox_violation_run_attempt FOREIGN KEY(run_attempt_ref) REFERENCES run_attempt (id) ON DELETE RESTRICT, 
	CONSTRAINT ck_sandbox_violation_id_uuid_length CHECK (LENGTH(id) = 36), 
	CONSTRAINT ck_sandbox_violation_category_nonempty CHECK (LENGTH(category) >= 1), 
	CONSTRAINT ck_sandbox_violation_detail_json CHECK (json_valid(detail))
);
CREATE INDEX ix_sandbox_violation_run_attempt_ts ON sandbox_violation (run_attempt_ref, ts);
CREATE TABLE dispatch_decision (
	id TEXT(36) NOT NULL, 
	run_attempt_ref TEXT(36) NOT NULL, 
	adapter TEXT NOT NULL, 
	model TEXT NOT NULL, 
	mode TEXT NOT NULL, 
	reason TEXT NOT NULL, 
	evidence_refs TEXT, 
	decided_at TEXT DEFAULT CURRENT_TIMESTAMP NOT NULL, 
	PRIMARY KEY (id), 
	CONSTRAINT fk_dispatch_decision_run_attempt FOREIGN KEY(run_attempt_ref) REFERENCES run_attempt (id) ON DELETE RESTRICT, 
	CONSTRAINT ck_dispatch_decision_id_uuid_length CHECK (LENGTH(id) = 36), 
	CONSTRAINT ck_dispatch_decision_run_attempt_ref_uuid_length CHECK (LENGTH(run_attempt_ref) = 36), 
	CONSTRAINT ck_dispatch_decision_adapter_enum CHECK (adapter IN ('claude_code', 'codex_cli')), 
	CONSTRAINT ck_dispatch_decision_mode_enum CHECK (mode IN ('pinned', 'cost_aware')), 
	CONSTRAINT ck_dispatch_decision_reason_enum CHECK (reason IN ('pin', 'default', 'cost_aware_routing')), 
	CONSTRAINT ck_dispatch_decision_evidence_refs_json CHECK (evidence_refs IS NULL OR json_valid(evidence_refs)), 
	UNIQUE (run_attempt_ref)
);
CREATE TABLE IF NOT EXISTS "audit_event" (
	id TEXT(36) NOT NULL, 
	ts TEXT DEFAULT (CURRENT_TIMESTAMP) NOT NULL, 
	actor TEXT NOT NULL, 
	subject_ref TEXT NOT NULL, 
	event_type TEXT NOT NULL, 
	before_hash TEXT(64), 
	after_hash TEXT(64), 
	before_value TEXT, 
	after_value TEXT, 
	reason TEXT, 
	run_attempt_ref TEXT(36), 
	PRIMARY KEY (id), 
	CONSTRAINT ck_audit_event_before_hash_length CHECK (before_hash IS NULL OR LENGTH(before_hash) = 64), 
	CONSTRAINT fk_audit_event_run_attempt FOREIGN KEY(run_attempt_ref) REFERENCES run_attempt (id) ON DELETE RESTRICT, 
	CONSTRAINT ck_audit_event_after_hash_length CHECK (after_hash IS NULL OR LENGTH(after_hash) = 64), 
	CONSTRAINT ck_audit_event_actor_nonempty CHECK (LENGTH(actor) >= 1), 
	CONSTRAINT ck_audit_event_type_enum CHECK (event_type IN ('state_transition', 'config_write', 'reconcile_decision', 'lifecycle_change')), 
	CONSTRAINT ck_audit_event_id_uuid_length CHECK (LENGTH(id) = 36), 
	CONSTRAINT ck_audit_event_subject_ref_prefix CHECK (subject_ref LIKE 'work_item:%' OR subject_ref LIKE 'run:%' OR subject_ref LIKE 'run_attempt:%' OR subject_ref LIKE 'tool_call_record:%' OR subject_ref LIKE 'decision:%' OR subject_ref LIKE 'config/%'), 
	CONSTRAINT ck_audit_event_subject_ref_format CHECK ((subject_ref LIKE 'work_item:%' AND LENGTH(subject_ref) = 46) OR (subject_ref LIKE 'run:%' AND LENGTH(subject_ref) = 40) OR (subject_ref LIKE 'run_attempt:%' AND LENGTH(subject_ref) = 48) OR (subject_ref LIKE 'tool_call_record:%' AND LENGTH(subject_ref) = 53) OR (subject_ref LIKE 'decision:%' AND LENGTH(subject_ref) = 45) OR (subject_ref LIKE 'config/%' AND LENGTH(subject_ref) >= 8))
);
CREATE INDEX ix_audit_event_subject_ref ON audit_event (subject_ref, ts);
CREATE INDEX ix_audit_event_run_attempt_ref ON audit_event (run_attempt_ref);
