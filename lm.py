"""
Lambda: query AWS Config in another account for KMS keys, build CSV, upload to S3.
Python 3.11, boto3.

Environment variables (required):
- TARGET_ROLE_ARN: ARN of role in the target account that the lambda will assume (e.g. arn:aws:iam::123456789012:role/ConfigReadRole)
- S3_BUCKET: S3 bucket name (in this account) to upload CSV
- S3_KEY_PREFIX: (optional) prefix/path for uploaded file, default "kms-reports/"
- REGION: (optional) AWS region to use for Config and S3 operations. Default from Lambda env.

Permissions required for Lambda's execution role (in its account):
- sts:AssumeRole  (to assume TARGET_ROLE_ARN)
- s3:PutObject on the S3_BUCKET
- config: (not needed in own account since calls to target account use assumed creds)
"""

import os
import json
import csv
import io
import time
from datetime import datetime, timezone

import boto3
from botocore.exceptions import ClientError, BotoCoreError

# --- Helpers ---------------------------------------------------------------

def assume_role(role_arn, session_name="crossaccount-config-reader", duration_seconds=900):
    sts = boto3.client("sts")
    resp = sts.assume_role(RoleArn=role_arn, RoleSessionName=session_name, DurationSeconds=duration_seconds)
    creds = resp["Credentials"]
    return {
        "aws_access_key_id": creds["AccessKeyId"],
        "aws_secret_access_key": creds["SecretAccessKey"],
        "aws_session_token": creds["SessionToken"],
    }

def paginate_list_discovered_resources(config_client, resource_type="AWS::KMS::Key"):
    """Yield resourceIdentifiers from list_discovered_resources (handles pagination)."""
    paginator = config_client.get_paginator("list_discovered_resources")
    for page in paginator.paginate(resourceType=resource_type):
        for ri in page.get("resourceIdentifiers", []):
            yield ri

def get_latest_configuration_item(config_client, resource_type, resource_id):
    """
    Use get_resource_config_history to get the latest configuration item for the resource.
    Returns parsed configuration dict, or None.
    """
    try:
        resp = config_client.get_resource_config_history(
            resourceType=resource_type,
            resourceId=resource_id,
            limit=1
        )
        items = resp.get("configurationItems", [])
        if not items:
            return None
        ci = items[0]
        # configuration is JSON string in 'configuration'
        config_str = ci.get("configuration")
        config_obj = None
        if config_str:
            try:
                config_obj = json.loads(config_str)
            except Exception:
                config_obj = {"raw": config_str}
        # include top-level metadata for fallback
        ci_meta = {
            "resourceType": ci.get("resourceType"),
            "resourceId": ci.get("resourceId"),
            "resourceName": ci.get("resourceName"),
            "awsAccountId": ci.get("awsAccountId"),
            "configurationItemCaptureTime": ci.get("configurationItemCaptureTime"),
            "configurationItemStatus": ci.get("configurationItemStatus"),
        }
        return {"configuration": config_obj, "metadata": ci_meta}
    except (ClientError, BotoCoreError) as e:
        print(f"Error fetching config history for {resource_id}: {e}")
        return None

def derive_size_from_key_spec(key_spec):
    """Try to convert AWS KMS KeySpec to a numeric size (bits)."""
    if not key_spec:
        return ""
    mapping = {
        "RSA_2048": 2048,
        "RSA_3072": 3072,
        "RSA_4096": 4096,
        "ECC_NIST_P256": 256,
        "ECC_NIST_P384": 384,
        "ECC_NIST_P521": 521,
        "ECC_SECG_P256K1": 256,
        "SYMMETRIC_DEFAULT": 256,
        "AES_256": 256,
        "AES_128": 128,
        # add more if needed
    }
    return mapping.get(key_spec, "")

def extract_application_from_config(conf_obj):
    """
    Try to find an application tag or an 'application' string in description.
    conf_obj is the parsed 'configuration' JSON from AWS Config (which reflects the KMS Key Resource).
    """
    if not conf_obj or not isinstance(conf_obj, dict):
        return ""
    # tags may be under 'tags' as list of dicts or dict
    # AWS Config representation sometimes includes 'tags' list of {'key':..., 'value':...}
    tags = conf_obj.get("tags") or conf_obj.get("Tags") or {}
    app = ""
    # handle dict-style tags: { "TagKey": "TagValue", ... }
    if isinstance(tags, dict):
        for candidate in ("Application", "application", "app", "App", "Owner", "owner"):
            if candidate in tags:
                app = tags[candidate]
                break
    elif isinstance(tags, list):
        for t in tags:
            # t might be { "key": "...", "value": "..." } or { "Key":..., "Value":... }
            key = t.get("key") or t.get("Key")
            value = t.get("value") or t.get("Value")
            if not key:
                continue
            if key.lower() in ("application", "app", "owner"):
                app = value
                break

    if not app:
        # fallback: check description field for "app:" or "application="
        desc = conf_obj.get("description") or conf_obj.get("Description") or ""
        if desc and isinstance(desc, str):
            # naive parsing
            lower = desc.lower()
            # look for patterns
            for token in ("application=", "application:", "app=", "app:"):
                if token in lower:
                    try:
                        # extract after token up to comma or end
                        idx = lower.index(token) + len(token)
                        rest = desc[idx:].split(",")[0].split(";")[0].strip()
                        app = rest
                        break
                    except Exception:
                        pass
    return app or ""

