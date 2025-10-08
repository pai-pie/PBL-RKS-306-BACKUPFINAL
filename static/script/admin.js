// Admin Panel JavaScript
document.addEventListener('DOMContentLoaded', function() {
    checkAuthAndInitialize();
});

async function checkAuthAndInitialize() {
    try {
        const response = await fetch('/api/auth/check');
        const data = await response.json();
        
        if (data.authenticated && data.user.role === 'admin') {
            initializeAdminPanel();
            loadDashboardData();
        } else {
            window.location.href = '/login';
        }
    } catch (error) {
        console.error('Auth check failed:', error);
        window.location.href = '/login';
    }
}

function initializeAdminPanel() {
    document.body.style.opacity = '1';
    document.body.style.transition = 'opacity 0.5s ease';
}

async function loadDashboardData() {
    try {
        const response = await fetch('/api/admin/stats');
        if (response.ok) {
            const stats = await response.json();
            updateDashboardStats(stats);
        }
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

function updateDashboardStats(stats) {
    const usersCard = document.querySelector('.summary-card:nth-child(3)');
    if (usersCard) {
        usersCard.innerHTML = `
            <h3>👤 Users</h3>
            <p>Registered: <b>${stats.total_users}</b></p>
            <p>Recent: <b>${stats.recent_users}</b></p>
        `;
    }
    
    const eventsCard = document.querySelector('.summary-card:nth-child(1)');
    if (eventsCard) {
        eventsCard.innerHTML = `
            <h3>🎵 Total Events</h3>
            <p>Active Events: <b>${stats.total_concerts}</b></p>
            <p>Upcoming: <b>${stats.total_concerts}</b></p>
        `;
    }
}

function showSection(id) {
    document.querySelectorAll('.section').forEach(sec => sec.style.display = "none");
    document.getElementById(id).style.display = "block";
    
    document.querySelectorAll('.sidebar a').forEach(a => a.classList.remove("active"));
    event.target.classList.add("active");
    
    if (id === 'users') loadUsersData();
    if (id === 'events') loadEventsData();
}

async function loadUsersData() {
    try {
        const response = await fetch('/api/admin/users');
        if (response.ok) {
            const users = await response.json();
            renderUsersTable(users);
        }
    } catch (error) {
        console.error('Error loading users:', error);
    }
}

async function loadEventsData() {
    try {
        const response = await fetch('/api/concerts');
        if (response.ok) {
            const concerts = await response.json();
            renderEventsTable(concerts);
        }
    } catch (error) {
        console.error('Error loading events:', error);
    }
}

function renderUsersTable(users) {
    const usersSection = document.getElementById('users');
    let tableHTML = `
        <h2>User Management</h2>
        <div class="table-container">
            <table>
                <tr>
                    <th>ID</th>
                    <th>Name</th>
                    <th>Email</th>
                    <th>Role</th>
                    <th>Join Date</th>
                </tr>
    `;
    
    users.forEach(user => {
        const joinDate = new Date(user.join_date).toLocaleDateString();
        tableHTML += `
            <tr>
                <td>${user.id}</td>
                <td>${user.username}</td>
                <td>${user.email}</td>
                <td class="${user.role === 'admin' ? 'status-paid' : 'status-pending'}">${user.role}</td>
                <td>${joinDate}</td>
            </tr>
        `;
    });
    
    tableHTML += `</table></div>`;
    usersSection.innerHTML = tableHTML;
}

function renderEventsTable(concerts) {
    const eventsSection = document.getElementById('events');
    let tableHTML = `
        <h2>Manage Events</h2>
        <div class="table-container">
            <table>
                <tr>
                    <th>Event Name</th>
                    <th>Artist</th>
                    <th>Date</th>
                    <th>Venue</th>
                    <th>Price</th>
                </tr>
    `;
    
    concerts.forEach(concert => {
        tableHTML += `
            <tr>
                <td>${concert.name}</td>
                <td>${concert.artist}</td>
                <td>${concert.date}</td>
                <td>${concert.venue}</td>
                <td>Rp ${concert.price.toLocaleString()}</td>
            </tr>
        `;
    });
    
    tableHTML += `</table></div>`;
    eventsSection.innerHTML = tableHTML;
}

function logout() {
    if (confirm('Are you sure you want to logout?')) {
        window.location.href = '/logout';
    }
}