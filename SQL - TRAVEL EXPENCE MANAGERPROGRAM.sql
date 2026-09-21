CREATE DATABASE IF NOT EXISTS travel_expense_manager;

USE travel_expense_manager;

CREATE TABLE IF NOT EXISTS expenses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    expense_date DATE NOT NULL,
    description VARCHAR(255) NOT NULL,
    category VARCHAR(100) NOT NULL,
    amount DECIMAL(10, 2) NOT NULL,
    payment_method VARCHAR(100) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
SHOW TABLES;

DESCRIBE expenses;
INSERT INTO expenses
(expense_date, description, category, amount, payment_method)
VALUES
('2026-09-01', 'Airport taxi', 'Transport', 450.00, 'UPI'),
('2026-09-01', 'Hotel room', 'Accommodation', 2500.00, 'Card'),
('2026-09-02', 'Lunch', 'Food', 350.00, 'Cash');
SELECT * FROM expenses;
SELECT category, SUM(amount) AS total_spent
FROM expenses
GROUP BY category
ORDER BY total_spent DESC;
SELECT
    DATE_FORMAT(expense_date, '%Y-%m') AS month,
    SUM(amount) AS total_spent
FROM expenses
GROUP BY DATE_FORMAT(expense_date, '%Y-%m')
ORDER BY month;