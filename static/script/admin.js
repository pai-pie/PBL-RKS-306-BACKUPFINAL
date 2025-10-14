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
// ... kode showSection sebelumnya ...

// ... kode showSection sebelumnya ...

function showSection(id) {
    document.querySelectorAll('.section').forEach(sec => sec.style.display = "none");
    document.getElementById(id).style.display = "block";
    
    document.querySelectorAll('.sidebar a').forEach(a => a.classList.remove("active"));
    event.target.classList.add("active");
    
    if (id === 'users') loadUsersData();
    if (id === 'events') loadEventsData();
    if (id === 'transactions') loadTransactionsData();
    // ⬇️ TAMBAHKAN BARIS INI ⬇️
    if (id === 'tickets') loadTicketsData();
}

// ... sisa kode ...
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
// ... fungsi renderEventsTable() di atas ...

// -----------------------------------------------------
// FUNGSI BARU UNTUK TRANSAKSI
// -----------------------------------------------------

async function loadTransactionsData() {
    const transactionsSection = document.getElementById('transactions');
    // Tampilkan loading state jika perlu, atau langsung panggil render.
    // Untuk saat ini, kita akan menggunakan array kosong untuk mensimulasikan data kosong.
    
    try {
        const response = await fetch('/api/admin/transactions'); // Asumsi API untuk data transaksi
        if (response.ok) {
            const transactions = await response.json();
            renderTransactionsTable(transactions);
        } else {
            // Jika ada error/data kosong dari server, render tabel kosong
            renderTransactionsTable([]);
        }
    } catch (error) {
        console.error('Error loading transactions:', error);
        // Tampilkan pesan error atau tabel kosong
        renderTransactionsTable([]); 
    }
}

function renderTransactionsTable(transactions) {
    const transactionsSection = document.getElementById('transactions');
    let tableBodyHTML = '';
    const colCount = 8; // ID, Buyer Name, Ticket Type, Total Price, Payment Method, Date, Status, Actions

    if (transactions.length === 0) {
        // Tampilan KOSONG (sesuai permintaan)
        tableBodyHTML = `
            <tr>
                <td colspan="${colCount}" style="text-align: center; padding: 40px 20px; background: rgba(42, 42, 61, 0.7);">
                    <p style="color: #FFD700; font-size: 1.2em; font-weight: bold; margin: 0;">
                        ⚠️ Belum ada data Transaksi.
                    </p>
                    <p style="color: #C8A2C8; margin-top: 10px; font-size: 0.9em;">
                        *Semua transaksi yang berhasil dan tertunda akan muncul di sini.*
                    </p>
                </td>
            </tr>
        `;
    } else {
        // Tampilan JIKA ADA DATA
        transactions.forEach(tx => {
            const txDate = new Date(tx.date).toLocaleDateString();
            const statusClass = tx.status === 'Completed' ? 'status-paid' : 'status-pending';
            const priceFormatted = new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(tx.total_price);

            tableBodyHTML += `
                <tr>
                    <td>${tx.id}</td>
                    <td>${tx.buyer_name}</td>
                    <td>${tx.ticket_type}</td>
                    <td>${priceFormatted}</td>
                    <td>${tx.payment_method}</td>
                    <td>${txDate}</td>
                    <td class="${statusClass}">${tx.status}</td>
                    <td>
                        <button class="btn-secondary" onclick="viewTxDetail(${tx.id})">View</button>
                    </td>
                </tr>
            `;
        });
    }

    // Gabungkan HTML penuh
    const tableHTML = `
        <h2>Transaction Management</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Buyer Name</th>
                        <th>Ticket Type</th>
                        <th>Total Price</th>
                        <th>Payment Method</th>
                        <th>Date</th>
                        <th>Status</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${tableBodyHTML}
                </tbody>
            </table>
        </div>
        <div class="summary">
            <p>Total Transaksi: ${transactions.length}</p>
        </div>
    `;

    transactionsSection.innerHTML = tableHTML;
}

// Tambahkan fungsi ini jika Anda ingin tombol 'View' berfungsi
function viewTxDetail(txId) {
    alert(`Melihat detail transaksi ID: ${txId}`);
    // Logika sebenarnya: membuka modal atau navigasi ke halaman detail
}
// ... setelah fungsi loadEventsData() ...

async function loadTicketsData() {
    // Tampilkan tabel kosong untuk sementara
    // Di masa depan, kode ini akan memanggil API: /api/admin/tickets
    renderTicketsTable([]);
}

function renderTicketsTable(tickets) {
    const ticketsSection = document.getElementById('tickets');
    let tableBodyHTML = '';
    const colCount = 6; // Ticket ID, Event Name, Ticket Type, Price, Quantity Available, Actions

    if (tickets.length === 0) {
        // Tampilan KOSONG
        tableBodyHTML = `
            <tr>
                <td colspan="${colCount}" style="text-align: center; padding: 40px 20px; background: rgba(42, 42, 61, 0.7);">
                    <p style="color: #FFD700; font-size: 1.2em; font-weight: bold; margin: 0;">
                        ⚠️ Belum ada jenis Tiket yang didaftarkan.
                    </p>
                    <p style="color: #C8A2C8; margin-top: 10px; font-size: 0.9em;">
                        *Tambahkan kategori tiket baru untuk event Anda di sini.*
                    </p>
                </td>
            </tr>
        `;
    } else {
        // Logika untuk menampilkan data tiket (jika sudah ada)
        tickets.forEach(ticket => {
            const priceFormatted = new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(ticket.price);
            tableBodyHTML += `
                <tr>
                    <td>${ticket.id}</td>
                    <td>${ticket.event_name}</td>
                    <td>${ticket.type}</td>
                    <td>${priceFormatted}</td>
                    <td>${ticket.quantity_available}</td>
                    <td>
                        <button class="btn-secondary" onclick="editTicket(${ticket.id})">Edit</button>
                    </td>
                </tr>
            `;
        });
    }

    // Gabungkan HTML penuh
    const tableHTML = `
        <h2>Ticket Management</h2>
        <div class="table-container">
            <table>
                <thead>
                    <tr>
                        <th>Ticket ID</th>
                        <th>Event Name</th>
                        <th>Ticket Type</th>
                        <th>Price</th>
                        <th>Quantity Available</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
                    ${tableBodyHTML}
                </tbody>
            </table>
        </div>
        <div class="summary">
            <p>Total Jenis Tiket: ${tickets.length}</p>
            <button class="btn-primary" onclick="addNewTicket()" style="margin-top: 15px;">+ Add New Ticket Type</button>
        </div>
    `;

    ticketsSection.innerHTML = tableHTML;
}

// Tambahkan placeholder fungsi aksi
function addNewTicket() {
    alert("Membuka form untuk menambah jenis tiket baru.");
}

function editTicket(ticketId) {
    alert(`Mengedit jenis tiket ID: ${ticketId}`);
}