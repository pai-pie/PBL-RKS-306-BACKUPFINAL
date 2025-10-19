-- Initialize MySQL database untuk GuardianTix
CREATE DATABASE IF NOT EXISTS guardiantix;
USE guardiantix;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role VARCHAR(50) DEFAULT 'user',
    phone VARCHAR(20),
    join_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create concerts table
CREATE TABLE IF NOT EXISTS concerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    artist VARCHAR(255) NOT NULL,
    date VARCHAR(100) NOT NULL,
    venue VARCHAR(255) NOT NULL,
    price INT NOT NULL,
    available_tickets INT NOT NULL
);

-- Insert admin user dengan password plaintext
INSERT IGNORE INTO users (username, email, password_hash, role) 
VALUES ('System Admin', 'admin@guardiantix.com', 'admin123', 'admin');

-- Insert sample concerts
INSERT IGNORE INTO concerts (name, artist, date, venue, price, available_tickets) VALUES
('Coldplay Tour', 'Coldplay', '2024-12-15', 'GBK Stadium', 750000, 1000),
('Blackpink Show', 'Blackpink', '2024-11-20', 'Istora Senayan', 1200000, 500),
('Jazz Festival', 'Various Artists', '2024-10-25', 'Plenary Hall', 500000, 300);