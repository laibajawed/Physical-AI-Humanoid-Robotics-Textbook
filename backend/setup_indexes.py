"""
Setup Qdrant Payload Indexes for Filtering

This script creates payload indexes on the rag_embedding collection
to enable efficient filtering by source_url and section fields.

Run this once after creating the collection:
    python setup_indexes.py
"""

import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import PayloadSchemaType


COLLECTION_NAME = "rag_embedding"


def setup_payload_indexes():
    """Create payload indexes for efficient filtering."""
    load_dotenv()

    url = os.getenv("QDRANT_URL")
    api_key = os.getenv("QDRANT_API_KEY")

    if not url or not api_key:
        raise EnvironmentError("Missing QDRANT_URL or QDRANT_API_KEY environment variables")

    client = QdrantClient(url=url, api_key=api_key)

    print(f"Setting up payload indexes for collection '{COLLECTION_NAME}'...")

    # Create text index for source_url (enables prefix/substring matching)
    try:
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="source_url",
            field_schema=PayloadSchemaType.TEXT,
        )
        print("  - Created TEXT index on 'source_url'")
    except Exception as e:
        if "already exists" in str(e).lower():
            print("  - Index on 'source_url' already exists")
        else:
            print(f"  - Warning: Could not create index on 'source_url': {e}")

    # Create keyword index for section (enables exact matching)
    try:
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="section",
            field_schema=PayloadSchemaType.KEYWORD,
        )
        print("  - Created KEYWORD index on 'section'")
    except Exception as e:
        if "already exists" in str(e).lower():
            print("  - Index on 'section' already exists")
        else:
            print(f"  - Warning: Could not create index on 'section': {e}")

    # Create keyword index for title (enables exact matching)
    try:
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="title",
            field_schema=PayloadSchemaType.KEYWORD,
        )
        print("  - Created KEYWORD index on 'title'")
    except Exception as e:
        if "already exists" in str(e).lower():
            print("  - Index on 'title' already exists")
        else:
            print(f"  - Warning: Could not create index on 'title': {e}")

    print("Done! Payload indexes are now configured.")

    # Verify collection info
    info = client.get_collection(COLLECTION_NAME)
    print(f"\nCollection status: {info.status}")
    print(f"Points count: {info.points_count}")
    if hasattr(info, 'payload_schema') and info.payload_schema:
        print(f"Indexed fields: {list(info.payload_schema.keys())}")


if __name__ == "__main__":
    setup_payload_indexes()
