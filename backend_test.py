
import requests
import json
import sys
import os
from datetime import datetime

class DiscordServerCreatorTester:
    def __init__(self, base_url):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.template_id = None
        
    def run_test(self, name, method, endpoint, expected_status, data=None, files=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {}
        
        if files is None:
            headers['Content-Type'] = 'application/json'
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers)
            elif method == 'POST':
                if files:
                    response = requests.post(url, files=files)
                else:
                    response = requests.post(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)
                
            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"Response: {response.json()}")
                except:
                    print(f"Response: {response.text}")
                return False, {}
                
        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}
    
    def test_bot_status(self):
        """Test Discord Bot API status endpoint"""
        print("\n📋 Testing Bot Status API")
        success, response = self.run_test(
            "Bot Status",
            "GET",
            "api",
            200
        )
        
        if success:
            print(f"Bot Ready: {response.get('bot_ready')}")
            print(f"Bot User: {response.get('bot_user')}")
            
            if not response.get('bot_ready'):
                print("⚠️ Warning: Bot is not ready, some tests may fail")
                
        return success
    
    def test_template_upload(self):
        """Test template upload endpoint"""
        print("\n📋 Testing Template Upload API")
        
        # Read the example template file
        try:
            with open('/app/example_template.json', 'rb') as f:
                template_file = f.read()
                
            files = {'file': ('example_template.json', template_file, 'application/json')}
            
            success, response = self.run_test(
                "Template Upload",
                "POST",
                "api/templates/upload",
                200,
                files=files
            )
            
            if success and response.get('success'):
                self.template_id = response.get('template_id')
                print(f"Template ID: {self.template_id}")
                print(f"Template Name: {response.get('template_name')}")
            
            return success and response.get('success')
            
        except Exception as e:
            print(f"❌ Failed to read template file: {str(e)}")
            return False
    
    def test_get_templates(self):
        """Test template retrieval endpoint"""
        print("\n📋 Testing Get Templates API")
        
        success, response = self.run_test(
            "Get Templates",
            "GET",
            "api/templates",
            200
        )
        
        if success:
            templates_count = len(response)
            print(f"Retrieved {templates_count} templates")
            
            if templates_count > 0:
                print(f"First template name: {response[0].get('name')}")
                
                # If we don't have a template ID yet, use the first one
                if not self.template_id and templates_count > 0:
                    self.template_id = response[0].get('id')
                    print(f"Using template ID: {self.template_id}")
        
        return success
    
    def test_create_server(self):
        """Test server creation endpoint"""
        print("\n📋 Testing Server Creation API")
        
        if not self.template_id:
            print("❌ No template ID available, skipping server creation test")
            return False
            
        server_name = f"Test Server {datetime.now().strftime('%H%M%S')}"
        
        success, response = self.run_test(
            "Create Server",
            "POST",
            "api/servers/create",
            200,
            data={
                "template_id": self.template_id,
                "server_name": server_name
            }
        )
        
        if success:
            print(f"Success: {response.get('success')}")
            print(f"Message: {response.get('message')}")
            
            if response.get('success'):
                print(f"Server ID: {response.get('server_id')}")
                print(f"Invite Link: {response.get('invite_link')}")
                
        return success and response.get('success')
    
    def test_get_created_servers(self):
        """Test created servers list endpoint"""
        print("\n📋 Testing Get Created Servers API")
        
        success, response = self.run_test(
            "Get Created Servers",
            "GET",
            "api/servers/created",
            200
        )
        
        if success:
            servers_count = len(response)
            print(f"Retrieved {servers_count} created servers")
            
            if servers_count > 0:
                print(f"First server name: {response[0].get('server_name')}")
                print(f"First server ID: {response[0].get('server_id')}")
                
        return success
        
    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting Discord Server Creator API Tests")
        print(f"Base URL: {self.base_url}")
        
        # Test 1: Bot Status
        self.test_bot_status()
        
        # Test 2: Template Upload
        self.test_template_upload()
        
        # Test 3: Get Templates
        self.test_get_templates()
        
        # Test 4: Create Server
        self.test_create_server()
        
        # Test 5: Get Created Servers
        self.test_get_created_servers()
        
        # Print results
        print(f"\n📊 Tests passed: {self.tests_passed}/{self.tests_run}")
        return self.tests_passed == self.tests_run

def main():
    # Get the backend URL from the frontend .env file
    backend_url = "https://69dc2d4a-7a3e-4bd3-8c56-8fb6e86a8eae.preview.emergentagent.com"
    
    # Run the tests
    tester = DiscordServerCreatorTester(backend_url)
    success = tester.run_all_tests()
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
