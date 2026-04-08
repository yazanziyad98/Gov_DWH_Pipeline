GO
CREATE TABLE [dbo].[SSC_Salaries](
	[Source_Type_Code] [numeric](1, 0) NOT NULL,
	[Source_Type_Name] [nvarchar](100) NOT NULL,
	[Work_Type] [nvarchar](100) NOT NULL,
	[DType] [nvarchar](100) NOT NULL,
	[National_Numer] [nvarchar](10) NOT NULL,
	[Social_Security_Number] [numeric](10, 0) NOT NULL,
	[Personal_Number] [numeric](10, 0) NULL,
	[Card_Number] [numeric](10, 0) NULL,
	[Salary] [numeric](10, 3) NULL,
	[Last_Subscription_Date] [date] NULL,
	[Pension_Type] [nvarchar](200) NULL,
	[Pension_Active] [nvarchar](10) NULL,
	[Sector] [nvarchar](50) NULL,
	[Retired_From_Facility_Name] [nvarchar](750) NULL,
	[Agent_Name] [nvarchar](300) NULL,
	[Last_Active_Subscription_Date] [date] NULL,
	[Last_Active_subscription_Count] [numeric](5, 0) NULL,
	[First_Subscription_Date] [date] NULL,
	[Total_Subscriptions_Count] [numeric](5, 0) NULL,
	[RATDISB] [numeric](10, 3) NULL,
	[Workplace_Name] [nvarchar](600) NULL,
	[Workplace_National_Number] [numeric](10, 0) NULL,
	[Sector_Code] [numeric](2, 0) NULL,
	[Sub_Sector_Code] [numeric](4, 0) NULL,
	[Branch_Code] [numeric](2, 0) NULL
) ON [PRIMARY]
GO




GO
	CREATE TABLE [dbo].[CSPD_Personal_Info](
		[National_Number] [nvarchar](10) NOT NULL,
		[First_Name] [nvarchar](30) NULL,
		[Second_Name] [nvarchar](20) NULL,
		[Third_Name] [nvarchar](20) NULL,
		[Family_Name] [nvarchar](20) NULL,
		[Gender] [nvarchar](1) NULL,
		[Religion_Code] [nvarchar](2) NULL,
		[Social_Status_Code] [nvarchar](2) NULL,
		[Nationality_Code] [nvarchar](3) NULL,
		[Birth_Country_Code] [nvarchar](3) NULL,
		[Birth_Governorate_Code] [nvarchar](2) NULL,
		[Birth_Liwa_Code] [nvarchar](2) NULL,
		[Birth_Kada_Code] [nvarchar](1) NULL,
		[Birth_City_Code] [nvarchar](3) NULL,
		[Birth_Date] [date] NULL,
		[Father_National_Number] [nvarchar](10) NULL,
		[Mother_National_Number] [nvarchar](10) NULL,
		[Civil_Reg_Office_Code] [nvarchar](3) NULL,
		[Civil_Registration_Number] [nvarchar](7) NULL,
		[Family_Book_Pub_Office_Code] [nvarchar](3) NULL,
		[Family_Book_Number] [nvarchar](7) NULL,
		[Family_Book_Issue_Date] [date] NULL,
		[Identity_Pub_Office_Code] [nvarchar](3) NULL,
		[Identity_Number] [nvarchar](8) NULL,
		[Identity_Issue_Date] [date] NULL,
		[Identity_Expired_Date] [date] NULL,
		[Passport_Pub_Office_Code] [nvarchar](3) NULL,
		[Passport_Number] [nvarchar](8) NULL,
		[Passport_Issue_date] [date] NULL,
		[Passport_Expired_date] [date] NULL,
		[Passport_File_Office_Code] [nvarchar](3) NULL,
		[Passport_File_Number] [nvarchar](20) NULL,
		[IS_Alive] [nvarchar](1) NULL,
		[FAM_STS] [nvarchar](2) NULL,
		[First_Name_En] [nvarchar](30) NULL,
		[Second_Name_En] [nvarchar](20) NULL,
		[Third_Name_En] [nvarchar](20) NULL,
		[Family_Name_En] [nvarchar](20) NULL,
		[Mother_Name] [nvarchar](30) NULL
	) ON [PRIMARY]
GO








CREATE TABLE [dbo].[SSC_Insured_Info](
	[Social_Security_Number] [numeric](10, 0) NOT NULL,
	[National_Number] [nvarchar](10) NULL,
	[Personal_Number] [numeric](10, 0) NULL
) ON [PRIMARY]








CREATE TABLE [dbo].[SSC_Insured_Yearly_Salary](
	[Social_Security_Number] [numeric](10, 0) NOT NULL,
	[Salary_Year] [numeric](4, 0) NOT NULL,
	[Salary_Amount] [numeric](9, 3) NULL
) ON [PRIMARY]







CREATE TABLE [dbo].[SSC_Insured_Transaction](
	[Social_Security_Number] [numeric](10, 0) NOT NULL,
	[Start_Date] [date] NOT NULL,
	[End_Date] [date] NULL,
	[Salary_Amount] [numeric](9, 3) NULL
) ON [PRIMARY]