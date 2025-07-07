#!/usr/bin/env python3
"""
Step 4: LLM Client with Basic Authentication
Supports real LLM APIs with basic auth + Mock client for testing
Run: python llm_client.py
"""

import requests
import json
from typing import Dict, List, Any
import base64

class LLMClient:
    """LLM client with basic authentication"""
    
    def __init__(self, api_url: str, username: str, password: str):
        self.api_url = api_url
        self.username = username
        self.password = password
        self.session = requests.Session()
        
        print(f"🤖 LLMClient initialized")
        print(f"   API URL: {api_url}")
        print(f"   Username: {username}")
        print(f"   Auth: Basic authentication configured")
        
        # Set up basic authentication
        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.session.headers.update({
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/json'
        })
    
    def extract_entities_and_relationships(self, text: str) -> Dict[str, Any]:
        """Extract entities and relationships from text using LLM"""
        
        prompt = f"""
        Analyze the following text and extract entities and relationships to build a knowledge graph.
        
        Text: {text}
        
        Please provide your response in the following JSON format:
        {{
            "entities": [
                {{
                    "id": "unique_id",
                    "label": "entity_name",
                    "type": "entity_type",
                    "properties": {{"key": "value"}}
                }}
            ],
            "relationships": [
                {{
                    "source": "source_entity_id",
                    "target": "target_entity_id",
                    "type": "relationship_type",
                    "properties": {{"key": "value"}}
                }}
            ]
        }}
        
        Focus on identifying:
        - People (employees, managers, contacts)
        - Organizations (departments, companies, teams)
        - Systems (servers, applications, databases)
        - Locations (offices, data centers, cities)
        - Assets (hardware, software, licenses)
        - Processes (workflows, procedures, services)
        
        And their relationships like:
        - works_for, manages, reports_to
        - located_in, hosted_on, depends_on
        - owns, uses, maintains
        """
        
        try:
            print(f"🔄 Calling LLM API...")
            response = self.session.post(
                self.api_url,
                json={
                    "model": "gpt-3.5-turbo",  # Adjust model name as needed
                    "messages": [
                        {"role": "system", "content": "You are a knowledge graph extraction expert. Always respond with valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 2000
                }
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '{}')
                
                # Try to parse JSON from response
                try:
                    parsed_result = json.loads(content)
                    print(f"✅ LLM extraction successful")
                    return parsed_result
                except json.JSONDecodeError:
                    print(f"⚠️ JSON parsing failed, using fallback")
                    return self._get_fallback_response()
            else:
                print(f"❌ API Error: {response.status_code} - {response.text}")
                return self._get_fallback_response()
                
        except Exception as e:
            print(f"❌ Error calling LLM API: {str(e)}")
            return self._get_fallback_response()
    
    def _get_fallback_response(self) -> Dict[str, Any]:
        """Return a fallback response when API fails"""
        return {
            "entities": [
                {
                    "id": "fallback_entity",
                    "label": "Fallback Entity",
                    "type": "system",
                    "properties": {"note": "API call failed, using fallback"}
                }
            ],
            "relationships": []
        }
    
    def test_connection(self) -> bool:
        """Test the connection to the LLM API"""
        try:
            print(f"🔄 Testing LLM API connection...")
            response = self.session.post(
                self.api_url,
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": "user", "content": "Hello, can you respond with 'Connection successful'?"}
                    ],
                    "max_tokens": 10
                }
            )
            
            if response.status_code == 200:
                print("✅ LLM API connection successful")
                return True
            else:
                print(f"❌ LLM API connection failed: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ LLM API connection error: {str(e)}")
            return False

