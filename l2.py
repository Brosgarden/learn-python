import boto3
import csv
import io
import os
from datetime import datetime, timezone

def lambda_handler(event, context):
    aggregator_name = os.environ["AGGREGATOR_NAME"]
    bucket = os.environ["S3_BUCKET"]
    prefix = os.environ.get("S3_KEY_PREFIX", "kms-reports/")

    config = boto3.client("config")

    query = """
    SELECT
      accountId,
      awsRegion,
      resourceId,
      resourceName,
      configuration.keySpec,
      configuration.keyUsage,
      configuration.keyManager,
      configuration.creationDate,
      tags.Application,
      tags.app,
      tags.owner,
      tags.Environment
    WHERE
      resourceType = 'AWS::KMS::Key'
    """

    results = []
    next_token = None

    while True:
        args = {
            "ConfigurationAggregatorName": aggregator_name,
            "Expression": query,
        }
        if next_token:
            args["NextToken"] = next_token

        resp = config.select_aggregate_resource_config(**args)
        results.extend(resp.get("Results", []))
        next_token = resp.get("NextToken")
        if not next_token:
            break

    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow([
        "account_id", "region", "key_id", "name", "key_spec",
        "usage", "manager", "creation_date", "application"
    ])

    for r in results:
        item = eval(r) if isinstance(r, str) else r  # Config returns JSON strings
        tags = {
            "Application": item.get("tags.Application"),
            "app": item.get("tags.app"),
            "owner": item.get("tags.owner"),
            "Environment": item.get("tags.Environment"),
        }
        application = next((v for v in tags.values() if v), "")
        writer.writerow([
            item.get("accountId"),
            item.get("awsRegion"),
            item.get("resourceId"),
            item.get("resourceName"),
            item.get("configuration.keySpec"),
            item.get("configuration.keyUsage"),
            item.get("configuration.keyManager"),
            item.get("configuration.creationDate"),
            application,
        ])

    s3 = boto3.client("s3")
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    key = f"{prefix.rstrip('/')}/kms-query-{ts}.csv"
    s3.put_object(Bucket=bucket, Key=key, Body=csv_buffer.getvalue().encode("utf-8"))

    return {"rows": len(results), "s3_key": key}
