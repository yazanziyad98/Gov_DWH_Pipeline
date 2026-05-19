  CREATE TABLE `salaries` (
  `Source_Type_Code` int NOT NULL,
  `Source_Type_Name` varchar(100) NOT NULL,
  `Work_Type` varchar(100) NOT NULL,
  `DType` varchar(100) NOT NULL,
  `National_Number` varchar(10) NOT NULL,
  `Social_Security_Number` decimal(10,0) NOT NULL,
  `Personal_Number` decimal(10,0) DEFAULT NULL,
  `Card_Number` decimal(10,0) DEFAULT NULL,
  `Salary` decimal(10,3) DEFAULT NULL,
  `Last_Subscription_Date` date DEFAULT NULL,
  `Pension_Type` varchar(200) DEFAULT NULL,
  `Pension_Active` varchar(10) DEFAULT NULL,
  `Sector` varchar(50) DEFAULT NULL,
  `Retired_From_Facility_Name` varchar(750) DEFAULT NULL,
  `Agent_Name` varchar(300) DEFAULT NULL,
  `Last_Active_Subscription_Date` date DEFAULT NULL,
  `Last_Active_subscription_Count` decimal(5,0) DEFAULT NULL,
  `First_Subscription_Date` date DEFAULT NULL,
  `Total_Subscriptions_Count` decimal(5,0) DEFAULT NULL,
  `RATDISB` decimal(10,3) DEFAULT NULL,
  `Workplace_Name` varchar(600) DEFAULT NULL,
  `Workplace_National_Number` decimal(10,0) DEFAULT NULL,
  `Sector_Code` decimal(2,0) DEFAULT NULL,
  `Sub_Sector_Code` decimal(4,0) DEFAULT NULL,
  `Branch_Code` decimal(2,0) DEFAULT NULL,
  `Load_Date` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;





CREATE TABLE `personal_info` (
  `National_Number` varchar(10) NOT NULL,
  `First_Name` varchar(30) DEFAULT NULL,
  `Second_Name` varchar(20) DEFAULT NULL,
  `Third_Name` varchar(20) DEFAULT NULL,
  `Family_Name` varchar(20) DEFAULT NULL,
  `Gender` varchar(1) DEFAULT NULL,
  `Religion_Code` varchar(2) DEFAULT NULL,
  `Social_Status_Code` varchar(2) DEFAULT NULL,
  `Nationality_Code` varchar(3) DEFAULT NULL,
  `Birth_Country_Code` varchar(10) DEFAULT NULL,
  `Birth_Governorate_Code` varchar(2) DEFAULT NULL,
  `Birth_Liwa_Code` varchar(2) DEFAULT NULL,
  `Birth_Kada_Code` varchar(1) DEFAULT NULL,
  `Birth_City_Code` varchar(10) DEFAULT NULL,
  `Birth_Date` date DEFAULT NULL,
  `Father_National_Number` varchar(10) DEFAULT NULL,
  `Mother_National_Number` varchar(10) DEFAULT NULL,
  `Civil_Reg_Office_Code` varchar(3) DEFAULT NULL,
  `Civil_Registration_Number` varchar(7) DEFAULT NULL,
  `Family_Book_Pub_Office_Code` varchar(3) DEFAULT NULL,
  `Family_Book_Number` varchar(7) DEFAULT NULL,
  `Family_Book_Issue_Date` date DEFAULT NULL,
  `Identity_Pub_Office_Code` varchar(3) DEFAULT NULL,
  `Identity_Number` varchar(8) DEFAULT NULL,
  `Identity_Issue_Date` date DEFAULT NULL,
  `Identity_Expired_Date` date DEFAULT NULL,
  `Passport_Pub_Office_Code` varchar(3) DEFAULT NULL,
  `Passport_Number` varchar(8) DEFAULT NULL,
  `Passport_Issue_date` date DEFAULT NULL,
  `Passport_Expired_date` date DEFAULT NULL,
  `Passport_File_Office_Code` varchar(3) DEFAULT NULL,
  `Passport_File_Number` varchar(20) DEFAULT NULL,
  `IS_Alive` varchar(1) DEFAULT NULL,
  `FAM_STS` varchar(2) DEFAULT NULL,
  `Mother_Name` varchar(30) DEFAULT NULL,
  `Birth_Country` varchar(10) DEFAULT NULL,
  `Load_Date` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;









 CREATE TABLE `insured_info` (
  `Social_Security_Number` decimal(10,0) NOT NULL,
  `National_Number` varchar(10) CHARACTER SET utf8mb3 COLLATE utf8mb3_general_ci DEFAULT NULL,
  `Personal_Number` decimal(10,0) DEFAULT NULL,
  `Load_Date` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;









CREATE TABLE `insured_yearly_salary` (
  `Social_Security_Number` decimal(10,0) NOT NULL,
  `Salary_Year` decimal(4,0) NOT NULL,
  `Salary_Amount` decimal(9,1) DEFAULT NULL,
  `Load_Date` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;







 CREATE TABLE `insured_transaction` (
  `Social_Security_Number` decimal(10,0) NOT NULL,
  `Start_Date` date NOT NULL,
  `End_Date` date DEFAULT NULL,
  `Salary_Amount` decimal(9,1) DEFAULT NULL,
  `Load_Date` datetime DEFAULT NULL,
  `message_num` int DEFAULT '0'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
