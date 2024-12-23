-- Initialize database with UTF-8 support
SET NAMES utf8mb4;
SET CHARACTER_SET_CLIENT = utf8mb4;

-- Create database if not exists
CREATE DATABASE IF NOT EXISTS menu_matching CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE menu_matching;

-- Grant privileges
GRANT ALL PRIVILEGES ON menu_matching.* TO 'menuuser'@'%';
FLUSH PRIVILEGES;
