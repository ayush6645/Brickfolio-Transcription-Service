-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: localhost
-- Generation Time: Apr 24, 2026 at 05:16 AM
-- Server version: 10.5.27-MariaDB
-- PHP Version: 8.3.10

SET FOREIGN_KEY_CHECKS=0;
SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `brick9ej_crm`
--

-- --------------------------------------------------------

--
-- Table structure for table `activity_types`
--

CREATE TABLE `activity_types` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `name` varchar(191) NOT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `call_dispositions`
--

CREATE TABLE `call_dispositions` (
  `code` varchar(30) NOT NULL,
  `name` varchar(100) NOT NULL,
  `created_at` datetime DEFAULT NULL,
  `updated_at` datetime DEFAULT NULL,
  `show_campaign_leads` int(11) NOT NULL DEFAULT 0,
  `raw_lead_stage_id` int(11) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `closed`
--

CREATE TABLE `closed` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `lead_id` bigint(20) UNSIGNED NOT NULL,
  `project_id` bigint(20) UNSIGNED NOT NULL,
  `user_id` text DEFAULT NULL,
  `flat_no` varchar(191) NOT NULL,
  `config` varchar(191) NOT NULL,
  `agreement_val` varchar(191) NOT NULL,
  `cheque_no` varchar(191) NOT NULL,
  `selfie` text DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL,
  `property_type` varchar(191) DEFAULT NULL COMMENT 'Commercial / Residential',
  `client_name` varchar(191) DEFAULT NULL,
  `client_number` bigint(20) NOT NULL,
  `developer_name` varchar(191) NOT NULL,
  `project_name` varchar(191) NOT NULL,
  `cluster_tower` varchar(191) NOT NULL,
  `configuration` varchar(191) DEFAULT NULL,
  `consideration_value` varchar(191) DEFAULT NULL,
  `agreement_value` varchar(191) DEFAULT NULL,
  `total_cost` varchar(191) DEFAULT NULL,
  `developer_rm` varchar(191) DEFAULT NULL,
  `developer_rm_name` varchar(191) DEFAULT NULL,
  `developer_rm_contact` varchar(191) DEFAULT NULL,
  `remarks` text NOT NULL,
  `booking_form` varchar(191) DEFAULT NULL,
  `builder_confirmation` varchar(191) DEFAULT NULL,
  `cheque_payment` varchar(191) DEFAULT NULL,
  `cost_sheet` varchar(191) DEFAULT NULL,
  `adhaar_card` varchar(191) DEFAULT NULL,
  `pan_card` varchar(191) DEFAULT NULL,
  `no_of_units` int(11) NOT NULL DEFAULT 1,
  `date_of_booking` timestamp NULL DEFAULT NULL,
  `focus_project` tinyint(1) NOT NULL,
  `cluster` varchar(191) NOT NULL,
  `tower` varchar(191) NOT NULL,
  `unit_number` bigint(20) UNSIGNED NOT NULL,
  `booking_amount` varchar(191) DEFAULT NULL,
  `sdr_received` tinyint(1) NOT NULL,
  `sdr_amount` varchar(191) DEFAULT NULL,
  `welcome_call` tinyint(1) NOT NULL,
  `tagging_issue` tinyint(1) NOT NULL,
  `p_l` int(11) NOT NULL,
  `region` varchar(191) NOT NULL DEFAULT '',
  `focus` varchar(191) NOT NULL,
  `caller_id` int(11) NOT NULL,
  `justifiction_incentive` varchar(191) NOT NULL,
  `referal_benefit` tinyint(1) NOT NULL,
  `bonus_received_to_company` tinyint(1) NOT NULL,
  `basic_value` double NOT NULL,
  `total_sales_value` double NOT NULL,
  `slab` varchar(191) NOT NULL,
  `gross_revenue` double NOT NULL,
  `referal_amount` varchar(191) NOT NULL,
  `referal_remark` varchar(191) NOT NULL,
  `cro_incentive_amount` varchar(191) NOT NULL,
  `tl_incentive_amount` varchar(191) NOT NULL,
  `presale_incentive_amount` varchar(191) NOT NULL,
  `balance_revenue` varchar(191) NOT NULL,
  `developer_cro_bonus` varchar(191) NOT NULL,
  `status` varchar(191) NOT NULL,
  `status_email` mediumtext NOT NULL,
  `status_call` mediumtext NOT NULL,
  `status_whatsapp` mediumtext NOT NULL,
  `transaction_status` varchar(191) NOT NULL DEFAULT 'active',
  `status_remark` text NOT NULL,
  `city` varchar(191) DEFAULT NULL,
  `zone` varchar(191) DEFAULT NULL,
  `billraised_amount` text NOT NULL,
  `builder_firm_name` varchar(191) NOT NULL,
  `lead_status` int(11) NOT NULL DEFAULT 1,
  `invoice_number` text NOT NULL DEFAULT '',
  `followup_dt` datetime DEFAULT NULL,
  `billing_name` varchar(191) NOT NULL DEFAULT '',
  `deleted_at` timestamp NULL DEFAULT NULL,
  `referal_raised_status` varchar(191) DEFAULT 'No',
  `zone_id` int(11) DEFAULT NULL,
  `supervisor_approval` int(11) NOT NULL DEFAULT 2 COMMENT '1=Approved, 2=Pending',
  `verified_by_areahead` datetime DEFAULT NULL,
  `verified_by_vp` datetime DEFAULT NULL,
  `areahead_id` int(11) DEFAULT NULL,
  `vp_id` int(11) DEFAULT NULL,
  `approval_1` int(11) DEFAULT NULL,
  `approval_1_at` datetime DEFAULT NULL,
  `approval_2` int(11) DEFAULT NULL,
  `approval_2_at` datetime DEFAULT NULL,
  `transaction_done_status` int(11) NOT NULL DEFAULT 0 COMMENT '0 - Transaction Pending, 1 - Transaction Completed',
  `approval_3` int(11) DEFAULT NULL,
  `approval_3_at` datetime DEFAULT NULL,
  `manager_referal_remark` text DEFAULT NULL,
  `supervisor_referal_remark` text DEFAULT NULL,
  `welcome_call_mail` int(11) DEFAULT NULL,
  `welcome_call_mail_remark` varchar(191) DEFAULT NULL,
  `added_by` int(11) DEFAULT NULL,
  `user_id_reports_to` bigint(20) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Triggers `closed`
--
DELIMITER $$
CREATE TRIGGER `change_lead_status_after_update_row` BEFORE UPDATE ON `closed` FOR EACH ROW BEGIN
    IF NEW.agreement_val * 1 = 0 OR
       NEW.focus_project IS NULL OR LENGTH(NEW.focus_project) = 0 OR
       NEW.region IS NULL OR NEW.region = '' OR
       NEW.developer_name IS NULL OR NEW.developer_name = '' OR
       NEW.project_name IS NULL OR NEW.project_name = '' OR
       NEW.cluster IS NULL OR NEW.cluster = '' OR
       NEW.tower IS NULL OR NEW.tower = '' OR
       NEW.slab IS NULL OR NEW.slab = '' OR
       NEW.flat_no IS NULL OR NEW.flat_no = '' OR
       NEW.configuration IS NULL OR NEW.configuration = '' OR
       NEW.consideration_value * 1 = 0 OR
       (NEW.sdr_received = 1 AND NEW.sdr_amount * 1 = 0) OR
       (NEW.referal_benefit = 1 AND NEW.referal_amount * 1 = 0) THEN
        SET NEW.lead_status = 1;
    ELSE
        SET NEW.lead_status = 2;
    END IF;
END
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Table structure for table `despositions`
--

CREATE TABLE `despositions` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `status` varchar(191) NOT NULL,
  `description` varchar(191) NOT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL,
  `parent_id` bigint(20) DEFAULT NULL,
  `update` int(11) NOT NULL DEFAULT 0,
  `additional` int(11) NOT NULL DEFAULT 0,
  `seque` int(11) DEFAULT 0,
  `lead_stages` bigint(20) NOT NULL DEFAULT 0,
  `group` varchar(191) NOT NULL DEFAULT '',
  `deleted_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `desposition_histories`
--

CREATE TABLE `desposition_histories` (
  `id` bigint(20) NOT NULL,
  `lead` bigint(20) DEFAULT NULL,
  `cust_name` varchar(219) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `cust_number` varchar(20) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `source` varchar(191) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `cust_status` varchar(191) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `cust_location` varchar(191) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `called_at` datetime DEFAULT NULL,
  `generated_on` timestamp NOT NULL DEFAULT current_timestamp(),
  `updated_at` datetime NOT NULL,
  `created_at` datetime NOT NULL,
  `ayukta_agent_id` varchar(191) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `user_id` int(11) DEFAULT NULL,
  `recording_path` text DEFAULT NULL,
  `image` text DEFAULT NULL,
  `remark` text DEFAULT NULL,
  `deleted_at` timestamp NULL DEFAULT NULL,
  `from_budget` int(11) DEFAULT NULL,
  `to_budget` int(11) DEFAULT NULL,
  `raw_lead_stage_id` int(11) NOT NULL DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Triggers `desposition_histories`
--
DELIMITER $$
CREATE TRIGGER `update latest disposition to raw_data table` AFTER INSERT ON `desposition_histories` FOR EACH ROW IF NEW.cust_number != '' THEN
UPDATE raw_data SET raw_data.disposition = NEW.cust_status WHERE raw_data.phone = NEW.cust_number;
 
 
UPDATE raw_leads SET call_count = (SELECT COUNT(id) FROM desposition_histories WHERE desposition_histories.cust_number = NEW.cust_number)
WHERE raw_leads.number = NEW.cust_number;
 
END IF
$$
DELIMITER ;

-- --------------------------------------------------------

--
-- Table structure for table `disposition_leads`
--

CREATE TABLE `disposition_leads` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `lead_id` bigint(20) NOT NULL,
  `disposition_id` bigint(20) NOT NULL,
  `address` varchar(191) DEFAULT NULL,
  `meeting_at` timestamp NULL DEFAULT NULL,
  `recording_link` varchar(191) NOT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL,
  `time` varchar(191) DEFAULT NULL,
  `date` date DEFAULT NULL,
  `remark` text DEFAULT NULL,
  `location` varchar(191) DEFAULT NULL,
  `latitude` varchar(191) DEFAULT NULL,
  `longitude` varchar(191) DEFAULT NULL,
  `project` varchar(191) DEFAULT NULL,
  `e_meeting_link` varchar(191) DEFAULT NULL,
  `other_cp` int(11) NOT NULL DEFAULT 0 COMMENT '1 for Others, 0 for Brickfolio',
  `cp_builder_broker` varchar(191) DEFAULT NULL,
  `configuration` varchar(191) DEFAULT NULL,
  `cost` varchar(191) DEFAULT NULL,
  `number_of_months` varchar(191) DEFAULT NULL,
  `image` varchar(191) DEFAULT NULL,
  `agent_id` bigint(20) DEFAULT NULL,
  `lead_stage` int(11) NOT NULL DEFAULT 0 COMMENT '0, 1, 2, 3, 4, 5, 6, 7',
  `accompanied_by` bigint(20) NOT NULL DEFAULT 0,
  `is_done` int(11) NOT NULL DEFAULT 1 COMMENT '1-pending , 2-completed',
  `deleted_at` timestamp NULL DEFAULT NULL,
  `desposition_ratings` int(11) DEFAULT NULL,
  `desposition_rate_by` int(11) DEFAULT NULL,
  `rate_remark` varchar(191) DEFAULT NULL,
  `developer_name` varchar(191) DEFAULT NULL,
  `cluster_tower` varchar(191) DEFAULT NULL,
  `project_name` varchar(191) DEFAULT NULL,
  `token_details_id` int(11) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `invalid_leads`
--

CREATE TABLE `invalid_leads` (
  `id` int(10) UNSIGNED NOT NULL,
  `lead_id` bigint(20) UNSIGNED NOT NULL,
  `agent_id` bigint(20) UNSIGNED NOT NULL,
  `reports_to` bigint(20) UNSIGNED NOT NULL,
  `remark` varchar(191) NOT NULL,
  `status` int(11) NOT NULL COMMENT '0 - added, 1- approved, 2 - rejected, 3 - transferred',
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL,
  `deleted_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `leads`
--

CREATE TABLE `leads` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `cust_name` varchar(191) DEFAULT NULL,
  `cust_number` varchar(191) DEFAULT NULL,
  `cust_email` varchar(191) DEFAULT NULL,
  `property_type` varchar(191) DEFAULT NULL,
  `cust_requirement` longtext DEFAULT NULL,
  `lead_source` int(11) DEFAULT NULL,
  `purpose` varchar(191) DEFAULT NULL,
  `budget` text DEFAULT NULL,
  `rating` tinyint(4) DEFAULT NULL,
  `caller_id` bigint(20) UNSIGNED DEFAULT NULL,
  `caller_recording_path` varchar(191) DEFAULT NULL,
  `call_duration` varchar(191) DEFAULT NULL,
  `agent_accepted` tinyint(1) NOT NULL DEFAULT 0,
  `agent_id` bigint(20) UNSIGNED DEFAULT NULL,
  `agent_reports_to_id` bigint(20) UNSIGNED DEFAULT NULL,
  `project_id` bigint(20) UNSIGNED DEFAULT NULL,
  `is_valid` tinyint(1) DEFAULT NULL,
  `desposition_id` bigint(20) UNSIGNED DEFAULT NULL,
  `closed` tinyint(1) NOT NULL DEFAULT 0,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL,
  `lead_ref` varchar(191) DEFAULT NULL,
  `proccessed` tinyint(1) NOT NULL DEFAULT 0,
  `rejected_ids` text DEFAULT NULL,
  `eval_other_projects` tinyint(4) DEFAULT NULL,
  `other_locations` text DEFAULT NULL,
  `purchase_time` text DEFAULT NULL,
  `decision_maker_influencer` int(11) DEFAULT NULL,
  `contact_person_name_relation` text DEFAULT NULL,
  `preferred_floor` text DEFAULT NULL,
  `preferred_cities` varchar(191) DEFAULT NULL,
  `sent_to_ayukta` int(11) DEFAULT NULL,
  `contact_person_number` bigint(20) DEFAULT NULL,
  `other_projects` text DEFAULT NULL,
  `possession_expected` varchar(191) DEFAULT NULL,
  `lead_assigned_on` datetime DEFAULT NULL,
  `reassign_caller_id` int(11) DEFAULT NULL COMMENT 'Reassign Pre Sales CRM',
  `reassign_agent_id` int(11) DEFAULT NULL COMMENT 'Reassign Sales CRM',
  `reassign_datetime` datetime DEFAULT NULL COMMENT 'Lead Reassign Date & Time',
  `reference` varchar(191) DEFAULT NULL,
  `reason_for_invalid` text DEFAULT NULL,
  `hql` int(11) NOT NULL DEFAULT 0,
  `invalid_on` datetime DEFAULT NULL,
  `call_done` int(11) NOT NULL DEFAULT 0,
  `call_pending` int(11) NOT NULL DEFAULT 0,
  `sales_valid` int(11) NOT NULL DEFAULT 0,
  `remark_id` bigint(20) DEFAULT NULL,
  `recording_id` bigint(20) DEFAULT NULL,
  `meeting_id` bigint(20) DEFAULT NULL,
  `lead_stage` int(11) NOT NULL DEFAULT 0 COMMENT '0, 1, 2, 3, 4, 5',
  `config` varchar(191) DEFAULT NULL,
  `new_lead` int(11) DEFAULT NULL,
  `budget_min` int(11) NOT NULL DEFAULT 0,
  `budget_max` int(11) NOT NULL DEFAULT 0,
  `ref_lead_id` int(11) DEFAULT NULL,
  `accepted` bigint(20) DEFAULT NULL,
  `need_loan_assistance` int(11) NOT NULL DEFAULT 0 COMMENT '0-no , 1-yes',
  `loan_remarks` text DEFAULT NULL,
  `loan_min_amount` int(11) DEFAULT NULL,
  `loan_max_amount` int(11) DEFAULT NULL,
  `loan_agent_id` int(11) DEFAULT NULL COMMENT 'user id of loan agent',
  `loan_agent_assigned_dt` datetime DEFAULT NULL,
  `deleted_at` timestamp NULL DEFAULT NULL,
  `is_low_budget` int(11) NOT NULL DEFAULT 0,
  `contact_client_id` int(11) DEFAULT NULL,
  `lockin_period` int(11) DEFAULT NULL,
  `type_of_client` varchar(191) DEFAULT NULL,
  `work_stations` int(11) DEFAULT NULL,
  `cabins` int(11) DEFAULT NULL,
  `conference_rooms` int(11) DEFAULT NULL,
  `pantry` int(11) DEFAULT NULL,
  `server_rooms` int(11) DEFAULT NULL,
  `outright_type` varchar(191) DEFAULT NULL,
  `meeting_rooms` int(11) DEFAULT NULL,
  `carpet_area` int(11) DEFAULT NULL,
  `buildup_area` int(11) DEFAULT NULL,
  `transaction_mark` int(11) NOT NULL DEFAULT 0 COMMENT '1 - Marked 0 - Not Marked',
  `transaction_done` date DEFAULT NULL,
  `washrooms` int(11) DEFAULT NULL,
  `parkings` int(11) DEFAULT NULL,
  `security_deposit` double DEFAULT NULL,
  `escalation` double DEFAULT NULL,
  `agreement_tenure` double DEFAULT NULL,
  `rent_on_carpet` int(11) DEFAULT NULL,
  `frontage` double DEFAULT NULL,
  `height` varchar(191) DEFAULT NULL,
  `posession` int(11) DEFAULT NULL,
  `center_height` varchar(191) DEFAULT NULL,
  `no_of_docs` int(11) DEFAULT NULL,
  `docs_height` varchar(191) DEFAULT NULL,
  `ready_to_move` varchar(191) DEFAULT NULL,
  `space_type` varchar(191) DEFAULT NULL,
  `roi_percent` double DEFAULT NULL,
  `dg_backup` varchar(191) DEFAULT NULL,
  `loan_presales_id` int(11) DEFAULT NULL,
  `expo_event` varchar(191) DEFAULT NULL,
  `global_partner_id` varchar(191) DEFAULT NULL,
  `country_code` varchar(191) NOT NULL DEFAULT '+91'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `lead_activities`
--

CREATE TABLE `lead_activities` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL,
  `activity` text NOT NULL,
  `lead_id` bigint(20) NOT NULL,
  `caused_by` bigint(20) NOT NULL,
  `activity_type_id` int(11) NOT NULL DEFAULT 0,
  `deleted_at` timestamp NULL DEFAULT NULL,
  `role_id` int(11) DEFAULT NULL,
  `created_date` date DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `lead_shuffle`
--

CREATE TABLE `lead_shuffle` (
  `ls_id` bigint(20) UNSIGNED NOT NULL,
  `ls_lead_id` bigint(20) UNSIGNED NOT NULL,
  `ls_agent_id` bigint(20) UNSIGNED DEFAULT NULL,
  `ls_remark` text DEFAULT NULL,
  `ls_lead_stage` int(11) DEFAULT NULL,
  `ls_lead_assigned_date` datetime DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `lead_stages`
--

CREATE TABLE `lead_stages` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `stage_name` varchar(191) NOT NULL,
  `stage_disc` varchar(191) DEFAULT NULL,
  `stage_slug` varchar(191) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `meetings`
--

CREATE TABLE `meetings` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `address` text NOT NULL,
  `meeting_time` time DEFAULT NULL,
  `meeting_date` date DEFAULT NULL,
  `agent_id` bigint(20) UNSIGNED DEFAULT NULL,
  `lead_id` bigint(20) UNSIGNED NOT NULL,
  `latitude` double(10,7) DEFAULT NULL,
  `longitude` double(10,7) DEFAULT NULL,
  `sitevisit` tinyint(1) NOT NULL DEFAULT 0,
  `checked_in` tinyint(1) NOT NULL DEFAULT 0,
  `checkin_time` timestamp NULL DEFAULT NULL,
  `description` varchar(191) DEFAULT NULL,
  `rating` int(4) DEFAULT NULL,
  `checked_out` tinyint(1) NOT NULL DEFAULT 0,
  `checkout_time` timestamp NULL DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL,
  `meeting_type` text DEFAULT NULL,
  `emeet_link` text DEFAULT NULL,
  `project_name` text DEFAULT NULL,
  `location` text DEFAULT NULL,
  `recording_link` text DEFAULT NULL,
  `deleted_at` timestamp NULL DEFAULT NULL,
  `rate_by_id` int(11) DEFAULT NULL,
  `rating_comments` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `raw_leads`
--

CREATE TABLE `raw_leads` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `name` varchar(191) DEFAULT NULL,
  `email` varchar(191) DEFAULT NULL,
  `number` varchar(191) NOT NULL,
  `origin` varchar(191) DEFAULT NULL,
  `area` varchar(191) DEFAULT NULL,
  `ip` varchar(191) DEFAULT NULL,
  `gcID` varchar(191) DEFAULT NULL,
  `utm_source` varchar(191) DEFAULT 'Organic',
  `utm_medium` varchar(191) DEFAULT NULL,
  `utm_campaign` varchar(191) DEFAULT NULL,
  `campaign_id` varchar(50) DEFAULT NULL,
  `utm_term` varchar(191) DEFAULT NULL,
  `utm_content` varchar(191) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL,
  `domain` varchar(191) DEFAULT NULL,
  `sent_to_avyukta` int(11) NOT NULL DEFAULT 0,
  `is_answered` tinyint(1) NOT NULL DEFAULT 0,
  `agent_avyukta_id` bigint(20) DEFAULT NULL,
  `agent_id` bigint(20) DEFAULT NULL,
  `is_valid` tinyint(1) DEFAULT NULL,
  `remark` text DEFAULT NULL,
  `recording_link` varchar(191) DEFAULT NULL,
  `answered_on` timestamp NULL DEFAULT NULL,
  `disposition_id` bigint(20) DEFAULT 0,
  `adgroup_id` varchar(50) DEFAULT NULL,
  `ad_id` varchar(50) DEFAULT NULL,
  `page_id` varchar(50) DEFAULT NULL,
  `form_id` varchar(50) DEFAULT NULL,
  `leadgen_id` varchar(50) DEFAULT NULL,
  `payload` mediumtext DEFAULT NULL,
  `priority` int(11) NOT NULL DEFAULT 1 COMMENT '0:pre-sales,1:sales',
  `is_in_bucket` int(11) NOT NULL DEFAULT 0 COMMENT '0:no,1:yes',
  `deleted_at` timestamp NULL DEFAULT NULL,
  `ad_name` varchar(191) DEFAULT '',
  `adset_name` varchar(191) DEFAULT '',
  `call_count` int(11) DEFAULT 0,
  `complete_phone_number` varchar(191) DEFAULT NULL,
  `created_date` date NOT NULL DEFAULT current_timestamp(),
  `ayukta_list_id` varchar(191) DEFAULT NULL,
  `created_by` int(11) DEFAULT NULL,
  `campaign_type` varchar(191) DEFAULT 'Residential',
  `event_date_time` datetime DEFAULT NULL,
  `remarks` text DEFAULT NULL,
  `voice_note` varchar(191) DEFAULT NULL,
  `relation_with_the_lead` varchar(191) DEFAULT NULL,
  `customer_address` text DEFAULT NULL,
  `buying_location` varchar(191) DEFAULT NULL,
  `property_type` varchar(191) DEFAULT NULL,
  `configuration` varchar(191) DEFAULT NULL,
  `budget_min` varchar(191) DEFAULT NULL,
  `budget_max` varchar(191) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `raw_lead_stages`
--

CREATE TABLE `raw_lead_stages` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `stage_name` varchar(191) NOT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `recordings`
--

CREATE TABLE `recordings` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `lead_id` bigint(20) UNSIGNED NOT NULL,
  `agent_id` bigint(20) UNSIGNED NOT NULL,
  `path` varchar(191) NOT NULL,
  `incoming` tinyint(1) NOT NULL DEFAULT 0,
  `call_duration` varchar(191) NOT NULL,
  `tag` varchar(191) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL,
  `deleted_at` timestamp NULL DEFAULT NULL,
  `transcription_job_name` varchar(191) DEFAULT NULL,
  `transcription_job_status` varchar(191) DEFAULT NULL,
  `transcript_file` varchar(200) DEFAULT NULL,
  `transcript` longtext DEFAULT NULL,
  `buying_intent` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `remarks`
--

CREATE TABLE `remarks` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `lead_id` bigint(20) NOT NULL,
  `remarks` text NOT NULL,
  `user_id` bigint(20) NOT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL,
  `deleted_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `sales_meetings`
--

CREATE TABLE `sales_meetings` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `lead_id` bigint(20) NOT NULL,
  `agent_id` bigint(20) NOT NULL,
  `meeting_date` varchar(191) NOT NULL,
  `meeting_time` varchar(191) NOT NULL,
  `checkin` varchar(191) DEFAULT NULL,
  `checkin_meeting_latitude` varchar(191) DEFAULT NULL,
  `checkin_meeting_longitude` varchar(191) DEFAULT NULL,
  `checkout` varchar(191) DEFAULT NULL,
  `checkin_status` int(11) NOT NULL DEFAULT 0,
  `checkout_meeting_location` varchar(191) DEFAULT NULL,
  `checkout_meeting_latitude` varchar(191) DEFAULT NULL,
  `checkout_meeting_longitude` varchar(191) DEFAULT NULL,
  `valid` int(11) NOT NULL DEFAULT 1,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL,
  `deleted_at` timestamp NULL DEFAULT NULL,
  `distance_travel_km` varchar(191) DEFAULT NULL,
  `distance_travel_duration` varchar(191) DEFAULT NULL,
  `approver_1` int(11) DEFAULT NULL COMMENT 'manager id',
  `approved_1_at` datetime DEFAULT NULL COMMENT 'manager approve time',
  `approver_2` int(11) DEFAULT NULL COMMENT 'account id',
  `approved_2_at` datetime DEFAULT NULL COMMENT 'manager approve time',
  `manager_approval_status` int(11) DEFAULT 0,
  `account_approval_status` int(11) DEFAULT 0,
  `approval_status` int(11) NOT NULL DEFAULT 0 COMMENT '0 - Pending, 1 - Approve 1, 2 - Approve by First,3 - Approve by Second, 4 - Rejected by First, 5 - Rejected by Second',
  `remark` varchar(191) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `sales_recordings`
--

CREATE TABLE `sales_recordings` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `user_id` int(11) NOT NULL,
  `recording` text NOT NULL,
  `contact` varchar(50) NOT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL,
  `recording_date` varchar(191) NOT NULL,
  `recording_time` varchar(191) NOT NULL,
  `converted_at` datetime DEFAULT NULL,
  `lead_id` int(11) DEFAULT NULL,
  `contact_book_id` int(11) DEFAULT NULL,
  `remark` text DEFAULT NULL,
  `image` text DEFAULT NULL,
  `meeting_type` varchar(191) DEFAULT NULL COMMENT '1.F2F Meeting 2.Site Visit 3.E-Meeting 4.Call Back',
  `deleted_at` timestamp NULL DEFAULT NULL,
  `duration` time DEFAULT NULL,
  `created_date` date DEFAULT NULL,
  `transcription_job_name` varchar(191) DEFAULT NULL,
  `transcription_job_status` varchar(191) DEFAULT NULL,
  `transcript_file` varchar(200) DEFAULT NULL,
  `transcript` longtext DEFAULT NULL,
  `buying_intent` text DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `sources`
--

CREATE TABLE `sources` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `title` varchar(191) NOT NULL,
  `is_paid` varchar(191) NOT NULL DEFAULT '0',
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL,
  `deleted_at` timestamp NULL DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `users`
--

CREATE TABLE `users` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `name` varchar(191) NOT NULL,
  `first_name` varchar(191) DEFAULT NULL,
  `middle_name` varchar(191) DEFAULT NULL,
  `last_name` varchar(191) DEFAULT NULL,
  `email` varchar(191) NOT NULL,
  `personal_email` varchar(191) DEFAULT NULL,
  `profile_image` varchar(191) DEFAULT NULL,
  `role_id` bigint(20) UNSIGNED NOT NULL,
  `project_id` text DEFAULT NULL,
  `mobile_number` varchar(191) DEFAULT NULL,
  `latitude` double(10,7) DEFAULT NULL,
  `longitude` double(10,7) DEFAULT NULL,
  `email_verified_at` timestamp NULL DEFAULT NULL,
  `password` varchar(191) NOT NULL,
  `remember_token` varchar(100) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL,
  `card` text DEFAULT NULL,
  `closure_count` int(11) DEFAULT NULL,
  `device_id` varchar(191) DEFAULT NULL,
  `is_checkIn` enum('Y','N') NOT NULL DEFAULT 'N',
  `app_version` varchar(191) DEFAULT NULL,
  `enabled` int(11) NOT NULL DEFAULT 1,
  `e_card` varchar(191) DEFAULT NULL,
  `comment` text DEFAULT NULL,
  `company_designation` varchar(191) DEFAULT NULL,
  `department_id` bigint(20) DEFAULT NULL,
  `avyukta_id` varchar(191) DEFAULT NULL,
  `dialer_campaign` varchar(191) DEFAULT NULL,
  `shift_id` int(11) DEFAULT 2,
  `weekoff` varchar(191) DEFAULT 'Tuesday',
  `enroll_status` tinyint(1) DEFAULT NULL,
  `brickfolio_id` varchar(10) DEFAULT NULL,
  `date_of_joining` date DEFAULT NULL,
  `employee_status` varchar(191) DEFAULT NULL,
  `enroll_form_status` int(11) DEFAULT 0,
  `deleted_at` timestamp NULL DEFAULT NULL,
  `policy_id` int(11) DEFAULT 1,
  `pl_bal` double NOT NULL DEFAULT 0,
  `restricted_holiday` int(11) DEFAULT NULL,
  `optional_holiday` int(11) DEFAULT 2,
  `assign_zone` int(11) DEFAULT NULL,
  `work_location` int(11) DEFAULT NULL,
  `department_head` text DEFAULT NULL,
  `reporting_manager_id` int(11) NOT NULL DEFAULT 0,
  `report_to` varchar(191) DEFAULT NULL,
  `brickfolio_fav_user` text DEFAULT NULL,
  `esper_device_id` varchar(191) DEFAULT NULL COMMENT 'esper serial no',
  `esper_device_name` varchar(191) DEFAULT NULL,
  `attendance_device` int(11) NOT NULL DEFAULT 1,
  `designation_id` int(11) DEFAULT NULL,
  `t3m_version` varchar(191) DEFAULT NULL,
  `bonus_pl` double(8,2) NOT NULL DEFAULT 0.00,
  `confirm_employee_code` varchar(191) DEFAULT NULL,
  `probation_employee_code` varchar(191) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------

--
-- Table structure for table `zones`
--

CREATE TABLE `zones` (
  `id` bigint(20) UNSIGNED NOT NULL,
  `zone` varchar(191) NOT NULL,
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL,
  `city` varchar(191) DEFAULT NULL,
  `property_type` enum('Residential','Commercial') NOT NULL DEFAULT 'Residential',
  `deleted_at` timestamp NULL DEFAULT NULL,
  `city_id` int(11) DEFAULT NULL,
  `project_id` int(11) DEFAULT NULL,
  `ayukta_list_id` varchar(191) DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

--
-- Indexes for dumped tables
--

--
-- Indexes for table `activity_types`
--
ALTER TABLE `activity_types`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `call_dispositions`
--
ALTER TABLE `call_dispositions`
  ADD UNIQUE KEY `code` (`code`),
  ADD KEY `code_2` (`code`);

--
-- Indexes for table `closed`
--
ALTER TABLE `closed`
  ADD PRIMARY KEY (`id`),
  ADD KEY `lead_id` (`lead_id`),
  ADD KEY `created_at` (`created_at`);

--
-- Indexes for table `despositions`
--
ALTER TABLE `despositions`
  ADD PRIMARY KEY (`id`),
  ADD KEY `parent_id` (`parent_id`);

--
-- Indexes for table `desposition_histories`
--
ALTER TABLE `desposition_histories`
  ADD PRIMARY KEY (`id`),
  ADD KEY `cust_number` (`cust_number`),
  ADD KEY `source` (`source`),
  ADD KEY `called_at` (`called_at`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `ayukta_agent_id` (`ayukta_agent_id`),
  ADD KEY `cust_status` (`cust_status`),
  ADD KEY `lead` (`lead`),
  ADD KEY `raw_lead_stage_id` (`raw_lead_stage_id`),
  ADD KEY `idx_dh_cust_stage` (`cust_number`,`raw_lead_stage_id`),
  ADD KEY `idx_dh_cust_id` (`cust_number`,`id`);

--
-- Indexes for table `disposition_leads`
--
ALTER TABLE `disposition_leads`
  ADD PRIMARY KEY (`id`),
  ADD KEY `lead_id` (`lead_id`),
  ADD KEY `disposition_id` (`disposition_id`),
  ADD KEY `agent_id` (`agent_id`),
  ADD KEY `created_at` (`created_at`),
  ADD KEY `date` (`date`),
  ADD KEY `lead_stage` (`lead_stage`),
  ADD KEY `accompanied_by` (`accompanied_by`);

--
-- Indexes for table `invalid_leads`
--
ALTER TABLE `invalid_leads`
  ADD PRIMARY KEY (`id`),
  ADD KEY `lead_id` (`lead_id`),
  ADD KEY `agent_id` (`agent_id`),
  ADD KEY `reports_to` (`reports_to`);

--
-- Indexes for table `leads`
--
ALTER TABLE `leads`
  ADD PRIMARY KEY (`id`),
  ADD KEY `leads_caller_id_foreign` (`caller_id`),
  ADD KEY `leads_desposition_id_foreign` (`desposition_id`),
  ADD KEY `leads_agent_id_foreign` (`agent_id`),
  ADD KEY `cust_name` (`cust_name`),
  ADD KEY `cust_number` (`cust_number`),
  ADD KEY `cust_email` (`cust_email`),
  ADD KEY `lead_assigned_on` (`lead_assigned_on`),
  ADD KEY `hql` (`hql`),
  ADD KEY `invalid_on` (`invalid_on`),
  ADD KEY `closed` (`closed`),
  ADD KEY `is_valid` (`is_valid`),
  ADD KEY `meeting_id` (`meeting_id`),
  ADD KEY `project_id` (`project_id`),
  ADD KEY `loan_agent_id` (`loan_agent_id`),
  ADD KEY `recording_id` (`recording_id`),
  ADD KEY `reassign_agent_id` (`reassign_agent_id`),
  ADD KEY `reassign_caller_id` (`reassign_caller_id`),
  ADD KEY `agent_reports_to_id` (`agent_reports_to_id`),
  ADD KEY `budget_min` (`budget_min`),
  ADD KEY `budget_max` (`budget_max`),
  ADD KEY `lead_source` (`lead_source`);

--
-- Indexes for table `lead_activities`
--
ALTER TABLE `lead_activities`
  ADD PRIMARY KEY (`id`),
  ADD KEY `lead_id` (`lead_id`),
  ADD KEY `caused_by` (`caused_by`),
  ADD KEY `activity_type_id` (`activity_type_id`),
  ADD KEY `created_at` (`created_at`),
  ADD KEY `idx_created_date` (`created_date`);

--
-- Indexes for table `lead_shuffle`
--
ALTER TABLE `lead_shuffle`
  ADD PRIMARY KEY (`ls_id`),
  ADD KEY `lead_shuffle_ls_lead_id_index` (`ls_lead_id`),
  ADD KEY `lead_shuffle_ls_agent_id_index` (`ls_agent_id`);

--
-- Indexes for table `lead_stages`
--
ALTER TABLE `lead_stages`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `meetings`
--
ALTER TABLE `meetings`
  ADD PRIMARY KEY (`id`),
  ADD KEY `meetings_agent_id_foreign` (`agent_id`),
  ADD KEY `meetings_lead_id_foreign` (`lead_id`);

--
-- Indexes for table `raw_leads`
--
ALTER TABLE `raw_leads`
  ADD PRIMARY KEY (`id`),
  ADD KEY `number` (`number`),
  ADD KEY `origin` (`origin`),
  ADD KEY `utm_source` (`utm_source`),
  ADD KEY `utm_campaign` (`utm_campaign`),
  ADD KEY `sent_to_avyukta` (`sent_to_avyukta`),
  ADD KEY `created_at` (`created_at`),
  ADD KEY `leadgen_id` (`leadgen_id`),
  ADD KEY `created_date` (`created_date`),
  ADD KEY `campaign_type` (`campaign_type`),
  ADD KEY `priority` (`priority`),
  ADD KEY `is_in_bucket` (`is_in_bucket`);

--
-- Indexes for table `raw_lead_stages`
--
ALTER TABLE `raw_lead_stages`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `recordings`
--
ALTER TABLE `recordings`
  ADD PRIMARY KEY (`id`),
  ADD KEY `lead_id` (`lead_id`),
  ADD KEY `agent_id` (`agent_id`),
  ADD KEY `transcription_job_name` (`transcription_job_name`);

--
-- Indexes for table `remarks`
--
ALTER TABLE `remarks`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `sales_meetings`
--
ALTER TABLE `sales_meetings`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `sales_recordings`
--
ALTER TABLE `sales_recordings`
  ADD PRIMARY KEY (`id`),
  ADD KEY `user_id` (`user_id`),
  ADD KEY `created_at` (`created_at`),
  ADD KEY `lead_id` (`lead_id`),
  ADD KEY `contact_book_id` (`contact_book_id`),
  ADD KEY `contact` (`contact`),
  ADD KEY `idx_created_date` (`created_date`),
  ADD KEY `transcription_job_name` (`transcription_job_name`);

--
-- Indexes for table `sources`
--
ALTER TABLE `sources`
  ADD PRIMARY KEY (`id`);

--
-- Indexes for table `users`
--
ALTER TABLE `users`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `users_email_unique` (`email`),
  ADD UNIQUE KEY `users_confirm_employee_code_unique` (`confirm_employee_code`),
  ADD UNIQUE KEY `users_probation_employee_code_unique` (`probation_employee_code`),
  ADD KEY `users_role_id_foreign` (`role_id`),
  ADD KEY `enabled` (`enabled`),
  ADD KEY `department_id` (`department_id`);

--
-- Indexes for table `zones`
--
ALTER TABLE `zones`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `activity_types`
--
ALTER TABLE `activity_types`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `closed`
--
ALTER TABLE `closed`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `despositions`
--
ALTER TABLE `despositions`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `desposition_histories`
--
ALTER TABLE `desposition_histories`
  MODIFY `id` bigint(20) NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `disposition_leads`
--
ALTER TABLE `disposition_leads`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `invalid_leads`
--
ALTER TABLE `invalid_leads`
  MODIFY `id` int(10) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `leads`
--
ALTER TABLE `leads`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `lead_activities`
--
ALTER TABLE `lead_activities`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `lead_shuffle`
--
ALTER TABLE `lead_shuffle`
  MODIFY `ls_id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `lead_stages`
--
ALTER TABLE `lead_stages`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `meetings`
--
ALTER TABLE `meetings`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `raw_leads`
--
ALTER TABLE `raw_leads`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `raw_lead_stages`
--
ALTER TABLE `raw_lead_stages`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `recordings`
--
ALTER TABLE `recordings`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `remarks`
--
ALTER TABLE `remarks`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `sales_meetings`
--
ALTER TABLE `sales_meetings`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `sales_recordings`
--
ALTER TABLE `sales_recordings`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `sources`
--
ALTER TABLE `sources`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `users`
--
ALTER TABLE `users`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- AUTO_INCREMENT for table `zones`
--
ALTER TABLE `zones`
  MODIFY `id` bigint(20) UNSIGNED NOT NULL AUTO_INCREMENT;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `users`
--
ALTER TABLE `users`
  ADD CONSTRAINT `users_role_id_foreign` FOREIGN KEY (`role_id`) REFERENCES `roles_bk2` (`id`);
SET FOREIGN_KEY_CHECKS=1;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
