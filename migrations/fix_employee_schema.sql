-- Schema fixes for employee/client modules (safe to re-run with IF NOT EXISTS / checks)
USE bdcompleta;

-- Missing tables
CREATE TABLE IF NOT EXISTS `prospects` (
  `id_Prospect` int(11) NOT NULL AUTO_INCREMENT,
  `fullname` varchar(60) NOT NULL,
  `company` varchar(100) DEFAULT NULL,
  `number` varchar(30) DEFAULT NULL,
  `email` varchar(60) DEFAULT NULL,
  `contacted` tinyint(1) NOT NULL DEFAULT 0,
  PRIMARY KEY (`id_Prospect`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `machinesid` (
  `id_Machine` int(11) NOT NULL,
  `uid_Machine` varchar(255) NOT NULL,
  PRIMARY KEY (`id_Machine`),
  UNIQUE KEY `uid_Machine` (`uid_Machine`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `access_records` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `fingerprint_id` int(11) NOT NULL,
  `date_time` datetime NOT NULL,
  `status` tinyint(1) NOT NULL DEFAULT 1,
  PRIMARY KEY (`id`),
  KEY `idx_fingerprint_datetime` (`fingerprint_id`, `date_time`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

CREATE TABLE IF NOT EXISTS `payroll` (
  `id_bonus` int(11) NOT NULL AUTO_INCREMENT,
  `employee_id` int(11) NOT NULL,
  `bonus` tinyint(1) NOT NULL DEFAULT 1,
  `datetime` timestamp NOT NULL DEFAULT current_timestamp(),
  PRIMARY KEY (`id_bonus`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

-- Ensure join-compatible collation if tables already existed with server default
ALTER TABLE `machinesid` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
ALTER TABLE `prospects` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
ALTER TABLE `access_records` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
ALTER TABLE `payroll` CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

-- orders columns
ALTER TABLE `orders`
  ADD COLUMN IF NOT EXISTS `status` tinyint(1) NOT NULL DEFAULT 1,
  ADD COLUMN IF NOT EXISTS `type` tinyint(1) NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS `cancel_status` tinyint(1) DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS `verifiedDocs` tinyint(1) NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS `paymentMade` tinyint(1) NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS `shipmentMade` tinyint(1) NOT NULL DEFAULT 0,
  ADD COLUMN IF NOT EXISTS `address` varchar(255) DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS `postalCode` varchar(20) DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS `rfc` varchar(20) DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS `phoneNumber` varchar(30) DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS `paymentMethod` varchar(50) DEFAULT NULL;

-- files: code uses status/changeRequest (dump has estado)
ALTER TABLE `files`
  ADD COLUMN IF NOT EXISTS `status` int(11) DEFAULT 0,
  ADD COLUMN IF NOT EXISTS `changeRequest` tinyint(1) DEFAULT 0;

UPDATE `files` SET `status` = COALESCE(`estado`, 0) WHERE `status` IS NULL OR `status` = 0;

-- machines maintenance flags
ALTER TABLE `machines`
  ADD COLUMN IF NOT EXISTS `maintenanceNotice` tinyint(1) DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS `retiredForMaintenenace` tinyint(1) NOT NULL DEFAULT 0;

-- machineorders
ALTER TABLE `machineorders`
  ADD COLUMN IF NOT EXISTS `price` decimal(10,2) DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS `type` tinyint(1) DEFAULT NULL;

-- preventivemaintenance
ALTER TABLE `preventivemaintenance`
  ADD COLUMN IF NOT EXISTS `scheduled_date` date DEFAULT NULL;

-- products
ALTER TABLE `products`
  ADD COLUMN IF NOT EXISTS `sell_price` decimal(10,2) DEFAULT NULL;

UPDATE `products` SET `sell_price` = `price` * 12 WHERE `sell_price` IS NULL;

-- user notes + password reset
ALTER TABLE `user`
  ADD COLUMN IF NOT EXISTS `note` text DEFAULT NULL,
  ADD COLUMN IF NOT EXISTS `reset_token` varchar(64) DEFAULT NULL;

-- Seed machinesid from store UIDs matched by model
INSERT IGNORE INTO `machinesid` (`id_Machine`, `uid_Machine`)
SELECT m.id_Machine, s.uid
FROM store s
INNER JOIN machines m ON m.model = s.model;

-- Sample prospects
INSERT INTO `prospects` (`fullname`, `company`, `number`, `email`, `contacted`)
SELECT * FROM (
  SELECT 'Prospecto Demo' AS fullname, 'Constructora Demo' AS company, '3312345678' AS number, 'prospecto@demo.com' AS email, 0 AS contacted
) AS tmp
WHERE NOT EXISTS (SELECT 1 FROM prospects LIMIT 1);
