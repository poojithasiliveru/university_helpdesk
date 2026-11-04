# Source Manifest

## Project

University Helpdesk and Policy Assistant

## Project Data and Source Inventory

| Source/location                           | Description                              | Purpose                             |
| ----------------------------------------- | ---------------------------------------- | ----------------------------------- |
| `backend/`                                | Flask application modules and API routes | Application logic                   |
| `frontend/`                               | HTML templates, CSS, and JavaScript      | User interface                      |
| `database/university_helpdesk_backup.sql` | MySQL backup                             | Database restoration                |
| `generator/`                              | Data-generation scripts                  | Reproducible sample-data generation |
| `dataset/exports/`                        | CSV and JSON exports                     | Review and evaluation               |
| `dataset/database_schema_report.csv`      | Database schema report                   | Table/column reference              |
| MySQL project database                    | Relational application data              | Runtime storage and validation      |
| `anomaly_labels`                          | Labelled anomaly examples                | Anomaly evaluation                  |
| `ground_truth`                            | Separate expected evaluation labels      | Evaluation reference                |

## Generation Configuration

- Intended deterministic seed: `20261022`.
- Use the scripts in `generator/` to regenerate generated records.
- For reproducibility, record the exact script/command, run date, Python version, and installed dependency versions.
- Keep manually created API test records distinguishable from generated records when reporting counts.

## Labelled Anomaly Categories

1. Expired Policy Citation
2. Unauthorized Team Routing
3. Unsupported Response Claim
4. Business-Hours SLA Error
5. Missing Escalation

## Expected Export Inventory

Check the actual `dataset/exports/` directory. Useful exports include:

- requesters
- roles
- terms
- categories
- tickets
- messages
- policy_documents
- knowledge_articles
- assignments
- sla
- ticket_events
- resolution_feedback
- anomaly_labels
- ground_truth

CSV and JSON availability may differ by table. Do not claim an export exists until it is present and current.

## Data Handling

- Do not publish `.env` values, database passwords, JWT secrets, or plain-text passwords.
- Review exports for personal information before sharing.
- Keep ground-truth labels separate from normal application input.
- Document manual data corrections and test records in the validation report.
