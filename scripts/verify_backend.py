import httpx
import asyncio
import json

BASE_URL = "http://localhost:8000"

async def verify():
    async with httpx.AsyncClient() as client:
        # 1. Check health
        try:
            resp = await client.get(f"{BASE_URL}/health")
            print(f"Health check: {resp.status_code} - {resp.json()}")
        except Exception as e:
            print(f"Server not running? {e}")
            return

        # 2. Test Auth - Register
        user_data = {"email": "test@example.com", "password": "password123"}
        try:
            resp = await client.post(f"{BASE_URL}/auth/register", json=user_data)
            print(f"Register: {resp.status_code} - {resp.json()}")
        except Exception as e:
            print(f"Register failed: {e}")

        # 3. Test Auth - Login
        login_data = {"username": "test@example.com", "password": "password123"}
        token = None
        try:
            resp = await client.post(f"{BASE_URL}/auth/login", data=login_data)
            print(f"Login: {resp.status_code}")
            if resp.status_code == 200:
                token = resp.json()["access_token"]
        except Exception as e:
            print(f"Login failed: {e}")

        # 4. Test Predict - Anonymous
        patient_data = {
            "age": 45, "gender": "Male", "weight_kg": 75.0, "height_cm": 170,
            "disease_type": "Diabetes", "severity": "Moderate", "activity_level": "Moderate",
            "daily_caloric": 2200, "cholesterol": 210.0, "blood_pressure": 135, "glucose": 150.0
        }
        try:
            headers = {}
            if token:
                headers["Authorization"] = f"Bearer {token}"
            
            # First call
            resp = await client.post(f"{BASE_URL}/predict", json=patient_data, headers=headers)
            print(f"Predict (1/2): {resp.status_code}")
            
            # Second call (should be cached)
            resp2 = await client.post(f"{BASE_URL}/predict", json=patient_data, headers=headers)
            print(f"Predict (2/2): {resp2.status_code}")
        except Exception as e:
            print(f"Prediction failed: {e}")

if __name__ == "__main__":
    asyncio.run(verify())
