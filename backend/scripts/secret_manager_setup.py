#!/usr/bin/env python3
"""
Bootstrap a Google Secret Manager secret with a service account JSON key.

Usage:
  python backend/scripts/secret_manager_setup.py --project <PROJECT_ID> \
      --secret <SECRET_NAME> --key-file </path/to/sa_key.json>

Requires Application Default Credentials or GOOGLE_APPLICATION_CREDENTIALS
with permissions: roles/secretmanager.admin or appropriate granular roles.

This script will:
- Create the secret if it does not exist
- Add the provided key file content as a new secret version
"""

import argparse
import json
import os
import sys
from typing import Optional

from google.api_core.exceptions import AlreadyExists, NotFound
from google.cloud import secretmanager


def ensure_secret(
    client: secretmanager.SecretManagerServiceClient,
    project_id: str,
    secret_id: str,
    replication: Optional[secretmanager.Replication] = None,
) -> None:
    parent = f"projects/{project_id}"
    name = f"{parent}/secrets/{secret_id}"
    try:
        client.get_secret(request={"name": name})
        print(f"Secret already exists: {name}")
        return
    except NotFound:
        pass

    if replication is None:
        replication = secretmanager.Replication(
            automatic=secretmanager.Replication.Automatic()
        )

    try:
        client.create_secret(
            request={
                "parent": parent,
                "secret_id": secret_id,
                "secret": {"replication": replication},
            }
        )
        print(f"Created secret: {name}")
    except AlreadyExists:
        print(f"Secret already exists: {name}")


def add_secret_version(
    client: secretmanager.SecretManagerServiceClient, project_id: str, secret_id: str, data: bytes
) -> str:
    parent = f"projects/{project_id}/secrets/{secret_id}"
    response = client.add_secret_version(
        request={"parent": parent, "payload": {"data": data}}
    )
    return response.name


def main() -> int:
    parser = argparse.ArgumentParser(description="Setup Secret Manager with SA key JSON")
    parser.add_argument("--project", required=True, help="GCP project ID")
    parser.add_argument("--secret", required=True, help="Secret name (e.g., medsearch-sa-key)")
    parser.add_argument("--key-file", required=True, help="Path to service account JSON key file")
    args = parser.parse_args()

    # Basic validation of the key file
    if not os.path.exists(args.key_file):
        print(f"Key file not found: {args.key_file}", file=sys.stderr)
        return 2

    with open(args.key_file, "r") as f:
        payload = f.read().strip()

    try:
        data = json.loads(payload)
        if not isinstance(data, dict) or data.get("type") != "service_account":
            print("Provided file is not a service account key JSON", file=sys.stderr)
            return 3
    except json.JSONDecodeError:
        print("Provided file is not valid JSON", file=sys.stderr)
        return 3

    # Initialize client (ADC or GOOGLE_APPLICATION_CREDENTIALS)
    client = secretmanager.SecretManagerServiceClient()

    # Create secret if missing
    ensure_secret(client, args.project, args.secret)

    # Add new version
    version_name = add_secret_version(client, args.project, args.secret, payload.encode("utf-8"))

    print("Added new secret version:", version_name)
    print()
    print("Next steps:")
    print("  1) Export env vars for your app:")
    print(f"     export SECRET_MANAGER_SECRET_NAME={args.secret}")
    print("     export SECRET_MANAGER_SECRET_VERSION=latest")
    print(f"     export GOOGLE_CLOUD_PROJECT={args.project}")
    print("  2) Unset GOOGLE_APPLICATION_CREDENTIALS to let the app load from Secret Manager automatically")
    print("     unset GOOGLE_APPLICATION_CREDENTIALS")
    print("  3) Start the backend; it will fetch the secret and write /tmp/medsearch-sa.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

