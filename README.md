# manufacturing-reporting-analytics
My SQL and Power BI project exploring manufacturing, produ# manufacturing-reporting-analytics

I wanted to practice working through a full analytics workflow, starting from raw data and ending with a dashboard that actually answers useful questions.
The dataset simulates pulp manufacturing operations across several mills. It includes things like machine production, planned vs actual output, machine downtime, and material purchasing costs.

Instead of just exploring the data randomly, I tried to approach it like a real analysis problem:
What would plant managers want to know?
What would help them understand production performance?
Where are the inefficiencies or cost drivers?

To answer those questions, I built a pipeline using PostgreSQL for data preparation and Power BI for analysis and visualization.

# What the Data Is About?

The dataset represents pulp production across three mills:
Durban Mill
Pietermaritzburg Mill
Richards Bay Mill

The data includes three main areas of information:
Machine performance
Machine ID
Actual production
Planned production
Machine throughput
Machine downtime

Production output
Total tons produced
Production by machine
Production by mill

Materials
Raw materials used in production
Material purchasing costs
Material spending by plant

Together these pieces make it possible to look at both operational performance and cost patterns.

# Questions I Tried To Answer
When I started building the dashboard I tried to frame the analysis around questions a production manager might ask:

Which machines are producing the most output?
Are we hitting our planned production targets?
Which machines experience the most downtime?
Which mill produces the most pulp?
Which materials contribute the most to cost?
Do different mills spend differently on materials?
Overall, how efficiently are we producing compared to plan?

The dashboard is designed to help answer those questions quickly.

Working With The Data (SQL)
The raw dataset was loaded into PostgreSQL.
From there I started writing SQL to reshape the data into something easier to analyze.
Instead of querying the raw tables directly in Power BI, I created analytics views that aggregate the data first.

# The basic idea was:

Raw tables
→ SQL transformations
→ Analytics views
→ Power BI dashboard

For example, this view summarizes machine performance:
CREATE VIEW analytics_vw_machine_summary AS 
SELECT machine_id, plant, SUM(actual_production) AS actual_production, 
SUM(planned_production) AS planned_production, AVG(downtime_minutes) AS downtime, AVG(throughput) AS throughput 
FROM machine_performance 
GROUP BY machine_id, plant;

This creates a cleaner dataset for the dashboard to use.

# Building The Dashboard
After preparing the data in SQL, I connected the views to Power BI.
From there I built two dashboard pages.

# Manufacturing Performance

This page focuses on machine performance and production output.
It shows things like:
Average machine downtime
Best machine throughput
Total tons produced
Actual vs planned production by machine
Production distribution across mills
This helps identify which machines are performing well and where there might be operational issues.
![Dashboard](screenshots/Dashboard1.png)

# Mill and Material Analysis

The second page focuses more on cost.
It looks at:
Total material cost by plant
Cost breakdown of materials
Which materials contribute the most to spending
This gives a sense of where production costs are coming from.

DAX Measure I Added
To include at least one analytical calculation in the dashboard, I created a DAX measure to calculate production efficiency.
The idea is simple: compare actual production against planned production.

Efficiency = DIVIDE( SUM(analytics_vw_machine_summary[actual_production]), SUM(analytics_vw_machine_summary[planned_production]) )
This gives a quick sense of whether production is meeting expectations.
![Dashboard](screenshots/Dashboard2.png)

# What I Noticed From The Dashboard

A few things stood out while exploring the visuals:
Some machines clearly outperform others in throughput.
Machine downtime varies quite a bit across machines.
Durban Mill contributes a large share of total production.
Certain raw materials dominate overall cost.
Material spending patterns differ slightly between mills.
These kinds of patterns are exactly the type of things dashboards are meant to highlight quickly.

# Tools Used

PostgreSQL — storing the dataset and writing SQL transformations
Power BI — building the dashboard and visualizing the data
DAX — calculating production efficiency
GitHub — documenting the project and version control

# Final Thoughts

This project was mainly about practicing the full workflow of a data analyst:
Start with raw data
Transform it using SQL
Build analytical views
Create a dashboard that answers real questions
It helped me get more comfortable thinking about how data moves from raw tables to useful insights.

