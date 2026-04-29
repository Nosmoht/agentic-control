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
