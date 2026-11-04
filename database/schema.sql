CREATE DATABASE university_helpdesk;

USE university_helpdesk;
#roles
CREATE TABLE roles (
    role_id INT AUTO_INCREMENT PRIMARY KEY,
    role_name VARCHAR(50) NOT NULL UNIQUE,
    description VARCHAR(255)
);
#requesters
CREATE TABLE requesters (
    requester_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(150) NOT NULL UNIQUE,
    role_id INT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (role_id)
    REFERENCES roles(role_id)
);
#terms
CREATE TABLE terms (
    term_id INT AUTO_INCREMENT PRIMARY KEY,
    term_name VARCHAR(50) NOT NULL UNIQUE,
    start_date DATE NOT NULL,
    end_date DATE NOT NULL,

    CHECK (end_date > start_date)
);
#categories
CREATE TABLE categories (
    category_id INT AUTO_INCREMENT PRIMARY KEY,
    category_name VARCHAR(50) NOT NULL UNIQUE,
    authorized_team VARCHAR(100) NOT NULL,
    description VARCHAR(255)
);
#policy_documents
CREATE TABLE policy_documents (
    policy_id VARCHAR(60) PRIMARY KEY,
    domain VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    version INT NOT NULL,
    effective_from DATE NOT NULL,
    effective_to DATE NULL,
    policy_content TEXT NOT NULL,
    status ENUM('Draft', 'Published', 'Expired', 'Archived')
        DEFAULT 'Draft',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    UNIQUE (domain, version),
    CHECK (effective_to IS NULL OR effective_to >= effective_from),
    CHECK (version > 0)
);
#knowledge_articles
CREATE TABLE knowledge_articles (
    article_id VARCHAR(20) PRIMARY KEY,
    policy_id VARCHAR(60) NOT NULL,
    title VARCHAR(200) NOT NULL,
    content TEXT NOT NULL,
    version INT NOT NULL,
    effective_from DATE NOT NULL,
    effective_to DATE NULL,
    status ENUM('Draft', 'Published', 'Expired', 'Archived')
        DEFAULT 'Draft',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (policy_id)
    REFERENCES policy_documents(policy_id),

    UNIQUE (policy_id, version),
    CHECK (version > 0),
    CHECK (effective_to IS NULL OR effective_to >= effective_from)
);
#tickets
CREATE TABLE tickets (
    ticket_id VARCHAR(30) PRIMARY KEY,
    requester_id INT NOT NULL,
    term_id INT NOT NULL,
    category_id INT NOT NULL,

    subject VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,

    priority ENUM('Low', 'Normal', 'High', 'Critical')
        DEFAULT 'Normal',

    status ENUM(
        'Open',
        'In Progress',
        'Waiting',
        'Escalated',
        'Resolved',
        'Closed'
    ) DEFAULT 'Open',

    issue_type VARCHAR(50) DEFAULT 'normal',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (requester_id)
        REFERENCES requesters(requester_id),

    FOREIGN KEY (term_id)
        REFERENCES terms(term_id),

    FOREIGN KEY (category_id)
        REFERENCES categories(category_id),

    INDEX idx_ticket_requester (requester_id),
    INDEX idx_ticket_category (category_id),
    INDEX idx_ticket_status (status),
    INDEX idx_ticket_created (created_at)
);

