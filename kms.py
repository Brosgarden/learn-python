import boto3
import os
import csv
import io
import json
from datetime import datetime, timezone

def lambda_handler(event, context):
    aggregator_name = os.environ["AGGREGATOR_NAME"]
    bucket = os.environ["S3_BUCKET"]
    prefix = os.environ.get("S3_KEY_PREFIX", "kms-reports/")

    config = boto3.client("config")

    # Step 1: list all KMS keys known to the aggregator
    paginator = config.get_paginator("list_aggregate_discovered_resources")
    kms_ids = []
    for page in paginator.paginate(
        ConfigurationAggregatorName=aggregator_name,
        ResourceType="AWS::KMS::Key"
    ):
        for rid in page.get("ResourceIdentifiers", []):
            kms_ids.append(rid)

    # Step 2: fetch details in batches (up to 20 per call)
    rows = []
    for i in range(0, len(kms_ids), 20):
        batch = kms_ids[i:i+20]
        resp = config.batch_get_aggregate_resource_config(
            ConfigurationAggregatorName=aggregator_name,
            ResourceIdentifiers=batch
        )
        for item in resp.get("BaseConfigurationItems", []):
            conf = json.loads(item["configuration"]) if item.get("configuration") else {}

            key_spec = conf.get("keySpec")
            size_bits = {
                "RSA_2048": 2048, "RSA_3072": 3072, "RSA_4096": 4096,
                "ECC_NIST_P256": 256, "ECC_NIST_P384": 384, "ECC_NIST_P521": 521,
                "ECC_SECG_P256K1": 256, "SYMMETRIC_DEFAULT": 256,
            }.get(key_spec, "")

            # pull application tag if present
            application = ""
            tags = conf.get("tags") or []
            for t in tags:
                k = t.get("key") or t.get("Key")
                v = t.get("value") or t.get("Value")
                if k and k.lower() in ["application", "app", "owner"]:
                    application = v
                    break

            rows.append([
                item.get("resourceId"),
                json.dumps({k: conf.get(k) for k in ("keyId","arn","keyState","keySpec","keyUsage")}),
                key_spec or conf.get("keyUsage"),
                size_bits,
                conf.get("creationDate", item.get("configurationItemCaptureTime")),
                application
            ])

    # Step 3: write CSV
    csv_buffer = io.StringIO()
    writer = csv.writer(csv_buffer)
    writer.writerow(["id","configuration","type","size","creation_date","application"])
    for r in rows:
        writer.writerow(r)

    s3 = boto3.client("s3")
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    key = f"{prefix.rstrip('/')}/kms-aggregator-{ts}.csv"
    s3.put_object(Bucket=bucket, Key=key, Body=csv_buffer.getvalue().encode("utf-8"))

    return {"rows": len(rows), "s3_key": key}
