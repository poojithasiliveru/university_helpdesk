# Data Dictionary

This document summarizes the main project entities. The live MySQL schema and `dataset/database_schema_report.csv` are authoritative for exact column names, types, keys, and constraints. Fields listed here are those confirmed during implementation; unlisted fields should be checked with `DESCRIBE table_name;`.

## requesters

Stores people using the helpdesk.

- `requester_id`: requester primary key.
- `role_id`: associated role.
- `name`: requester name.
- `email`: requester email.
- `created_at`: creation timestamp.
- `password_hash`: password hash, if present in the live schema. Never store plain-text passwords.

## roles

Stores application roles such as Student, Instructor, Support Staff, Academic Admin, and Platform Admin. Confirm exact columns with `DESCRIBE roles;`.

## terms

Stores academic terms and their active date ranges. Confirm exact columns with `DESCRIBE terms;`.

## categories

Stores ticket categories and authorized teams.

- `category_id`: category primary key.
- `category_name`: category name.
- `authorized_team`: team authorized to handle the category.

## tickets

Stores helpdesk requests.

- `ticket_id`: VARCHAR(30) primary key.
- `requester_id`: requester who created the ticket.
- `term_id`: associated academic term.
- `category_id`: ticket category.
- `subject`: short subject.
- `description`: request details.
- `priority`: Low, Normal, High, or Critical.
- `status`: Open, In Progress, Waiting, Escalated, Resolved, or Closed.
- `issue_type`: issue classification.
- `created_at`: creation timestamp.
- `updated_at`: last update timestamp.

## messages

Stores conversation messages for tickets.

- `message_id`: message identifier.
- `ticket_id`: related ticket.
- `sender_id`: sender identifier.
- `sender_type`: sender type/role.
- `message_text`: message content.
- `created_at`: message timestamp.

## policy_documents

Stores policy documents and their publication/effective-date information. Confirm exact columns with `DESCRIBE policy_documents;`.

## knowledge_articles

Stores knowledge-base articles linked to policy documents. `policy_id` is used to associate an article with a policy. Confirm remaining columns with `DESCRIBE knowledge_articles;`.

## assignments

Stores ticket assignment information.

- `assignment_id`: assignment record identifier.
- `ticket_id`: related ticket.
- `assigned_team`: assigned support team.
- `assigned_to`: assigned staff requester ID, where applicable.
- `assigned_at`: assignment timestamp.
- `assignment_reason`: reason for assignment.
- `assignment_status`: assignment state.

## sla

Stores service-level targets and deadlines.

- `sla_id`: SLA record identifier.
- `ticket_id`: related ticket.
- `response_target_minutes`: response target duration.
- `resolution_target_minutes`: resolution target duration.
- `response_deadline`: response deadline.
- `resolution_deadline`: resolution deadline.
- `business_hours_only`: whether business hours apply.
- `response_breached`: response breach indicator.
- `resolution_breached`: resolution breach indicator.

## ticket_events

Stores ticket lifecycle/audit history.

- `event_id`: event identifier.
- `ticket_id`: related ticket.
- `event_type`: event type.
- `old_value`: previous value, where applicable.
- `new_value`: new value, where applicable.
- `event_description`: event details.
- `actor_id`: actor identifier.
- `created_at`: event timestamp.

## resolution_feedback

Stores feedback about ticket resolutions. Confirm exact columns with `DESCRIBE resolution_feedback;`.

## anomaly_labels

Stores labelled anomaly examples.

- `anomaly_id`: anomaly label primary key.
- `ticket_id`: associated ticket.
- `anomaly_type`: anomaly category.
- `description`: anomaly explanation.
- `source_table`: table where the anomaly is observed.
- `created_at`: label creation timestamp.

## ground_truth

Stores expected evaluation labels separately from normal application input.

- `ground_truth_id`: ground-truth primary key.
- `ticket_id`: associated ticket.
- `anomaly_type`: expected anomaly category.
- `expected_issue`: expected issue description.
- `source_table`: table containing the issue.

## Main Relationships

- One role can be associated with many requesters.
- One requester can create many tickets.
- One term and one category can be associated with many tickets.
- One ticket can have multiple messages, assignments, and events.
- A ticket can have an SLA record.
- Policy documents can be linked to knowledge articles.
- Anomaly labels and ground-truth records reference tickets.

## Schema Verification

Run `SHOW TABLES;` and `DESCRIBE <table_name>;` in MySQL to confirm the current schema before treating this document as a complete column-level specification.