#messages
CREATE TABLE messages (
    message_id VARCHAR(60) PRIMARY KEY,
    ticket_id VARCHAR(30) NOT NULL,
    sender_id INT NOT NULL,

    sender_type ENUM(
        'Student',
        'Instructor',
        'Admin',
        'Support',
        'System'
    ) NOT NULL,

    message_text TEXT NOT NULL,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ticket_id)
        REFERENCES tickets(ticket_id),

    FOREIGN KEY (sender_id)
        REFERENCES requesters(requester_id),

    INDEX idx_message_ticket (ticket_id)
);
#assignments
CREATE TABLE assignments (
    assignment_id INT AUTO_INCREMENT PRIMARY KEY,
    ticket_id VARCHAR(30) NOT NULL,
    assigned_team VARCHAR(100) NOT NULL,
    assigned_to INT NULL,

    assigned_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    assignment_reason VARCHAR(255),

    assignment_status ENUM(
        'Active',
        'Reassigned',
        'Completed'
    ) DEFAULT 'Active',

    FOREIGN KEY (ticket_id)
        REFERENCES tickets(ticket_id),

    FOREIGN KEY (assigned_to)
        REFERENCES requesters(requester_id),

    INDEX idx_assignment_ticket (ticket_id)
);
#sla
CREATE TABLE sla (
    sla_id VARCHAR(50) PRIMARY KEY,
    ticket_id VARCHAR(30) NOT NULL UNIQUE,

    response_target_minutes INT NOT NULL,
    resolution_target_minutes INT NOT NULL,

    response_deadline DATETIME NOT NULL,
    resolution_deadline DATETIME NOT NULL,

    business_hours_only BOOLEAN DEFAULT TRUE,

    response_breached BOOLEAN DEFAULT FALSE,
    resolution_breached BOOLEAN DEFAULT FALSE,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ticket_id)
        REFERENCES tickets(ticket_id),

    CHECK (response_target_minutes > 0),
    CHECK (resolution_target_minutes > 0)
);
#ticket_articles
CREATE TABLE ticket_articles (
    ticket_id VARCHAR(30) NOT NULL,
    article_id VARCHAR(20) NOT NULL,

    citation_type ENUM(
        'Retrieved',
        'Used',
        'Rejected'
    ) DEFAULT 'Retrieved',

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    PRIMARY KEY (ticket_id, article_id),

    FOREIGN KEY (ticket_id)
        REFERENCES tickets(ticket_id),

    FOREIGN KEY (article_id)
        REFERENCES knowledge_articles(article_id)
);
#message_sources
CREATE TABLE message_sources (
    message_id VARCHAR(60) NOT NULL,
    article_id VARCHAR(20) NOT NULL,

    citation_note VARCHAR(255),

    PRIMARY KEY (message_id, article_id),

    FOREIGN KEY (message_id)
        REFERENCES messages(message_id),

    FOREIGN KEY (article_id)
        REFERENCES knowledge_articles(article_id)
);
#ticket_events
CREATE TABLE ticket_events (
    event_id BIGINT AUTO_INCREMENT PRIMARY KEY,

    ticket_id VARCHAR(30) NOT NULL,

    event_type VARCHAR(50) NOT NULL,

    old_value VARCHAR(100),
    new_value VARCHAR(100),

    event_description TEXT,

    actor_id INT NULL,

    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (ticket_id)
        REFERENCES tickets(ticket_id),

    FOREIGN KEY (actor_id)
        REFERENCES requesters(requester_id),

    INDEX idx_event_ticket (ticket_id)
);
#routing_rules
CREATE TABLE routing_rules (
    rule_id INT AUTO_INCREMENT PRIMARY KEY,

    category_id INT NOT NULL,

    keyword VARCHAR(100) NOT NULL,

    authorized_team VARCHAR(100) NOT NULL,

    priority ENUM(
        'Low',
        'Normal',
        'High',
        'Critical'
    ) DEFAULT 'Normal',

    is_active BOOLEAN DEFAULT TRUE,

    FOREIGN KEY (category_id)
        REFERENCES categories(category_id),

    UNIQUE (category_id, keyword)
);
#sla_rules
CREATE TABLE sla_rules (
    rule_id INT AUTO_INCREMENT PRIMARY KEY,

    category_id INT NOT NULL,

    priority ENUM(
        'Low',
        'Normal',
        'High',
        'Critical'
    ) NOT NULL,

    response_target_minutes INT NOT NULL,

    resolution_target_minutes INT NOT NULL,

    business_hours_only BOOLEAN DEFAULT TRUE,

    UNIQUE (category_id, priority),

    FOREIGN KEY (category_id)
        REFERENCES categories(category_id),

    CHECK (response_target_minutes > 0),
    CHECK (resolution_target_minutes > 0)
);
#insert roles
INSERT INTO roles (role_name, description)
VALUES
('Student', 'University student'),
('Instructor', 'Teaching faculty'),
('Academic Admin', 'Academic administrator'),
('Support Staff', 'Helpdesk support employee'),
('Platform Admin', 'System administrator');

