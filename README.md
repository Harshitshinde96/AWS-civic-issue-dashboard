# AWS Civic Issue Reporting Dashboard

## Project Overview

The **AWS Civic Issue Reporting Dashboard** is a cloud-native application designed to crowd-source and manage civic issues (such as potholes, traffic congestion, garbage problems, and street light outages) from the public. 

The core concept is to provide an end-to-end automated pipeline where a user can capture a photo of a civic issue in the field, and the system automatically analyzes, categorizes, and displays it on a public-facing dashboard.

## High-Level Architecture and Flow

The project leverages several AWS services to create a scalable, serverless architecture. Here is the step-by-step flow of how the system works:

1. **User Submission (Frontend):** 
   Citizens interact with a web-based dashboard where they can take a live photo or upload an image of a civic problem. 

2. **API & Initial Processing (API Gateway & Lambda):**
   The uploaded image is sent to an AWS API Gateway endpoint, which triggers a backend AWS Lambda function.

3. **Storage & AI Analysis (S3 & Amazon Rekognition):**
   - The Lambda function securely stores the raw image in an Amazon S3 bucket.
   - It then passes the image to **Amazon Rekognition** (AWS's machine learning image analysis service). Rekognition analyzes the image and returns descriptive labels (e.g., "asphalt", "damage", "trash").

4. **Categorization & Data Persistence (RDS MySQL):**
   - Based on the AI-generated labels, the backend logic categorizes the issue into predefined buckets like "Plot Holes" or "Garbage Problem".
   - The categorization, AI confidence score, and the image's S3 URL are saved in an Amazon RDS MySQL database.

5. **Data Aggregation (Lambda):**
   - A separate data-aggregation Lambda function connects to the RDS database to fetch the latest reported issues.
   - It structures this data into a comprehensive JSON payload and pushes it as a static feed to an Amazon S3 bucket. 

6. **Dashboard Consumption:**
   - Instead of continuously querying a live database, the frontend dashboard periodically fetches the lightweight JSON feed directly from S3. 
   - This approach ensures the dashboard remains fast, scalable, and highly available, instantly displaying newly reported and categorized issues to the public.

## Summary of Accomplishments

In this AWS project, we have successfully:
- Built a serverless ingestion pipeline for user-generated content using API Gateway and AWS Lambda.
- Integrated AI-driven image recognition (Amazon Rekognition) to automate the categorization of civic issues.
- Established a robust relational database (Amazon RDS) to persist report data.
- Optimized frontend performance by decoupling database reads from the user interface using a static, auto-refreshing S3 JSON feed.