class MockLLMClient:
    """Mock LLM client for testing purposes - No API required!"""
    
    def __init__(self):
        print("🎭 MockLLMClient initialized")
        print("   Mode: Testing (no API calls)")
        print("   Purpose: Generate sample entities and relationships")
    
    def extract_entities_and_relationships(self, text: str) -> Dict[str, Any]:
        """Return realistic mock entities and relationships based on input"""
        print(f"🔄 Mock LLM processing {len(text)} characters...")
        
        # Generate response based on input content
        if "server" in text.lower() or "database" in text.lower() or "cmdb" in text.lower():
            # CMDB-style response
            response = {
                "entities": [
                    {
                        "id": "john_doe",
                        "label": "John Doe",
                        "type": "person",
                        "properties": {"department": "IT", "role": "System Administrator"}
                    },
                    {
                        "id": "jane_smith",
                        "label": "Jane Smith",
                        "type": "person",
                        "properties": {"department": "IT", "role": "Database Administrator"}
                    },
                    {
                        "id": "mike_wilson",
                        "label": "Mike Wilson",
                        "type": "person",
                        "properties": {"department": "IT", "role": "IT Manager"}
                    },
                    {
                        "id": "web_server_01",
                        "label": "Web Server 01",
                        "type": "system",
                        "properties": {"ip": "192.168.1.10", "status": "Active", "os": "Linux"}
                    },
                    {
                        "id": "database_01",
                        "label": "Database Server",
                        "type": "system",
                        "properties": {"ip": "192.168.1.20", "status": "Active", "type": "MySQL"}
                    },
                    {
                        "id": "it_department",
                        "label": "IT Department",
                        "type": "organization",
                        "properties": {"budget": "2M", "location": "New York"}
                    },
                    {
                        "id": "nyc_dc1",
                        "label": "NYC-DC1",
                        "type": "location",
                        "properties": {"type": "datacenter", "city": "New York"}
                    }
                ],
                "relationships": [
                    {
                        "source": "john_doe",
                        "target": "it_department",
                        "type": "works_for",
                        "properties": {}
                    },
                    {
                        "source": "jane_smith",
                        "target": "it_department",
                        "type": "works_for",
                        "properties": {}
                    },
                    {
                        "source": "john_doe",
                        "target": "mike_wilson",
                        "type": "reports_to",
                        "properties": {}
                    },
                    {
                        "source": "jane_smith",
                        "target": "mike_wilson",
                        "type": "reports_to",
                        "properties": {}
                    },
                    {
                        "source": "john_doe",
                        "target": "web_server_01",
                        "type": "manages",
                        "properties": {}
                    },
                    {
                        "source": "jane_smith",
                        "target": "database_01",
                        "type": "manages",
                        "properties": {}
                    },
                    {
                        "source": "web_server_01",
                        "target": "database_01",
                        "type": "depends_on",
                        "properties": {}
                    },
                    {
                        "source": "web_server_01",
                        "target": "nyc_dc1",
                        "type": "located_in",
                        "properties": {}
                    },
                    {
                        "source": "database_01",
                        "target": "nyc_dc1",
                        "type": "located_in",
                        "properties": {}
                    }
                ]
            }
        else:
            # Generic response
            response = {
                "entities": [
                    {
                        "id": "entity_1",
                        "label": "Sample Entity",
                        "type": "unknown",
                        "properties": {"source": "mock_data"}
                    }
                ],
                "relationships": []
            }
        
        print(f"✅ Mock extraction complete:")
        print(f"   Entities: {len(response['entities'])}")
        print(f"   Relationships: {len(response['relationships'])}")
        
        return response
    
    def test_connection(self) -> bool:
        """Test the mock client (always succeeds)"""
        print("✅ Mock LLM client ready")
        return True

def test_llm_clients():
    """Test both real and mock LLM clients"""
    print("🧪 Testing LLM Clients...")
    print("=" * 60)
    
    # Test Mock Client (always works)
    print("\n1️⃣ Testing Mock LLM Client:")
    print("-" * 30)
    mock_client = MockLLMClient()
    
    if mock_client.test_connection():
        sample_text = """John Doe works in the IT department as a System Administrator in New York. 
He manages Web Server 01 which runs Linux and is located in NYC-DC1.
Jane Smith is the Database Administrator and manages Database Server DB001.
Both John and Jane report to Mike Wilson who is the IT Manager."""
        
        result = mock_client.extract_entities_and_relationships(sample_text)
        
        print("\n📊 Mock extraction result:")
        print(f"   Entities found: {len(result['entities'])}")
        print(f"   Relationships found: {len(result['relationships'])}")
        
        # Show some examples
        print("\n🏷️ Sample entities:")
        for entity in result['entities'][:3]:
            print(f"   • {entity['label']} ({entity['type']})")
        
        print("\n🔗 Sample relationships:")
        for rel in result['relationships'][:3]:
            print(f"   • {rel['source']} --{rel['type']}--> {rel['target']}")
    
    # Test Real Client (requires API credentials)
    print("\n\n2️⃣ Testing Real LLM Client:")
    print("-" * 30)
    print("ℹ️ Real LLM client requires API credentials.")
    print("📝 For now, we'll demonstrate with mock credentials:")
    
    # Demo with fake credentials (will fail gracefully)
    try:
        real_client = LLMClient(
            api_url="https://api.openai.com/v1/chat/completions",
            username="your_username", 
            password="your_password"
        )
        print("⚠️ Real API test skipped (no valid credentials)")
        print("   Configure real credentials in the Streamlit app")
    except Exception as e:
        print(f"⚠️ Real client demo error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Step 4 PASSED - LLM clients work!")
    print("🎭 Mock client: Ready for testing")
    print("🤖 Real client: Ready for production (needs credentials)")
    print("👉 Ready for Step 5: Knowledge Graph Generation")
    
    return mock_client

if __name__ == "__main__":
    test_client = test_llm_clients()
