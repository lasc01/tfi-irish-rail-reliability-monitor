# TFI and Irish Rail Transport Data Reliability Monitor

## Project Overview

This project is a real world transport data reliability pipeline built with Python, PostgreSQL, SQL and Power BI.

The goal of the project is to monitor live public transport data from Transport for Ireland and Irish Rail, store ingestion batches, validate data quality, and produce a simple operational dashboard that shows whether the pipeline worked, how much data was processed, and what issues were detected.

The project was designed to reflect the kind of work carried out in transport data environments, where analysts and data engineers need to validate time based operational feeds, check missing records, detect duplicates, log failed batches, and build reliable reporting outputs for stakeholders.

## Why I Built This Project

In transport data work, the challenge is not only collecting data. The bigger challenge is knowing whether the data can be trusted.

A dashboard showing bus, train or route information is only useful if the underlying data is complete, fresh, correctly mapped, and properly validated. This project focuses on that reality.

The pipeline checks live transport feeds, logs each ingestion run, stores successful and failed batches, runs quality checks, and exposes clean reporting views for Power BI.

## Data Sources

The project uses two Irish transport data sources.

1. Transport for Ireland GTFS Realtime API  
   Used for live public transport trip update records.

2. Irish Rail Realtime API  
   Used for current train snapshot data.

The TFI feed contributes the larger share of records, while Irish Rail provides a smaller but useful train monitoring feed.

## Tools and Technologies

1. Python  
   Used for API ingestion, XML parsing, GTFS Realtime parsing, data transformation, quality checks, and scheduled pipeline runs.

2. PostgreSQL  
   Used as the main database for storing ingestion batches, transport records, and data quality results.

3. SQL  
   Used to create schemas, validation views, reporting views, KPI views, and dashboard ready tables.

4. Power BI  
   Used to build the final one page transport reliability dashboard.

5. WSL  
   Used as the development environment for Python and PostgreSQL.

## Project Architecture

```text
TFI GTFS Realtime API
        |
        v
Python TFI ingestion script
        |
        v
PostgreSQL transport schema
        |
        v
SQL quality and reporting views
        |
        v
Power BI dashboard


Irish Rail Realtime API
        |
        v
Python Irish Rail ingestion script
        |
        v
PostgreSQL transport schema
        |
        v
SQL quality and reporting views
        |
        v
Power BI dashboard
