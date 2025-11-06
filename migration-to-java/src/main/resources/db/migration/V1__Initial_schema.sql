CREATE TABLE users (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL,
    first_name VARCHAR(255),
    last_name VARCHAR(255)
);

CREATE TABLE bank_account_types (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(128) NOT NULL,
    maximum_withdrawal_amount DECIMAL(12, 2) NOT NULL,
    annual_interest_rate DECIMAL(5, 2) NOT NULL,
    interest_calculation_per_year INT NOT NULL
);

CREATE TABLE user_bank_accounts (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    account_type_id BIGINT NOT NULL,
    account_no BIGINT NOT NULL UNIQUE,
    gender VARCHAR(1) NOT NULL,
    birth_date DATE,
    balance DECIMAL(12, 2) NOT NULL DEFAULT 0.00,
    interest_start_date DATE,
    initial_deposit_date DATE,
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (account_type_id) REFERENCES bank_account_types(id)
);

CREATE TABLE user_addresses (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    user_id BIGINT NOT NULL,
    street_address VARCHAR(512) NOT NULL,
    city VARCHAR(256) NOT NULL,
    postal_code INT NOT NULL,
    country VARCHAR(256) NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE TABLE transactions (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    account_id BIGINT NOT NULL,
    amount DECIMAL(12, 2) NOT NULL,
    balance_after_transaction DECIMAL(12, 2) NOT NULL,
    transaction_type INT NOT NULL,
    timestamp TIMESTAMP NOT NULL,
    FOREIGN KEY (account_id) REFERENCES user_bank_accounts(id)
);

CREATE INDEX idx_transactions_account ON transactions(account_id);
CREATE INDEX idx_transactions_timestamp ON transactions(timestamp);
CREATE INDEX idx_user_bank_accounts_user ON user_bank_accounts(user_id);
