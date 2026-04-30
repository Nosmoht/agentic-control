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
