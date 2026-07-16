import json
import boto3
import pymysql
import logging
from decimal import Decimal
from datetime import datetime

# Set up logging for AWS CloudWatch
logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3 = boto3.client('s3')

# RDS Config (Match your actual credentials)
RDS_HOST = "database-1.c5oi4cio6lqj.ap-south-1.rds.amazonaws.com"
RDS_USER = "admin"
RDS_PASS = "pass1234"
RDS_DB = "CivicIssuesDB"
BUCKET = "civic-issue-tracker-assets"

# Helper to fix JSON serialization for Decimals and Datetimes coming from MySQL
class CustomEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super(CustomEncoder, self).default(obj)

def lambda_handler(event, context):
    logger.info("Lambda execution started.")
    logger.info(f"Event received: {json.dumps(event)}")
    
    try:
        logger.info(f"Attempting to connect to RDS: {RDS_HOST}, Database: {RDS_DB}")
        conn = pymysql.connect(host=RDS_HOST, user=RDS_USER, password=RDS_PASS, database=RDS_DB, cursorclass=pymysql.cursors.DictCursor)
        logger.info("Successfully connected to the database.")
        
        with conn.cursor() as cur:
            logger.info("Executing query to fetch reported issues...")
            cur.execute("SELECT * FROM ReportedIssues ORDER BY ReportedAt DESC")
            rows = cur.fetchall()
            logger.info(f"Successfully fetched {len(rows)} records from the database.")
            
        conn.close()
        logger.info("Database connection closed.")

        # Structure the data for the frontend dashboard
        dashboard_data = {
            "last_updated": datetime.utcnow().isoformat() + "Z",
            "categories": {
                "Plot Holes": [],
                "Traffic": [],
                "Garbage Problem": [],
                "Street Light Problem": [],
                "Other (Uncategorized)": []
            }
        }

        logger.info("Categorizing records...")
        # Sort rows into their respective category arrays
        for row in rows:
            cat = row.get('Category', 'Other (Uncategorized)')
            
            # Parse the RawLabels string back into an actual JSON array
            try:
                if row.get('RawLabels'):
                    row['RawLabels'] = json.loads(row['RawLabels'])
                else:
                    row['RawLabels'] = []
            except Exception as e:
                logger.warning(f"Failed to parse RawLabels for IssueId {row.get('IssueId')}. Error: {str(e)}")
                row['RawLabels'] = []
                
            if cat in dashboard_data["categories"]:
                dashboard_data["categories"][cat].append(row)
            else:
                dashboard_data["categories"]["Other (Uncategorized)"].append(row)

        logger.info("Categorization complete. Generating JSON payload...")
        # Convert the dictionary to a JSON string using our CustomEncoder
        json_payload = json.dumps(dashboard_data, cls=CustomEncoder)
        payload_size_kb = len(json_payload.encode('utf-8')) / 1024
        logger.info(f"JSON payload generated successfully. Size: {payload_size_kb:.2f} KB.")
        logger.info(f"Payload content to be written to S3:\n{json_payload}")

        logger.info(f"Uploading payload to S3 Bucket: {BUCKET} with Key: test.json")
        # Push the static JSON file to S3
        s3.put_object(
            Bucket=BUCKET,
            Key='test.json',
            Body=json_payload,
            ContentType='application/json',
            CacheControl='max-age=120' # Tells browsers not to cache it longer than our 2-min sync
        )
        logger.info("Upload to S3 complete.")

        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Dashboard test feed updated successfully.'})
        }

    except Exception as e:
        logger.error(f"Aggregation Error: {str(e)}", exc_info=True)
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }
