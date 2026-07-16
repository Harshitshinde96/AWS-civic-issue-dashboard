import base64
import json
import uuid

import boto3
import pymysql  # Requires PyMySQL Layer

s3 = boto3.client("s3")
rekognition = boto3.client("rekognition")

# RDS Config (Use Environment Variables in production!)
RDS_HOST = "database-1.c5oi4cio6lqj.ap-south-1.rds.amazonaws.com"
RDS_USER = "admin"
RDS_PASS = "pass1234"
RDS_DB = "CivicIssuesDB"
BUCKET = "civic-issue-tracker-assets"


def get_category(labels):
    # Mapping logic for your 4 categories
    label_names = [l["Name"].lower() for l in labels]

    if any(word in label_names for word in ["pothole", "road damage", "cracks"]):
        return "Plot Holes"
    if any(
        word in label_names for word in ["traffic", "cars", "traffic jam", "vehicle"]
    ):
        return "Traffic"
    if any(word in label_names for word in ["garbage", "trash", "litter", "waste"]):
        return "Garbage Problem"
    if any(word in label_names for word in ["street light", "lamp", "lamp post"]):
        return "Street Light Problem"

    return "Other (Uncategorized)"


def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
        image_data = body.get("image")
        issue_id = str(uuid.uuid4())

        # 1. Save Image to S3
        img_bytes = base64.b64decode(image_data.split(",")[-1])
        img_key = f"uploads/{issue_id}.jpg"
        s3.put_object(
            Bucket=BUCKET, Key=img_key, Body=img_bytes, ContentType="image/jpeg"
        )
        img_url = f"https://{BUCKET}.s3.amazonaws.com/{img_key}"

        # 2. Analyze with Rekognition
        rek_res = rekognition.detect_labels(
            Image={"S3Object": {"Bucket": BUCKET, "Name": img_key}}, MaxLabels=10
        )
        labels = rek_res.get("Labels", [])

        # 3. Categorize
        category = get_category(labels)
        top_confidence = labels[0]["Confidence"] if labels else 0.0
        raw_labels = json.dumps([l["Name"] for l in labels])

        # 4. Save to RDS
        conn = pymysql.connect(
            host=RDS_HOST, user=RDS_USER, password=RDS_PASS, database=RDS_DB
        )
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO ReportedIssues (IssueId, Category, ConfidenceScore, ImageUrl, RawLabels) VALUES (%s, %s, %s, %s, %s)",
                (issue_id, category, top_confidence, img_url, raw_labels),
            )
        conn.commit()
        conn.close()

        return {
            "statusCode": 200,
            "headers": {"Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"status": "success", "category": category}),
        }

    except Exception as e:
        print(f"Error: {str(e)}")  # Goes to CloudWatch
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
