"""
Simple test script to verify AutoVid project setup
"""

import httpx
import asyncio
import json

BASE_URL = "http://localhost:8000"


async def test_all():
    """Test all endpoints"""
    async with httpx.AsyncClient(timeout=30.0) as client:

        # Test health
        print("Testing /health...")
        response = await client.get(f"{BASE_URL}/health")
        print(f"  Status: {response.status_code}")
        print(f"  Response: {response.text}")
        assert response.status_code == 200

        # Test model config
        print("\nTesting /api/v1/model-config...")
        response = await client.get(f"{BASE_URL}/api/v1/model-config")
        print(f"  Status: {response.status_code}")
        assert response.status_code == 200

        # Test prompt templates
        print("\nTesting /api/v1/prompt-templates...")
        response = await client.get(f"{BASE_URL}/api/v1/prompt-templates")
        print(f"  Status: {response.status_code}")
        assert response.status_code == 200

        # Test create project
        print("\nTesting POST /api/v1/projects...")
        response = await client.post(
            f"{BASE_URL}/api/v1/projects",
            json={
                "name": "Test Project",
                "type": "drama",
                "description": "Test description"
            }
        )
        print(f"  Status: {response.status_code}")
        assert response.status_code == 200
        data = response.json()
        print(f"  Created project ID: {data.get('id')}")

        print("\n" + "=" * 50)
        print("All tests passed! ✅")
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(test_all())
