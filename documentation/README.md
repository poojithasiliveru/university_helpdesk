# University Helpdesk and Policy Assistant

## Overview

A web-based university support system for registering users, creating and tracking helpdesk tickets, exchanging ticket messages, assigning tickets to support teams, recording SLA deadlines, and searching published policy/knowledge-base content.

## Technology

- Backend: Python, Flask
- Database: MySQL
- Frontend: HTML, CSS, JavaScript, Bootstrap
- Authentication: JWT
- Database connector: MySQL Connector/Python

## Roles

Student, Instructor, Support Staff, Academic Admin, Platform Admin.

## Categories

Financial Aid, Registration, IT, Accessibility.

## Main Features

- Registration and login
- JWT-protected APIs and role-based access
- Ticket creation, listing, details, status updates, and history
- Ticket messages
- Support-team assignment
- SLA target and deadline records
- Policy and knowledge article search
- Anomaly labels and separate ground-truth evaluation records

## Project Structure

```text
University_Helpdesk/
├── backend/
├── database/
│   └── university_helpdesk_backup.sql
├── dataset/
│   ├── exports/
│   └── database_schema_report.csv
├── documentation/
├── evaluation/
├── frontend/
│   ├── templates/
│   └── static/
├── generator/
├── venv/
└── requirements.txt
```

## Setup

1. Install Python and MySQL.
2. Restore `database/university_helpdesk_backup.sql` into MySQL, if setting up a fresh database.
3. From the project root, create and activate a virtual environment:
   ```powershell
   python -m venv venv
   venv\Scripts\activate
   ```
4. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
5. Configure database credentials and application secrets in the backend configuration/environment files. Do not share real credentials.
6. Start the Flask app from the project root:
   ```powershell
   python backend/app.py
   ```
7. Open `http://127.0.0.1:5000/login` or `http://127.0.0.1:5000/register`.

## API Endpoints

| Feature        | Method and endpoint                     |
| -------------- | --------------------------------------- |
| Register       | `POST /api/auth/register`               |
| Login          | `POST /api/auth/login`                  |
| Health         | `GET /api/health`                       |
| Profile        | `GET /api/profile`                      |
| Create ticket  | `POST /api/tickets/`                    |
| My tickets     | `GET /api/tickets/my`                   |
| All tickets    | `GET /api/tickets/`                     |
| Ticket details | `GET /api/tickets/<ticket_id>`          |
| Update status  | `PATCH /api/tickets/<ticket_id>/status` |
| Ticket history | `GET /api/tickets/<ticket_id>/history`  |
| Messages       | `GET/POST /api/messages/<ticket_id>`    |
| Policy search  | `GET /api/policies/search?q=<keyword>`  |

Protected endpoints require a valid Bearer token and appropriate role permissions.

## Dataset and Evaluation

The project data generator is intended to use seed `20261022`. Dataset targets include 5,000 tickets, 20,000 messages, 200 knowledge articles, 40 policy documents, and 500 requesters. Actual final counts must be taken from the current database. Manual API test records may make totals larger than generated-data targets.

Five labelled anomaly categories:

1. Expired Policy Citation
2. Unauthorized Team Routing
3. Unsupported Response Claim
4. Business-Hours SLA Error
5. Missing Escalation

Ground-truth labels are stored separately from normal application input.

## Security and Submission Notes

- Never commit `.env` files, database passwords, JWT secrets, or plain-text passwords.
- Review exported data for personal information before sharing.
- Verify the SQL backup can be restored.
- Update this README if setup commands or endpoints change.