#Insert categories
INSERT INTO categories (category_name, authorized_team, description)
VALUES
('Financial Aid', 'Financial Aid Team', 'Scholarships and financial assistance'),
('Registration', 'Registrar Team', 'Course and semester registration'),
('IT', 'IT Support Team', 'Technical issues and account access'),
('Accessibility', 'Accessibility Support Team', 'Accessibility and accommodation requests');

#Insert academic terms
INSERT INTO terms (term_name, start_date, end_date)
VALUES
('Fall 2026', '2026-08-01', '2026-12-31'),
('Spring 2027', '2027-01-01', '2027-05-31'),
('Summer 2027', '2027-06-01', '2027-07-31');

#Insert routing rules
INSERT INTO routing_rules
(category_id, keyword, authorized_team, priority)
VALUES
(1, 'scholarship', 'Financial Aid Team', 'Normal'),
(1, 'grant', 'Financial Aid Team', 'Normal'),
(1, 'financial aid', 'Financial Aid Team', 'High'),

(2, 'registration', 'Registrar Team', 'Normal'),
(2, 'enrollment', 'Registrar Team', 'Normal'),

(3, 'password', 'IT Support Team', 'Normal'),
(3, 'login', 'IT Support Team', 'High'),
(3, 'wifi', 'IT Support Team', 'Normal'),

(4, 'accessibility', 'Accessibility Support Team', 'High'),
(4, 'accommodation', 'Accessibility Support Team', 'High');

#Insert SLA rules
INSERT INTO sla_rules
(category_id, priority,
 response_target_minutes,
 resolution_target_minutes,
 business_hours_only)
VALUES
(1, 'Critical', 15, 240, TRUE),
(1, 'High', 30, 480, TRUE),
(1, 'Normal', 240, 1440, TRUE),
(1, 'Low', 480, 2880, TRUE),

(2, 'Critical', 15, 240, TRUE),
(2, 'High', 30, 480, TRUE),
(2, 'Normal', 240, 1440, TRUE),
(2, 'Low', 480, 2880, TRUE),

(3, 'Critical', 15, 240, TRUE),
(3, 'High', 30, 480, TRUE),
(3, 'Normal', 240, 1440, TRUE),
(3, 'Low', 480, 2880, TRUE),

(4, 'Critical', 15, 240, TRUE),
(4, 'High', 30, 480, TRUE),
(4, 'Normal', 240, 1440, TRUE),
(4, 'Low', 480, 2880, TRUE);

#Insert sample requesters
INSERT INTO requesters (name, email, role_id)
VALUES
('Student One', 'student1@example.com', 1),
('Student Two', 'student2@example.com', 1),
('Faculty One', 'faculty1@example.com', 2),
('Academic Admin', 'admin@example.com', 3),
('Support Staff', 'support@example.com', 4),
('Platform Admin', 'platform@example.com', 5);

#Insert a sample policy document
INSERT INTO policy_documents
(policy_id, domain, title, version,
 effective_from, effective_to,
 policy_content, status)
VALUES
(
'POL-financial_aid-2026-001',
'Financial Aid',
'Financial Aid Policy',
1,
'2026-08-01',
NULL,
'Students must submit financial aid applications before the published deadline.',
'Published'
);

#Insert a sample knowledge article
INSERT INTO knowledge_articles
(article_id, policy_id, title, content,
 version, effective_from, effective_to, status)
VALUES
(
'KB-000001',
'POL-financial_aid-2026-001',
'How to Apply for Financial Aid',
'Students must submit financial aid applications before the published deadline.',
1,
'2026-08-01',
NULL,
'Published'
);

ALTER TABLE messages
MODIFY sender_id INT NULL;

SHOW TABLES;

SELECT * FROM requesters;
SELECT * FROM categories;
SELECT * FROM knowledge_articles;
SHOW CREATE TABLE tickets;
SELECT
    t.ticket_id,
    r.name AS requester_name,
    ro.role_name,
    c.category_name,
    t.subject,
    t.priority,
    t.status

FROM tickets t

JOIN requesters r
    ON t.requester_id = r.requester_id

JOIN roles ro
    ON r.role_id = ro.role_id

JOIN categories c
    ON t.category_id = c.category_id;
    