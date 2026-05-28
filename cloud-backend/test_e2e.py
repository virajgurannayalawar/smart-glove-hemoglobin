"""
End-to-End Test Suite for Smart Glove Hemoglobin Backend

This script tests the complete workflow:
1. Auth: register/login/profile
2. Patient CRUD
3. Scan workflow (session creation, long-poll, glove upload)
4. Report generation

Run with: python test_e2e.py
"""

import asyncio
import httpx
import json
import uuid
import time
from datetime import datetime, timezone
from typing import Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
BASE_URL = "http://localhost:8000"
API_V1 = "/api/v1"

# Test data
TEST_USER = {
    "email": f"e2e_test_{int(time.time())}@example.com",
    "password": "TestPassword123!",
    "name": "E2E Test User",
    "age": 30,
    "gender": "male",
    "contact_number": "+1234567890"
}

TEST_PATIENT = {
    "name": "Test Patient",
    "age": 25,
    "gender": "female",
    "contact_number": "+9876543210",
    "email": f"patient_{int(time.time())}@example.com",
    "notes": "E2E test patient"
}


class E2ETestRunner:
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.client = httpx.AsyncClient(timeout=60.0)
        self.token: Optional[str] = None
        self.user_data: Optional[Dict[str, Any]] = None
        self.patient_id: Optional[str] = None
        self.scan_id: Optional[str] = None
        self.reading_id: Optional[str] = None
        self.report_id: Optional[str] = None
        self.glove_api_key: Optional[str] = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    def _log(self, message: str, level: str = "info"):
        if level == "info":
            logger.info(message)
        elif level == "error":
            logger.error(message)
        elif level == "success":
            logger.info(f"✓ {message}")
        elif level == "warning":
            logger.warning(message)

    async def _request(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
        """Helper method to make HTTP requests"""
        url = f"{self.base_url}{endpoint}"
        headers = kwargs.pop("headers", {})
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        
        try:
            response = await self.client.request(method, url, headers=headers, **kwargs)
            return response
        except Exception as e:
            self._log(f"Request failed: {e}", "error")
            raise

    # ==================== AUTH TESTS ====================
    async def test_register(self) -> bool:
        """Test user registration"""
        self._log("Testing user registration...")
        
        try:
            response = await self._request(
                "POST",
                f"{API_V1}/auth/register",
                json=TEST_USER
            )
            
            if response.status_code == 200:
                data = response.json()
                self.user_data = data
                self._log(f"User registered successfully: {data['email']}", "success")
                return True
            else:
                self._log(f"Registration failed: {response.status_code} - {response.text}", "error")
                return False
        except Exception as e:
            self._log(f"Registration error: {e}", "error")
            return False

    async def test_login(self) -> bool:
        """Test user login"""
        self._log("Testing user login...")
        
        try:
            response = await self._request(
                "POST",
                f"{API_V1}/auth/login",
                json={
                    "email": TEST_USER["email"],
                    "password": TEST_USER["password"]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.token = data["token"]
                self.user_data = data["user"]
                self._log("Login successful", "success")
                return True
            else:
                self._log(f"Login failed: {response.status_code} - {response.text}", "error")
                return False
        except Exception as e:
            self._log(f"Login error: {e}", "error")
            return False

    async def test_get_profile(self) -> bool:
        """Test getting user profile"""
        self._log("Testing profile retrieval...")
        
        try:
            response = await self._request("GET", f"{API_V1}/profile")
            
            if response.status_code == 200:
                data = response.json()
                self._log(f"Profile retrieved: {data['email']}", "success")
                return True
            else:
                self._log(f"Profile retrieval failed: {response.status_code} - {response.text}", "error")
                return False
        except Exception as e:
            self._log(f"Profile retrieval error: {e}", "error")
            return False

    async def test_get_owner_id(self) -> bool:
        """Test getting owner ID for glove provisioning"""
        self._log("Testing owner ID retrieval...")
        
        try:
            response = await self._request("GET", f"{API_V1}/scan/owner-id")
            
            if response.status_code == 200:
                data = response.json()
                self._log(f"Owner ID retrieved: {data['owner_id']}", "success")
                return True
            else:
                self._log(f"Owner ID retrieval failed: {response.status_code} - {response.text}", "error")
                return False
        except Exception as e:
            self._log(f"Owner ID retrieval error: {e}", "error")
            return False

    async def test_get_glove_key(self) -> bool:
        """Test getting glove API key"""
        self._log("Testing glove API key retrieval...")
        
        try:
            response = await self._request("GET", f"{API_V1}/scan/glove-key")
            
            if response.status_code == 200:
                data = response.json()
                self.glove_api_key = data["glove_api_key"]
                self._log(f"Glove API key retrieved: {self.glove_api_key[:10]}...", "success")
                return True
            else:
                self._log(f"Glove key retrieval failed: {response.status_code} - {response.text}", "error")
                return False
        except Exception as e:
            self._log(f"Glove key retrieval error: {e}", "error")
            return False

    # ==================== PATIENT TESTS ====================
    async def test_create_patient(self) -> bool:
        """Test patient creation"""
        self._log("Testing patient creation...")
        
        try:
            response = await self._request(
                "POST",
                f"{API_V1}/patients",
                json=TEST_PATIENT
            )
            
            if response.status_code == 200:
                data = response.json()
                self.patient_id = data["patient_id"]
                self._log(f"Patient created: {data['name']} (ID: {self.patient_id})", "success")
                return True
            else:
                self._log(f"Patient creation failed: {response.status_code} - {response.text}", "error")
                return False
        except Exception as e:
            self._log(f"Patient creation error: {e}", "error")
            return False

    async def test_list_patients(self) -> bool:
        """Test listing patients"""
        self._log("Testing patient listing...")
        
        try:
            response = await self._request("GET", f"{API_V1}/patients")
            
            if response.status_code == 200:
                data = response.json()
                self._log(f"Patients listed: {len(data)} patient(s)", "success")
                return True
            else:
                self._log(f"Patient listing failed: {response.status_code} - {response.text}", "error")
                return False
        except Exception as e:
            self._log(f"Patient listing error: {e}", "error")
            return False

    async def test_get_patient(self) -> bool:
        """Test getting a specific patient"""
        self._log("Testing patient retrieval...")
        
        if not self.patient_id:
            self._log("No patient ID available", "warning")
            return False
        
        try:
            response = await self._request("GET", f"{API_V1}/patients/{self.patient_id}")
            
            if response.status_code == 200:
                data = response.json()
                self._log(f"Patient retrieved: {data['name']}", "success")
                return True
            else:
                self._log(f"Patient retrieval failed: {response.status_code} - {response.text}", "error")
                return False
        except Exception as e:
            self._log(f"Patient retrieval error: {e}", "error")
            return False

    # ==================== SCAN WORKFLOW TESTS ====================
    async def test_create_scan_session(self) -> bool:
        """Test creating a scan session"""
        self._log("Testing scan session creation...")
        
        if not self.patient_id:
            self._log("No patient ID available", "warning")
            return False
        
        try:
            response = await self._request(
                "POST",
                f"{API_V1}/scan/sessions",
                json={
                    "patient_id": self.patient_id,
                    "is_pregnant": False
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.scan_id = data["scan_id"]
                self._log(f"Scan session created: {self.scan_id}", "success")
                return True
            else:
                self._log(f"Scan session creation failed: {response.status_code} - {response.text}", "error")
                return False
        except Exception as e:
            self._log(f"Scan session creation error: {e}", "error")
            return False

    async def test_glove_upload(self) -> bool:
        """Test glove image upload (simulated)"""
        self._log("Testing glove upload...")
        
        if not self.scan_id or not self.glove_api_key:
            self._log("Missing scan_id or glove_api_key", "warning")
            return False
        
        try:
            # Create a minimal test image (1x1 PNG)
            test_image_bytes = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0bIDAT\x08\xd7c\x60\x00\x02\x00\x00\x05\x00\x01\xe2+\xfe\x0b\x00\x00\x00\x00IEND\xaeB`\x82'
            
            # For this test, we'll skip encryption and send raw bytes
            # In production, the edge device would encrypt the image
            
            metadata = {
                "owner_id": self.user_data["owner_id"],
                "patient_id": self.patient_id,
                "capture_timestamp": int(time.time()),
                "sync_timestamp": int(time.time()),
                "is_pregnant": False
            }
            
            files = {
                "image": ("test.png", test_image_bytes, "image/png")
            }
            data = {
                "metadata": json.dumps(metadata)
            }
            headers = {
                "X-Glove-Key": self.glove_api_key
            }
            
            response = await self._request(
                "POST",
                f"{API_V1}/scan/sessions/{self.scan_id}/upload",
                files=files,
                data=data,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                self.reading_id = data.get("reading_id")
                self._log(f"Glove upload successful: {self.reading_id}", "success")
                return True
            else:
                self._log(f"Glove upload failed: {response.status_code} - {response.text}", "error")
                return False
        except Exception as e:
            self._log(f"Glove upload error: {e}", "error")
            return False

    async def test_get_scan_result(self) -> bool:
        """Test getting scan result via long-poll"""
        self._log("Testing scan result retrieval (long-poll)...")
        
        if not self.scan_id:
            self._log("No scan ID available", "warning")
            return False
        
        try:
            response = await self._request(
                "GET",
                f"{API_V1}/scan/sessions/{self.scan_id}/result",
                params={"timeout_seconds": 10}
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "completed":
                    self._log(f"Scan result retrieved: Hb={data.get('hemoglobin_level')}, Anemic={data.get('is_anemic')}", "success")
                    return True
                else:
                    self._log(f"Scan status: {data.get('status')}", "warning")
                    return False
            else:
                self._log(f"Scan result retrieval failed: {response.status_code} - {response.text}", "error")
                return False
        except Exception as e:
            self._log(f"Scan result retrieval error: {e}", "error")
            return False

    # ==================== REPORT TESTS ====================
    async def test_create_report(self) -> bool:
        """Test report creation"""
        self._log("Testing report creation...")
        
        if not self.reading_id:
            self._log("No reading ID available", "warning")
            return False
        
        try:
            response = await self._request(
                "POST",
                f"{API_V1}/reports",
                json={
                    "reading_id": self.reading_id,
                    "is_pregnant": False
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                self.report_id = data["report_id"]
                self._log(f"Report created: {self.report_id}", "success")
                return True
            else:
                self._log(f"Report creation failed: {response.status_code} - {response.text}", "error")
                return False
        except Exception as e:
            self._log(f"Report creation error: {e}", "error")
            return False

    async def test_get_report(self) -> bool:
        """Test getting a specific report"""
        self._log("Testing report retrieval...")
        
        if not self.report_id:
            self._log("No report ID available", "warning")
            return False
        
        try:
            response = await self._request("GET", f"{API_V1}/reports/{self.report_id}")
            
            if response.status_code == 200:
                data = response.json()
                self._log(f"Report retrieved: PDF URL available", "success")
                return True
            else:
                self._log(f"Report retrieval failed: {response.status_code} - {response.text}", "error")
                return False
        except Exception as e:
            self._log(f"Report retrieval error: {e}", "error")
            return False

    async def test_list_reports(self) -> bool:
        """Test listing reports"""
        self._log("Testing report listing...")
        
        try:
            response = await self._request("GET", f"{API_V1}/reports")
            
            if response.status_code == 200:
                data = response.json()
                self._log(f"Reports listed: {len(data)} report(s)", "success")
                return True
            else:
                self._log(f"Report listing failed: {response.status_code} - {response.text}", "error")
                return False
        except Exception as e:
            self._log(f"Report listing error: {e}", "error")
            return False

    # ==================== HISTORY TESTS ====================
    async def test_get_history(self) -> bool:
        """Test getting scan history"""
        self._log("Testing history retrieval...")
        
        try:
            response = await self._request("GET", f"{API_V1}/history")
            
            if response.status_code == 200:
                data = response.json()
                self._log(f"History retrieved: {len(data)} reading(s)", "success")
                return True
            else:
                self._log(f"History retrieval failed: {response.status_code} - {response.text}", "error")
                return False
        except Exception as e:
            self._log(f"History retrieval error: {e}", "error")
            return False

    # ==================== CLEANUP ====================
    async def test_cleanup(self) -> bool:
        """Test cleanup - delete patient and related data"""
        self._log("Testing cleanup...")
        
        if not self.patient_id:
            self._log("No patient ID available for cleanup", "warning")
            return True
        
        try:
            response = await self._request("DELETE", f"{API_V1}/patients/{self.patient_id}")
            
            if response.status_code == 200:
                self._log("Patient deleted successfully", "success")
                return True
            else:
                self._log(f"Patient deletion failed: {response.status_code} - {response.text}", "error")
                return False
        except Exception as e:
            self._log(f"Patient deletion error: {e}", "error")
            return False

    # ==================== MAIN TEST RUNNER ====================
    async def run_all_tests(self) -> Dict[str, bool]:
        """Run all end-to-end tests"""
        self._log("=" * 60)
        self._log("STARTING END-TO-END TEST SUITE")
        self._log("=" * 60)
        
        results = {}
        
        # Auth tests
        self._log("\n--- AUTH TESTS ---")
        results["register"] = await self.test_register()
        results["login"] = await self.test_login()
        results["profile"] = await self.test_get_profile()
        results["owner_id"] = await self.test_get_owner_id()
        results["glove_key"] = await self.test_get_glove_key()
        
        # Patient tests
        self._log("\n--- PATIENT TESTS ---")
        results["create_patient"] = await self.test_create_patient()
        results["list_patients"] = await self.test_list_patients()
        results["get_patient"] = await self.test_get_patient()
        
        # Scan workflow tests
        self._log("\n--- SCAN WORKFLOW TESTS ---")
        results["create_scan_session"] = await self.test_create_scan_session()
        results["glove_upload"] = await self.test_glove_upload()
        results["get_scan_result"] = await self.test_get_scan_result()
        
        # Report tests
        self._log("\n--- REPORT TESTS ---")
        results["create_report"] = await self.test_create_report()
        results["get_report"] = await self.test_get_report()
        results["list_reports"] = await self.test_list_reports()
        
        # History test
        self._log("\n--- HISTORY TEST ---")
        results["get_history"] = await self.test_get_history()
        
        # Cleanup
        self._log("\n--- CLEANUP ---")
        results["cleanup"] = await self.test_cleanup()
        
        # Summary
        self._log("\n" + "=" * 60)
        self._log("TEST SUMMARY")
        self._log("=" * 60)
        
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        for test_name, result in results.items():
            status = "✓ PASS" if result else "✗ FAIL"
            self._log(f"{status}: {test_name}")
        
        self._log(f"\nTotal: {passed}/{total} tests passed")
        self._log("=" * 60)
        
        return results


async def main():
    """Main entry point"""
    async with E2ETestRunner() as runner:
        results = await runner.run_all_tests()
        
        # Exit with appropriate code
        passed = sum(1 for v in results.values() if v)
        total = len(results)
        
        if passed == total:
            logger.info("All tests passed!")
            return 0
        else:
            logger.error(f"Some tests failed: {passed}/{total} passed")
            return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