# --- Main Lambda handler --------------------------------------------------

def lambda_handler(event, context):
    # Load env
    TARGET_ROLE_ARN = os.environ.get("TARGET_ROLE_ARN")
    S3_BUCKET = os.environ.get("S3_BUCKET")
    S3_KEY_PREFIX = os.environ.get("S3_KEY_PREFIX", "kms-reports/")
    REGION = os.environ.get("REGION")  # optional

    if not TARGET_ROLE_ARN or not S3_BUCKET:
        return {"statusCode": 400, "body": "Missing TARGET_ROLE_ARN or S3_BUCKET environment variables"}

    # assume role in target account
    try:
        assumed_creds = assume_role(TARGET_ROLE_ARN)
    except Exception as e:
        print("Error assuming role:", e)
        return {"statusCode": 500, "body": f"Error assuming role: {e}"}

    # create config client in target account using assumed creds
    session_args = dict(
        aws_access_key_id=assumed_creds["aws_access_key_id"],
        aws_secret_access_key=assumed_creds["aws_secret_access_key"],
        aws_session_token=assumed_creds["aws_session_token"],
    )
    if REGION:
        session_args["region_name"] = REGION

    target_session = boto3.Session(**session_args)
    config_client = target_session.client("config")

    # Prepare CSV in memory
    csv_buffer = io.StringIO()
    csv_writer = csv.writer(csv_buffer)
    header = ["id", "configuration_summary", "type", "size_bits", "creation_date", "application"]
    csv_writer.writerow(header)

    resource_type = "AWS::KMS::Key"
    count = 0

    try:
        for ri in paginate_list_discovered_resources(config_client, resource_type=resource_type):
            resource_id = ri.get("resourceId")  # often this is the KMS Key ID or ARN
            resource_arn = ri.get("resourceArn")
            # prefer resourceArn if available as id
            id_field = resource_arn or resource_id or ""

            conf_item = get_latest_configuration_item(config_client, resource_type, resource_id)
            if not conf_item:
                # write a row with what we have
                csv_writer.writerow([id_field, "", "", "", "", ""])
                continue

            conf = conf_item.get("configuration") or {}
            meta = conf_item.get("metadata") or {}

            # configuration summary: keep some key fields compacted as JSON string
            cfg_summary = {}
            # try to extract common KMS fields
            for k in ("keyId", "arn", "keyState", "keySpec", "keyUsage", "origin", "description", "keyManager"):
                if k in conf:
                    cfg_summary[k] = conf[k]
            # include tags if small
            if "tags" in conf:
                cfg_summary["tags"] = conf.get("tags")

            # type: prefer keySpec then keyUsage then keyManager
            key_spec = conf.get("keySpec") or conf.get("KeySpec") or ""
            key_usage = conf.get("keyUsage") or conf.get("KeyUsage") or ""
            key_manager = conf.get("keyManager") or conf.get("KeyManager") or ""
            type_field = key_spec or key_usage or key_manager

            size_bits = derive_size_from_key_spec(key_spec)

            # creation date: try configuration capture time or conf field 'creationDate'
            creation_date = ""
            # conf may include 'creationDate' as ISO or epoch. Try common fields.
            if conf.get("creationDate"):
                cd = conf.get("creationDate")
                # if a number, convert from epoch
                if isinstance(cd, (int, float)):
                    creation_date = datetime.fromtimestamp(cd, tz=timezone.utc).isoformat()
                else:
                    creation_date = str(cd)
            else:
                # fallback to metadata capture time
                capture = meta.get("configurationItemCaptureTime")
                if capture:
                    # capture may already be ISO
                    creation_date = str(capture)

            application = extract_application_from_config(conf)

            cfg_json_short = json.dumps(cfg_summary, default=str)

            csv_writer.writerow([id_field, cfg_json_short, type_field, size_bits, creation_date, application])
            count += 1

    except Exception as e:
        print("Error while reading resources:", e)
        return {"statusCode": 500, "body": f"Error reading resources: {e}"}

    # prepare upload key
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    s3_key = f"{S3_KEY_PREFIX.rstrip('/')}/kms-config-{timestamp}.csv"

    # upload CSV to S3 (in this account)
    s3 = boto3.client("s3", region_name=REGION) if REGION else boto3.client("s3")
    csv_buffer.seek(0)
    try:
        s3.put_object(Bucket=S3_BUCKET, Key=s3_key, Body=csv_buffer.getvalue().encode("utf-8"))
    except Exception as e:
        print("Error uploading to S3:", e)
        return {"statusCode": 500, "body": f"Error uploading to S3: {e}"}

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "CSV created",
            "rows": count,
            "s3_bucket": S3_BUCKET,
            "s3_key": s3_key
        })
    }
