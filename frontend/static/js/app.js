
const API = "http://127.0.0.1:5000";


// LOGIN
const loginForm = document.getElementById("loginForm");

if (loginForm) {
    loginForm.addEventListener("submit", async function (e) {
        e.preventDefault();

        const response = await fetch(API + "/api/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                email: document.getElementById("email").value,
                password: document.getElementById("password").value
            })
        });

        const data = await response.json();

        document.getElementById("message").innerText = data.message;

        if (response.ok) {
            localStorage.setItem("token", data.token);
            localStorage.setItem("role", data.user.role);

            if (data.user.role === "Student" ||
                data.user.role === "Instructor") {
                window.location.href = "/student-dashboard";
            } else {
                window.location.href = "/support-dashboard";
            }
        }
    });
}


// REGISTER
const registerForm = document.getElementById("registerForm");

if (registerForm) {
    registerForm.addEventListener("submit", async function (e) {
        e.preventDefault();

        const response = await fetch(API + "/api/auth/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                name: document.getElementById("name").value,
                email: document.getElementById("email").value,
                password: document.getElementById("password").value,
                role_id: document.getElementById("role_id").value
            })
        });

        const data = await response.json();

        document.getElementById("message").innerText = data.message;

        if (response.ok) {
            window.location.href = "/login";
        }
    });
}


// AUTH HEADER
function authHeaders() {
    return {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + localStorage.getItem("token")
    };
}


// CREATE TICKET
const ticketForm = document.getElementById("ticketForm");

if (ticketForm) {
    ticketForm.addEventListener("submit", async function (e) {
        e.preventDefault();

        const response = await fetch(API + "/api/tickets/", {
            method: "POST",
            headers: authHeaders(),
            body: JSON.stringify({
                subject: document.getElementById("subject").value,
                description: document.getElementById("description").value,
                category_id: document.getElementById("category_id").value,
                priority: document.getElementById("priority").value
            })
        });

        const data = await response.json();

        document.getElementById("ticketMessage").innerText = data.message;

        if (response.ok) {
            ticketForm.reset();
            loadTickets();
        }
    });
}


// VIEW MY TICKETS
async function loadTickets() {
    const response = await fetch(API + "/api/tickets/my", {
        headers: authHeaders()
    });

    const data = await response.json();

    const list = document.getElementById("ticketList");
    if (!list) return;

    list.innerHTML = "";

    (data.tickets || []).forEach(ticket => {
        list.innerHTML += `
            <div class="card p-3">
                <h5>${ticket.subject}</h5>
                <p>Ticket ID: ${ticket.ticket_id}</p>
                <p>Category: ${ticket.category_name}</p>
                <p>Priority: ${ticket.priority}</p>
                <p>Status: ${ticket.status}</p>
            </div>
        `;
    });
}


// VIEW ALL TICKETS
async function loadAllTickets() {
    const response = await fetch(API + "/api/tickets/", {
        headers: authHeaders()
    });

    const data = await response.json();

    const list = document.getElementById("allTickets");
    if (!list) return;

    list.innerHTML = "";

    (data.tickets || []).forEach(ticket => {
        list.innerHTML += `
            <div class="card p-3">
                <h5>${ticket.subject}</h5>
                <p>Ticket ID: ${ticket.ticket_id}</p>
                <p>Requester: ${ticket.requester_name}</p>
                <p>Team: ${ticket.authorized_team}</p>
                <p>Status: ${ticket.status}</p>

                <select id="status-${ticket.ticket_id}" class="form-select mb-2">
                    <option>Open</option>
                    <option>In Progress</option>
                    <option>Waiting</option>
                    <option>Escalated</option>
                    <option>Resolved</option>
                    <option>Closed</option>
                </select>

                <button class="btn btn-primary"
                    onclick="updateStatus('${ticket.ticket_id}')">
                    Update Status
                </button>
            </div>
        `;
    });
}


// UPDATE STATUS
async function updateStatus(ticketId) {
    const status = document.getElementById("status-" + ticketId).value;

    const response = await fetch(
        API + "/api/tickets/" + ticketId + "/status",
        {
            method: "PATCH",
            headers: authHeaders(),
            body: JSON.stringify({ status: status })
        }
    );

    const data = await response.json();
    alert(data.message);

    if (response.ok) {
        loadAllTickets();
    }
}


// POLICY SEARCH
async function searchPolicies() {
    const keyword = document.getElementById("keyword").value.trim();

    if (!keyword) {
        alert("Enter a search keyword");
        return;
    }

    const response = await fetch(
        API + "/api/policies/search?q=" + encodeURIComponent(keyword),
        { headers: authHeaders() }
    );

    const data = await response.json();

    const results = document.getElementById("policyResults");
    results.innerHTML = "";

    if (!response.ok) {
        results.innerText = data.message;
        return;
    }

    (data.results || []).forEach(policy => {
        const card = document.createElement("div");
        card.className = "card p-3";

        const title = document.createElement("h5");
        title.textContent = policy.article_title;

        const answer = document.createElement("p");
        answer.textContent = policy.answer;

        const citation = document.createElement("small");
        citation.textContent =
            "Policy: " + policy.policy_title +
            " | Version: " + policy.policy_version;

        card.append(title, answer, citation);
        results.appendChild(card);
    });
}


// LOGOUT
function logout() {
    localStorage.removeItem("token");
    localStorage.removeItem("role");
    window.location.href = "/login";
}
