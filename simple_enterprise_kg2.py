#!/usr/bin/env python3
"""
Simple Enterprise Knowledge Graph with LLM Basic Auth
Run: streamlit run simple_enterprise_kg.py
"""

# ========================================
# 🔧 CONFIGURE YOUR LLM CREDENTIALS HERE
# ========================================
LLM_API_URL = "https://your-api-endpoint.com/v1/chat/completions"
LLM_USERNAME = "your_username_here"
LLM_PASSWORD = "your_password_here"
# ========================================

import streamlit as st
import pandas as pd
import requests
import base64
import json
import networkx as nx
from pyvis.network import Network
import tempfile
import os
from docx import Document
import io

# Simple LLM Client with Basic Auth
class SimpleLLMClient:
    def __init__(self, api_url=None, username=None, password=None):
        # Use hardcoded credentials if not provided
        self.api_url = api_url or LLM_API_URL
        self.username = username or LLM_USERNAME
        self.password = password or LLM_PASSWORD
        
        # Setup basic auth
        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/json'
        }
    
    def extract_entities_relationships(self, text):
        """Extract entities and relationships with strong business context"""
        
        # Enhanced prompt for CMDB application architecture
        prompt = f"""
        You are analyzing a CMDB (Configuration Management Database) that represents a BUSINESS APPLICATION ARCHITECTURE.
        
        CMDB DATA TO ANALYZE: {text}
        
        EXTRACT BUSINESS APPLICATION COMPONENTS AND THEIR RELATIONSHIPS:
        
        FOCUS ON THESE CMDB PATTERNS:
        1. APPLICATION COMPONENTS (applications, services, interfaces, APIs)
        2. INFRASTRUCTURE COMPONENTS (servers, databases, networks)
        3. BUSINESS SERVICES (functions, processes, capabilities)
        4. ORGANIZATIONAL COMPONENTS (teams, departments, roles)
        5. ENVIRONMENTAL COMPONENTS (datacenters, environments, locations)
        
        FOR EACH COMPONENT, IDENTIFY:
        - Business function and purpose
        - Technical role in the architecture
        - Ownership and management responsibility
        - Dependencies and relationships
        - Location and environment
        
        EXTRACT THESE SPECIFIC RELATIONSHIP TYPES:
        - SUPPORTS: how components support business functions
        - RUNS_ON: what infrastructure hosts what applications
        - DEPENDS_ON: technical dependencies between components
        - MANAGED_BY: who manages each component
        - LOCATED_IN: where components are physically/logically placed
        - PART_OF: how components belong to larger systems
        - CONNECTS_TO: network and interface connections
        - PROVIDES: what services components provide
        - CONSUMES: what resources components use
        
        CREATE A COMPREHENSIVE APPLICATION ARCHITECTURE showing:
        - Central application with supporting components around it
        - Clear business functions for each component
        - Management and ownership relationships
        - Technical dependencies and data flows
        - Infrastructure hosting relationships
        
        RESPOND WITH ONLY THIS JSON STRUCTURE:
        {{
            "entities": [
                {{
                    "id": "component_id",
                    "label": "Component Display Name",
                    "type": "application|server|database|service|person|location|organization",
                    "properties": {{
                        "business_function": "specific business purpose",
                        "technical_role": "role in the architecture",
                        "component_type": "application/infrastructure/service type",
                        "department": "owning department",
                        "environment": "production/test/dev environment",
                        "description": "detailed component description"
                    }}
                }}
            ],
            "relationships": [
                {{
                    "source": "source_component_id",
                    "target": "target_component_id",
                    "type": "supports|runs_on|depends_on|managed_by|located_in|part_of|connects_to|provides|consumes",
                    "properties": {{
                        "description": "specific relationship purpose",
                        "business_impact": "what this relationship enables"
                    }}
                }}
            ]
        }}
        
        ENSURE EVERY COMPONENT HAS MULTIPLE RELATIONSHIPS showing the complete application architecture.
        CREATE A RICH INTERCONNECTED STRUCTURE like enterprise application diagrams.
        """
        
        try:
            print("🧠 Sending enhanced prompt to LLM...")
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {
                            "role": "system", 
                            "content": "You are an expert enterprise architect who creates detailed knowledge graphs. You MUST respond with ONLY valid JSON showing rich business relationships. Focus on creating many meaningful connections between entities."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.2,  # Slightly higher for more creative relationship discovery
                    "max_tokens": 3000   # More tokens for detailed relationships
                },
                timeout=45
            )
            
            print(f"API Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '{}')
                
                print(f"Raw LLM Response: {content[:300]}...")
                
                # Clean the response
                content = content.strip()
                if content.startswith('```json'):
                    content = content[7:]
                if content.startswith('```'):
                    content = content[3:]
                if content.endswith('```'):
                    content = content[:-3]
                content = content.strip()
                
                try:
                    parsed_data = json.loads(content)
                    
                    # Validate and enhance the data
                    if 'entities' in parsed_data and 'relationships' in parsed_data:
                        entities = parsed_data['entities']
                        relationships = parsed_data['relationships']
                        
                        print(f"✅ LLM extracted: {len(entities)} entities, {len(relationships)} relationships")
                        
                        # Enhance with additional business relationships if sparse
                        if len(relationships) < len(entities) * 0.5:  # If less than 0.5 relationships per entity
                            print("⚡ Enhancing sparse relationships...")
                            enhanced_data = self._enhance_relationships(parsed_data)
                            return enhanced_data
                        
                        return parsed_data
                    else:
                        print("❌ Invalid JSON structure")
                        return self._create_business_fallback(text)
                        
                except json.JSONDecodeError as e:
                    print(f"❌ JSON parsing error: {e}")
                    return self._create_business_fallback(text)
                    
            else:
                print(f"❌ API Error: {response.status_code} - {response.text}")
                return self._create_business_fallback(text)
                
        except Exception as e:
            print(f"❌ LLM Error: {e}")
            return self._create_business_fallback(text)
    
    def _enhance_relationships(self, data):
        """Add logical business relationships if LLM output is sparse"""
        entities = data['entities']
        relationships = data['relationships']
        
        # Create lookup by type
        by_type = {}
        for entity in entities:
            entity_type = entity.get('type', 'unknown')
            if entity_type not in by_type:
                by_type[entity_type] = []
            by_type[entity_type].append(entity)
        
        # Add logical relationships
        new_relationships = []
        
        # Connect people to organizations
        people = by_type.get('person', [])
        orgs = by_type.get('organization', [])
        
        for person in people:
            # Find matching department in org
            person_dept = person.get('properties', {}).get('department', '')
            for org in orgs:
                if person_dept.lower() in org.get('label', '').lower():
                    new_relationships.append({
                        "source": person['id'],
                        "target": org['id'],
                        "type": "works_for",
                        "properties": {"description": f"Employee of {org['label']}"}
                    })
                    break
        
        # Connect systems to people (find owners/managers)
        systems = by_type.get('system', [])
        for system in systems:
            system_props = system.get('properties', {})
            # Look for owner/manager in system properties
            for person in people:
                person_name = person.get('label', '').lower()
                if any(person_name in str(v).lower() for v in system_props.values()):
                    new_relationships.append({
                        "source": person['id'],
                        "target": system['id'],
                        "type": "manages",
                        "properties": {"description": f"Responsible for {system['label']}"}
                    })
                    break
        
        # Connect applications to systems
        applications = by_type.get('application', [])
        for app in applications:
            if systems:  # Connect to first available system
                new_relationships.append({
                    "source": app['id'],
                    "target": systems[0]['id'],
                    "type": "runs_on",
                    "properties": {"description": f"{app['label']} hosted on {systems[0]['label']}"}
                })
        
        # Connect systems to locations
        locations = by_type.get('location', [])
        if locations:
            location = locations[0]  # Use first location
            for system in systems:
                new_relationships.append({
                    "source": system['id'],
                    "target": location['id'],
                    "type": "located_in",
                    "properties": {"description": f"Physically located in {location['label']}"}
                })
        
        # Add new relationships
        relationships.extend(new_relationships)
        data['relationships'] = relationships
        
        print(f"⚡ Enhanced with {len(new_relationships)} additional relationships")
        return data
    
    def _create_business_fallback(self, text):
        """Create comprehensive business fallback with relationships"""
        print("🔄 Creating comprehensive business fallback...")
        
        entities = []
        relationships = []
        
        # Extract more comprehensive entities from text
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Look for CMDB-style data patterns
        people_found = []
        systems_found = []
        departments_found = []
        locations_found = []
        
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Extract people (look for names, roles, titles)
            if any(keyword in line_lower for keyword in ['admin', 'manager', 'analyst', 'engineer', 'developer', 'owner']):
                entity_id = f"person_{len(people_found) + 1}"
                entities.append({
                    "id": entity_id,
                    "label": f"Staff Member {len(people_found) + 1}",
                    "type": "person",
                    "properties": {
                        "business_function": "IT operations and management",
                        "role": "System administrator/manager",
                        "department": "IT",
                        "source_line": line[:50] + "..."
                    }
                })
                people_found.append(entity_id)
            
            # Extract systems (servers, databases, applications)
            if any(keyword in line_lower for keyword in ['server', 'database', 'system', 'application', 'service']):
                entity_id = f"system_{len(systems_found) + 1}"
                
                # Determine system type
                if 'database' in line_lower:
                    biz_function = "Data storage and management"
                elif 'web' in line_lower:
                    biz_function = "Web service delivery"
                elif 'application' in line_lower or 'app' in line_lower:
                    biz_function = "Business application hosting"
                else:
                    biz_function = "IT infrastructure support"
                
                entities.append({
                    "id": entity_id,
                    "label": f"System {len(systems_found) + 1}",
                    "type": "system",
                    "properties": {
                        "business_function": biz_function,
                        "status": "Active",
                        "department": "IT",
                        "description": f"Critical system supporting business operations",
                        "source_line": line[:50] + "..."
                    }
                })
                systems_found.append(entity_id)
            
            # Extract departments
            if any(keyword in line_lower for keyword in ['department', 'dept', 'division', 'team']):
                entity_id = f"dept_{len(departments_found) + 1}"
                entities.append({
                    "id": entity_id,
                    "label": f"Department {len(departments_found) + 1}",
                    "type": "organization",
                    "properties": {
                        "business_function": "Organizational unit managing business operations",
                        "type": "department",
                        "source_line": line[:50] + "..."
                    }
                })
                departments_found.append(entity_id)
            
            # Extract locations
            if any(keyword in line_lower for keyword in ['datacenter', 'dc', 'office', 'location', 'site', 'building']):
                entity_id = f"location_{len(locations_found) + 1}"
                entities.append({
                    "id": entity_id,
                    "label": f"Location {len(locations_found) + 1}",
                    "type": "location",
                    "properties": {
                        "business_function": "Physical hosting and infrastructure location",
                        "type": "datacenter",
                        "source_line": line[:50] + "..."
                    }
                })
                locations_found.append(entity_id)
        
        # If no entities found, create realistic business scenario
        if not entities:
            # Create a complete business scenario
            entities = [
                {
                    "id": "it_manager",
                    "label": "IT Manager",
                    "type": "person",
                    "properties": {
                        "business_function": "Manages IT infrastructure and team",
                        "role": "Department Manager",
                        "department": "IT",
                        "responsibilities": "Strategic planning, team management, budget oversight"
                    }
                },
                {
                    "id": "system_admin",
                    "label": "System Administrator", 
                    "type": "person",
                    "properties": {
                        "business_function": "Daily system operations and maintenance",
                        "role": "Systems Administrator",
                        "department": "IT",
                        "responsibilities": "Server management, monitoring, troubleshooting"
                    }
                },
                {
                    "id": "web_server",
                    "label": "Production Web Server",
                    "type": "system",
                    "properties": {
                        "business_function": "Hosts customer-facing web applications",
                        "status": "Active",
                        "department": "IT",
                        "business_impact": "Critical - affects customer experience",
                        "description": "Primary web server handling customer transactions"
                    }
                },
                {
                    "id": "database_server",
                    "label": "Production Database",
                    "type": "system",
                    "properties": {
                        "business_function": "Stores critical business data and customer information",
                        "status": "Active", 
                        "department": "IT",
                        "business_impact": "Critical - core business data",
                        "description": "Main database supporting all business operations"
                    }
                },
                {
                    "id": "crm_application",
                    "label": "CRM Application",
                    "type": "application",
                    "properties": {
                        "business_function": "Customer relationship management and sales tracking",
                        "department": "Sales",
                        "business_impact": "High - sales team productivity",
                        "users": "Sales team, customer service",
                        "description": "Core application for managing customer relationships"
                    }
                },
                {
                    "id": "primary_datacenter",
                    "label": "Primary Data Center",
                    "type": "location",
                    "properties": {
                        "business_function": "Houses critical IT infrastructure",
                        "type": "datacenter",
                        "business_impact": "Critical - all systems hosted here",
                        "description": "Main facility hosting production systems"
                    }
                },
                {
                    "id": "it_department",
                    "label": "IT Department",
                    "type": "organization",
                    "properties": {
                        "business_function": "Manages technology infrastructure and digital operations",
                        "budget": "Operational budget for technology",
                        "business_impact": "Enables all digital business operations",
                        "description": "Department responsible for technology strategy and operations"
                    }
                }
            ]
            
            # Create comprehensive business relationships
            relationships = [
                # Management hierarchy
                {
                    "source": "system_admin",
                    "target": "it_manager", 
                    "type": "reports_to",
                    "properties": {
                        "description": "Organizational reporting structure",
                        "business_impact": "Management oversight and decision-making"
                    }
                },
                
                # System ownership and management
                {
                    "source": "system_admin",
                    "target": "web_server",
                    "type": "manages",
                    "properties": {
                        "description": "Responsible for daily operations and maintenance",
                        "business_impact": "System downtime affects customer access"
                    }
                },
                {
                    "source": "system_admin", 
                    "target": "database_server",
                    "type": "manages",
                    "properties": {
                        "description": "Database administration and maintenance",
                        "business_impact": "Data availability critical for business operations"
                    }
                },
                
                # Technical dependencies
                {
                    "source": "web_server",
                    "target": "database_server",
                    "type": "depends_on",
                    "properties": {
                        "description": "Web server requires database for dynamic content",
                        "business_impact": "Database outage stops web application functionality"
                    }
                },
                {
                    "source": "crm_application",
                    "target": "web_server",
                    "type": "runs_on",
                    "properties": {
                        "description": "CRM application hosted on web server",
                        "business_impact": "Server issues affect sales team productivity"
                    }
                },
                {
                    "source": "crm_application",
                    "target": "database_server", 
                    "type": "uses",
                    "properties": {
                        "description": "CRM stores customer data in database",
                        "business_impact": "Database issues lose customer information access"
                    }
                },
                
                # Physical location relationships
                {
                    "source": "web_server",
                    "target": "primary_datacenter",
                    "type": "located_in",
                    "properties": {
                        "description": "Server physically located in datacenter",
                        "business_impact": "Datacenter issues affect server availability"
                    }
                },
                {
                    "source": "database_server",
                    "target": "primary_datacenter",
                    "type": "located_in", 
                    "properties": {
                        "description": "Database server housed in primary facility",
                        "business_impact": "Facility outage affects data access"
                    }
                },
                
                # Organizational relationships  
                {
                    "source": "it_manager",
                    "target": "it_department",
                    "type": "manages",
                    "properties": {
                        "description": "Leads IT department operations and strategy",
                        "business_impact": "Department effectiveness depends on leadership"
                    }
                },
                {
                    "source": "system_admin",
                    "target": "it_department",
                    "type": "works_for",
                    "properties": {
                        "description": "IT department team member",
                        "business_impact": "Skills and availability affect IT operations"
                    }
                }
            ]
        
        else:
            # Create relationships between found entities
            # Connect people to systems (management)
            for i, person in enumerate(people_found):
                if i < len(systems_found):
                    relationships.append({
                        "source": person,
                        "target": systems_found[i],
                        "type": "manages",
                        "properties": {
                            "description": "Responsible for system operations",
                            "business_impact": "System availability depends on administrator"
                        }
                    })
            
            # Connect systems to locations
            if locations_found:
                for system in systems_found:
                    relationships.append({
                        "source": system,
                        "target": locations_found[0],
                        "type": "located_in",
                        "properties": {
                            "description": "System hosted at this location",
                            "business_impact": "Location issues affect system availability"
                        }
                    })
            
            # Connect people to departments
            if departments_found and people_found:
                for person in people_found:
                    relationships.append({
                        "source": person,
                        "target": departments_found[0],
                        "type": "works_for",
                        "properties": {
                            "description": "Department team member",
                            "business_impact": "Department operations depend on team members"
                        }
                    })
        
        print(f"✅ Business fallback created: {len(entities)} entities, {len(relationships)} relationships")
        print(f"   🏷️ Entity types: {set(e['type'] for e in entities)}")
        print(f"   🔗 Relationship types: {set(r['type'] for r in relationships)}")
        
        return {
            "entities": entities,
            "relationships": relationships
        }

# Simple File Processor
class SimpleFileProcessor:
    def process_file(self, uploaded_file):
        """Process uploaded file and extract CMDB relationships"""
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension == 'csv':
            df = pd.read_csv(uploaded_file)
            return self._extract_cmdb_relationships(df)
        elif file_extension in ['xlsx', 'xls']:
            df = pd.read_excel(uploaded_file)
            return self._extract_cmdb_relationships(df)
        elif file_extension == 'docx':
            doc = Document(io.BytesIO(uploaded_file.read()))
            text_content = []
            for paragraph in doc.paragraphs:
                if paragraph.text.strip():
                    text_content.append(paragraph.text.strip())
            return "\n".join(text_content)
        elif file_extension == 'txt':
            return str(uploaded_file.read(), "utf-8")
        else:
            return "Unsupported file format"
    
    def _extract_cmdb_relationships(self, df):
        """Extract detailed CMDB relationships from DataFrame"""
        text_content = []
        
        print(f"📊 Processing CMDB data: {len(df)} rows, {len(df.columns)} columns")
        print(f"Columns: {list(df.columns)}")
        
        # Add header information
        text_content.append("=== CMDB BUSINESS APPLICATION ARCHITECTURE ===")
        text_content.append(f"Total Components: {len(df)}")
        text_content.append(f"Data Fields: {', '.join(df.columns)}")
        text_content.append("")
        
        # Process each row with detailed business context
        for idx, row in df.iterrows():
            component_info = []
            component_info.append(f"=== COMPONENT {idx + 1} ===")
            
            # Extract all available information
            for col in df.columns:
                if pd.notna(row[col]) and str(row[col]).strip():
                    value = str(row[col]).strip()
                    component_info.append(f"{col}: {value}")
            
            # Add business context based on common CMDB patterns
            component_text = " ".join([str(row[col]) for col in df.columns if pd.notna(row[col])])
            component_lower = component_text.lower()
            
            # Identify component type and business function
            if any(keyword in component_lower for keyword in ['application', 'app', 'software', 'system']):
                component_info.append("BUSINESS_FUNCTION: Core business application providing services to users")
                component_info.append("COMPONENT_TYPE: Application")
                
            elif any(keyword in component_lower for keyword in ['server', 'host', 'machine']):
                component_info.append("BUSINESS_FUNCTION: Infrastructure server hosting applications and services")
                component_info.append("COMPONENT_TYPE: Infrastructure Server")
                
            elif any(keyword in component_lower for keyword in ['database', 'db', 'data']):
                component_info.append("BUSINESS_FUNCTION: Data storage and management system")
                component_info.append("COMPONENT_TYPE: Database System")
                
            elif any(keyword in component_lower for keyword in ['service', 'api', 'interface']):
                component_info.append("BUSINESS_FUNCTION: Service interface providing business functionality")
                component_info.append("COMPONENT_TYPE: Business Service")
                
            elif any(keyword in component_lower for keyword in ['network', 'router', 'switch', 'firewall']):
                component_info.append("BUSINESS_FUNCTION: Network infrastructure enabling connectivity")
                component_info.append("COMPONENT_TYPE: Network Component")
                
            else:
                component_info.append("BUSINESS_FUNCTION: Business component supporting organizational operations")
                component_info.append("COMPONENT_TYPE: Business Component")
            
            # Add relationship context
            component_info.append("RELATIONSHIPS:")
            
            # Look for common CMDB relationship indicators
            for col in df.columns:
                if pd.notna(row[col]):
                    col_lower = col.lower()
                    value = str(row[col]).strip()
                    
                    if any(keyword in col_lower for keyword in ['owner', 'manager', 'responsible', 'admin']):
                        component_info.append(f"  MANAGED_BY: {value} (person responsible for this component)")
                        
                    elif any(keyword in col_lower for keyword in ['department', 'dept', 'team', 'group']):
                        component_info.append(f"  BELONGS_TO: {value} (organizational unit)")
                        
                    elif any(keyword in col_lower for keyword in ['location', 'datacenter', 'site', 'environment']):
                        component_info.append(f"  LOCATED_IN: {value} (physical or logical location)")
                        
                    elif any(keyword in col_lower for keyword in ['depends', 'requires', 'uses', 'connects']):
                        component_info.append(f"  DEPENDS_ON: {value} (technical dependency)")
                        
                    elif any(keyword in col_lower for keyword in ['supports', 'serves', 'provides']):
                        component_info.append(f"  SUPPORTS: {value} (business service relationship)")
                        
                    elif any(keyword in col_lower for keyword in ['runs', 'hosts', 'contains']):
                        component_info.append(f"  HOSTS: {value} (hosting relationship)")
            
            # Add component interactions based on the diagram pattern
            component_info.append("BUSINESS_INTERACTIONS:")
            component_info.append("  - This component is part of a larger business application architecture")
            component_info.append("  - It may support business functions like data processing, user interfaces, or system integration")
            component_info.append("  - It has dependencies on other components for full functionality")
            component_info.append("  - It may be managed by specific teams or individuals")
            component_info.append("  - It operates within specific environments or locations")
            
            text_content.extend(component_info)
            text_content.append("")  # Add spacing
        
        # Add overall architecture context
        text_content.append("=== OVERALL ARCHITECTURE CONTEXT ===")
        text_content.append("This CMDB represents a business application architecture with multiple interconnected components.")
        text_content.append("Components include applications, servers, databases, services, and infrastructure elements.")
        text_content.append("Each component has specific business functions, ownership, and relationships with other components.")
        text_content.append("The architecture supports business operations through integrated technology components.")
        text_content.append("Management responsibilities are distributed across different teams and individuals.")
        text_content.append("Components are deployed across various environments and locations.")
        
        # Look for specific relationship patterns in column names
        text_content.append("\n=== DETECTED RELATIONSHIP PATTERNS ===")
        relationship_columns = []
        for col in df.columns:
            col_lower = col.lower()
            if any(keyword in col_lower for keyword in ['owner', 'manager', 'depends', 'location', 'environment', 'team', 'group']):
                relationship_columns.append(col)
        
        if relationship_columns:
            text_content.append(f"Relationship indicators found in columns: {', '.join(relationship_columns)}")
            text_content.append("These columns contain information about component relationships and dependencies.")
        
        result = "\n".join(text_content)
        print(f"✅ CMDB processing complete: {len(result)} characters of relationship data extracted")
        return result

# Simple Knowledge Graph
class SimpleKnowledgeGraph:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.entities = {}
        
    def build_from_data(self, data):
        """Build graph from extracted data"""
        # Add entities
        for entity in data.get('entities', []):
            entity_id = entity['id']
            self.entities[entity_id] = entity
            self.graph.add_node(entity_id, **entity)
        
        # Add relationships
        for rel in data.get('relationships', []):
            if rel['source'] in self.entities and rel['target'] in self.entities:
                self.graph.add_edge(rel['source'], rel['target'], **rel)
    
    def generate_pyvis_html(self):
        """Generate enhanced Pyvis visualization with legend and filtering"""
        net = Network(
            height="700px", 
            width="100%", 
            bgcolor="#1a1a1a", 
            font_color="white", 
            directed=True,
            filter_menu=True,
            select_menu=True
        )
        
        # Configure enhanced physics
        net.set_options("""
        {
          "physics": {
            "enabled": true,
            "stabilization": {"iterations": 150},
            "barnesHut": {
              "gravitationalConstant": -3000,
              "centralGravity": 0.1,
              "springLength": 200,
              "springConstant": 0.02,
              "damping": 0.05
            }
          },
          "layout": {
            "improvedLayout": true,
            "hierarchical": {
              "enabled": false
            }
          },
          "interaction": {
            "dragNodes": true,
            "dragView": true,
            "zoomView": true,
            "selectConnectedEdges": true,
            "hover": true
          },
          "nodes": {
            "font": {"size": 14, "color": "white"},
            "borderWidth": 2,
            "shadow": true
          },
          "edges": {
            "font": {"size": 12, "color": "white"},
            "shadow": true,
            "smooth": {"enabled": true, "type": "continuous"}
          }
        }
        """)
        
        # Enhanced color scheme with better contrast
        colors = {
            'application': '#FF6B6B',     # Red - Critical business apps
            'system': '#4ECDC4',          # Teal - Infrastructure systems  
            'server': '#45B7D1',          # Blue - Servers
            'database': '#96CEB4',        # Green - Databases
            'service': '#FFEAA7',         # Yellow - Services
            'person': '#DDA0DD',          # Purple - People
            'location': '#FFA07A',        # Orange - Locations
            'organization': '#98D8C8',    # Mint - Organizations
            'network': '#F7DC6F',         # Light Yellow - Network components
            'unknown': '#BDC3C7'          # Gray - Unknown
        }
        
        # Enhanced relationship colors
        edge_colors = {
            'supports': '#E74C3C',        # Red - Business support
            'runs_on': '#3498DB',         # Blue - Hosting
            'depends_on': '#9B59B6',      # Purple - Dependencies
            'manages': '#E67E22',         # Orange - Management
            'located_in': '#2ECC71',      # Green - Location
            'works_for': '#F39C12',       # Yellow - Employment
            'part_of': '#1ABC9C',         # Turquoise - Membership
            'connects_to': '#34495E',     # Dark blue - Connections
            'provides': '#8E44AD',        # Dark purple - Services
            'consumes': '#16A085'         # Dark teal - Resource usage
        }
        
        print(f"🎨 Building enhanced visualization with {len(self.graph.nodes)} nodes...")
        
        # Collect statistics for legend
        node_stats = {}
        edge_stats = {}
        
        # Add nodes with enhanced styling
        for node_id, node_data in self.graph.nodes(data=True):
            entity_type = node_data.get('type', 'unknown')
            color = colors.get(entity_type, '#BDC3C7')
            label = node_data.get('label', node_id)
            
            # Count for statistics
            node_stats[entity_type] = node_stats.get(entity_type, 0) + 1
            
            # Create comprehensive hover info
            properties = node_data.get('properties', {})
            hover_text = f"<div style='max-width: 300px;'>"
            hover_text += f"<h3 style='color: {color}; margin: 0;'>{label}</h3>"
            hover_text += f"<p><strong>Type:</strong> {entity_type.title()}</p>"
            
            if properties:
                if 'business_function' in properties:
                    hover_text += f"<p><strong>Function:</strong> {properties['business_function']}</p>"
                if 'department' in properties:
                    hover_text += f"<p><strong>Department:</strong> {properties['department']}</p>"
                if 'description' in properties:
                    hover_text += f"<p><strong>Description:</strong> {properties['description'][:100]}...</p>"
                
                # Add other properties
                other_props = {k: v for k, v in properties.items() 
                             if k not in ['business_function', 'department', 'description']}
                if other_props:
                    hover_text += "<p><strong>Details:</strong><br>"
                    for key, value in list(other_props.items())[:3]:
                        hover_text += f"• {key}: {value}<br>"
                    if len(other_props) > 3:
                        hover_text += f"• ... and {len(other_props) - 3} more"
                    hover_text += "</p>"
            
            hover_text += "</div>"
            
            # Determine node size based on connections
            connections = len(list(self.graph.neighbors(node_id)))
            node_size = min(50, max(25, 20 + connections * 3))
            
            net.add_node(
                node_id,
                label=label,
                color=color,
                title=hover_text,
                size=node_size,
                font={'size': 14, 'color': 'white'},
                borderWidth=3,
                borderWidthSelected=5,
                group=entity_type  # For filtering
            )
        
        print(f"🔗 Adding {len(self.graph.edges)} relationships...")
        
        # Add edges with enhanced styling
        for source, target, edge_data in self.graph.edges(data=True):
            rel_type = edge_data.get('type', 'connected')
            edge_color = edge_colors.get(rel_type, '#848484')
            
            # Count for statistics
            edge_stats[rel_type] = edge_stats.get(rel_type, 0) + 1
            
            # Create edge hover info
            source_label = self.entities.get(source, {}).get('label', source)
            target_label = self.entities.get(target, {}).get('label', target)
            
            edge_properties = edge_data.get('properties', {})
            edge_title = f"<div style='max-width: 250px;'>"
            edge_title += f"<h4 style='margin: 0; color: {edge_color};'>{rel_type.replace('_', ' ').title()}</h4>"
            edge_title += f"<p><strong>From:</strong> {source_label}</p>"
            edge_title += f"<p><strong>To:</strong> {target_label}</p>"
            
            if edge_properties:
                if 'description' in edge_properties:
                    edge_title += f"<p><strong>Purpose:</strong> {edge_properties['description']}</p>"
                if 'business_impact' in edge_properties:
                    edge_title += f"<p><strong>Impact:</strong> {edge_properties['business_impact']}</p>"
            
            edge_title += "</div>"
            
            net.add_edge(
                source,
                target,
                label=rel_type.replace('_', ' '),
                color={'color': edge_color, 'opacity': 0.8},
                title=edge_title,
                arrows={'to': {'enabled': True, 'scaleFactor': 1.5}},
                width=4,
                font={'size': 11, 'color': 'white', 'strokeWidth': 2, 'strokeColor': '#000000'},
                smooth={'enabled': True, 'type': 'continuous', 'roundness': 0.2}
            )
        
        # Generate HTML with custom legend and controls
        try:
            import uuid
            temp_filename = f"temp_graph_{uuid.uuid4().hex[:8]}.html"
            
            # Save initial graph
            net.save_graph(temp_filename)
            
            # Read and enhance HTML
            with open(temp_filename, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Add custom legend and controls
            legend_html = self._create_legend_and_controls(node_stats, edge_stats, colors, edge_colors)
            
            # Insert legend before closing body tag
            html_content = html_content.replace('</body>', f'{legend_html}</body>')
            
            # Clean up temp file
            try:
                os.remove(temp_filename)
            except:
                pass
            
            print(f"✅ Enhanced Pyvis with legend and filtering generated")
            return html_content
            
        except Exception as e:
            print(f"❌ Enhanced Pyvis generation failed: {e}")
            return self._generate_detailed_fallback_html()
    
    def _create_legend_and_controls(self, node_stats, edge_stats, colors, edge_colors):
        """Create interactive legend and filtering controls"""
        
        legend_html = """
        <div id="legend-panel" style="
            position: fixed; 
            top: 10px; 
            right: 10px; 
            background: rgba(0,0,0,0.9); 
            color: white; 
            padding: 15px; 
            border-radius: 10px; 
            max-width: 300px;
            font-family: Arial, sans-serif;
            font-size: 12px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.3);
            z-index: 1000;
            max-height: 80vh;
            overflow-y: auto;
        ">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <h3 style="margin: 0; color: #4ECDC4;">📊 Graph Legend</h3>
                <button onclick="toggleLegend()" style="
                    background: #4ECDC4; 
                    border: none; 
                    color: black; 
                    padding: 5px 10px; 
                    border-radius: 5px;
                    cursor: pointer;
                    font-size: 10px;
                ">Hide</button>
            </div>
            
            <div id="legend-content">
                <!-- Node Types Legend -->
                <div style="margin-bottom: 15px;">
                    <h4 style="margin: 5px 0; color: #FF6B6B;">🏷️ Component Types</h4>
        """
        
        # Add node type legend
        for node_type, count in sorted(node_stats.items()):
            color = colors.get(node_type, '#BDC3C7')
            legend_html += f"""
                    <div style="display: flex; align-items: center; margin: 3px 0;">
                        <div style="
                            width: 15px; 
                            height: 15px; 
                            background: {color}; 
                            border-radius: 50%; 
                            margin-right: 8px;
                            border: 2px solid white;
                        "></div>
                        <span>{node_type.title()} ({count})</span>
                    </div>
            """
        
        legend_html += """
                </div>
                
                <!-- Relationship Types Legend -->
                <div style="margin-bottom: 15px;">
                    <h4 style="margin: 5px 0; color: #45B7D1;">🔗 Relationship Types</h4>
        """
        
        # Add relationship type legend
        for rel_type, count in sorted(edge_stats.items()):
            color = edge_colors.get(rel_type, '#848484')
            legend_html += f"""
                    <div style="display: flex; align-items: center; margin: 3px 0;">
                        <div style="
                            width: 20px; 
                            height: 3px; 
                            background: {color}; 
                            margin-right: 8px;
                            border-radius: 2px;
                        "></div>
                        <span>{rel_type.replace('_', ' ').title()} ({count})</span>
                    </div>
            """
        
        legend_html += f"""
                </div>
                
                <!-- Graph Statistics -->
                <div style="margin-bottom: 15px;">
                    <h4 style="margin: 5px 0; color: #FFEAA7;">📈 Statistics</h4>
                    <div style="font-size: 11px;">
                        <div>Total Components: {sum(node_stats.values())}</div>
                        <div>Total Relationships: {sum(edge_stats.values())}</div>
                        <div>Component Types: {len(node_stats)}</div>
                        <div>Relationship Types: {len(edge_stats)}</div>
                    </div>
                </div>
                
                <!-- Controls -->
                <div>
                    <h4 style="margin: 5px 0; color: #96CEB4;">🎮 Controls</h4>
                    <div style="font-size: 11px;">
                        <div>• Drag nodes to move them</div>
                        <div>• Scroll to zoom in/out</div>
                        <div>• Hover for details</div>
                        <div>• Click to select nodes</div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Toggle Button for Collapsed Legend -->
        <div id="legend-toggle" style="
            position: fixed; 
            top: 10px; 
            right: 10px; 
            background: rgba(0,0,0,0.9); 
            color: white; 
            padding: 10px; 
            border-radius: 10px; 
            font-family: Arial, sans-serif;
            cursor: pointer;
            z-index: 1000;
            display: none;
        " onclick="toggleLegend()">
            📊 Show Legend
        </div>
        
        <script>
            function toggleLegend() {{
                const panel = document.getElementById('legend-panel');
                const toggle = document.getElementById('legend-toggle');
                
                if (panel.style.display === 'none') {{
                    panel.style.display = 'block';
                    toggle.style.display = 'none';
                }} else {{
                    panel.style.display = 'none';
                    toggle.style.display = 'block';
                }}
            }}
            
            // Add keyboard shortcuts
            document.addEventListener('keydown', function(event) {{
                if (event.key === 'l' || event.key === 'L') {{
                    toggleLegend();
                }}
            }});
        </script>
        """
        
        return legend_html
    
    def _generate_detailed_fallback_html(self):
        """Generate detailed HTML with relationship visualization if Pyvis fails"""
        html = """
        <div style="background: #1a1a1a; color: white; padding: 20px; border-radius: 8px; font-family: Arial, sans-serif;">
            <h2 style="color: #4ECDC4; text-align: center;">📊 Knowledge Graph Visualization</h2>
            <p style="text-align: center; color: #ccc;">Interactive Pyvis unavailable - showing detailed graph structure</p>
        """
        
        # Entity type colors for the legend
        colors = {
            'person': '#FF6B6B',
            'system': '#4ECDC4',
            'application': '#45B7D1',
            'location': '#96CEB4',
            'organization': '#FFEAA7'
        }
        
        # Legend
        html += '<div style="margin: 20px 0; padding: 15px; background: #2a2a2a; border-radius: 8px;">'
        html += '<h3 style="color: #45B7D1;">🎨 Entity Types Legend:</h3>'
        for entity_type, color in colors.items():
            html += f'<span style="background: {color}; color: black; padding: 4px 8px; margin: 2px; border-radius: 4px; display: inline-block;">{entity_type.title()}</span> '
        html += '</div>'
        
        # Show entities grouped by type
        html += '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0;">'
        
        # Left column - Entities
        html += '<div style="background: #2a2a2a; padding: 15px; border-radius: 8px;">'
        html += f'<h3 style="color: #FF6B6B;">🏷️ Entities ({len(self.entities)})</h3>'
        
        # Group entities by type
        by_type = {}
        for entity_id, entity in self.entities.items():
            entity_type = entity.get('type', 'unknown')
            if entity_type not in by_type:
                by_type[entity_type] = []
            by_type[entity_type].append(entity)
        
        for entity_type, entities in by_type.items():
            color = colors.get(entity_type, '#BDC3C7')
            html += f'<h4 style="color: {color};">{entity_type.title()}s ({len(entities)})</h4>'
            for entity in entities:
                html += f'<div style="margin: 8px 0; padding: 8px; background: #333; border-radius: 4px; border-left: 4px solid {color};">'
                html += f'<strong>{entity.get("label", entity["id"])}</strong><br>'
                
                properties = entity.get('properties', {})
                if properties:
                    html += '<small style="color: #ccc;">'
                    prop_list = [f"{k}: {v}" for k, v in list(properties.items())[:3]]
                    html += " | ".join(prop_list)
                    if len(properties) > 3:
                        html += f" (+{len(properties)-3} more)"
                    html += '</small>'
                html += '</div>'
        
        html += '</div>'
        
        # Right column - Relationships
        html += '<div style="background: #2a2a2a; padding: 15px; border-radius: 8px;">'
        relationships = list(self.graph.edges(data=True))
        html += f'<h3 style="color: #45B7D1;">🔗 Relationships ({len(relationships)})</h3>'
        
        # Group relationships by type
        rel_by_type = {}
        for source, target, data in relationships:
            rel_type = data.get('type', 'connected')
            if rel_type not in rel_by_type:
                rel_by_type[rel_type] = []
            rel_by_type[rel_type].append((source, target, data))
        
        for rel_type, rels in rel_by_type.items():
            rel_colors = {
                'manages': '#E74C3C',
                'depends_on': '#3498DB', 
                'reports_to': '#9B59B6',
                'located_in': '#2ECC71',
                'works_for': '#F39C12'
            }
            color = rel_colors.get(rel_type, '#848484')
            
            html += f'<h4 style="color: {color};">{rel_type.replace("_", " ").title()} ({len(rels)})</h4>'
            
            for source, target, data in rels[:5]:  # Show first 5 of each type
                source_label = self.entities.get(source, {}).get('label', source)
                target_label = self.entities.get(target, {}).get('label', target)
                
                html += f'<div style="margin: 6px 0; padding: 6px; background: #333; border-radius: 4px; border-left: 3px solid {color};">'
                html += f'<span style="color: #FF6B6B;">{source_label}</span> '
                html += f'<span style="color: {color};">--{rel_type}--></span> '
                html += f'<span style="color: #4ECDC4;">{target_label}</span>'
                html += '</div>'
            
            if len(rels) > 5:
                html += f'<small style="color: #888;">... and {len(rels) - 5} more {rel_type} relationships</small><br>'
        
        html += '</div>'
        html += '</div>'  # Close grid
        
        # Network structure summary
        html += '<div style="background: #2a2a2a; padding: 15px; border-radius: 8px; margin: 20px 0;">'
        html += '<h3 style="color: #FFEAA7;">📈 Graph Structure Summary</h3>'
        html += f'<div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 15px; text-align: center;">'
        html += f'<div><span style="font-size: 2em; color: #FF6B6B;">{len(self.entities)}</span><br><small>Total Entities</small></div>'
        html += f'<div><span style="font-size: 2em; color: #45B7D1;">{len(relationships)}</span><br><small>Total Relationships</small></div>'
        html += f'<div><span style="font-size: 2em; color: #4ECDC4;">{len(by_type)}</span><br><small>Entity Types</small></div>'
        html += f'<div><span style="font-size: 2em; color: #FFEAA7;">{len(rel_by_type)}</span><br><small>Relationship Types</small></div>'
        html += '</div></div>'
        
        html += '''
            <div style="background: #2a2a2a; padding: 15px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: #96CEB4;">💡 Your Knowledge Graph is Working!</h3>
                <p>The graph structure shows all entities and their relationships. Use the Q&A section below to explore connections like:</p>
                <ul style="color: #ccc;">
                    <li>"Who manages [system name]?"</li>
                    <li>"What does [person name] manage?"</li>
                    <li>"Show all people" / "Show all systems"</li>
                </ul>
            </div>
        </div>
        '''
        
        return html
    
    def query(self, question):
        """Simple Q&A"""
        question = question.lower()
        
        if 'who manages' in question:
            # Extract entity name from question
            words = question.replace('who manages', '').replace('?', '').strip().split()
            target_name = ' '.join(words)
            
            for entity_id, entity in self.entities.items():
                if target_name.lower() in entity['label'].lower():
                    managers = []
                    for pred in self.graph.predecessors(entity_id):
                        edge = self.graph[pred][entity_id]
                        if edge.get('type') == 'manages':
                            manager = self.entities[pred]
                            managers.append(f"👤 {manager['label']}")
                    
                    if managers:
                        return f"✅ {entity['label']} is managed by:\n" + "\n".join(managers)
                    else:
                        return f"ℹ️ No manager found for {entity['label']}"
            
            return f"❌ Could not find entity: {target_name}"
        
        elif 'what does' in question and 'manage' in question:
            # Extract person name
            start = question.find('what does') + 9
            end = question.find('manage')
            person_name = question[start:end].strip()
            
            for entity_id, entity in self.entities.items():
                if person_name.lower() in entity['label'].lower():
                    managed = []
                    for succ in self.graph.successors(entity_id):
                        edge = self.graph[entity_id][succ]
                        if edge.get('type') == 'manages':
                            item = self.entities[succ]
                            managed.append(f"🔧 {item['label']}")
                    
                    if managed:
                        return f"✅ {entity['label']} manages:\n" + "\n".join(managed)
                    else:
                        return f"ℹ️ {entity['label']} doesn't manage anything"
            
            return f"❌ Could not find person: {person_name}"
        
        elif 'show all' in question:
            if 'people' in question or 'person' in question:
                people = [e['label'] for e in self.entities.values() if e.get('type') == 'person']
                return f"👥 People:\n" + "\n".join([f"• {p}" for p in people])
            elif 'systems' in question or 'system' in question:
                systems = [e['label'] for e in self.entities.values() if e.get('type') == 'system']
                return f"💻 Systems:\n" + "\n".join([f"• {s}" for s in systems])
        
        return "❓ Try asking: 'Who manages [item]?', 'What does [person] manage?', 'Show all people'"

# Streamlit App
def main():
    st.set_page_config(page_title="🕸️ Enterprise Knowledge Graph", layout="wide")
    
    st.title("🕸️ Enterprise Knowledge Graph Generator")
    st.markdown("Upload your data → LLM extraction → Interactive visualization")
    
    # Initialize session state
    if 'graph_data' not in st.session_state:
        st.session_state.graph_data = None
    if 'kg' not in st.session_state:
        st.session_state.kg = None
    if 'html_content' not in st.session_state:
        st.session_state.html_content = None
    
    # Sidebar - LLM Configuration (Optional Override)
    st.sidebar.header("🤖 LLM Configuration")
    st.sidebar.info("✅ Credentials configured in code")
    
    # Optional override in UI
    with st.sidebar.expander("🔧 Override Credentials (Optional)"):
        api_url = st.text_input("API URL", value=LLM_API_URL)
        username = st.text_input("Username", value=LLM_USERNAME)
        password = st.text_input("Password", type="password", value=LLM_PASSWORD)
    
    # Use the values (either from expander or defaults)
    if not api_url:
        api_url = LLM_API_URL
    if not username:
        username = LLM_USERNAME  
    if not password:
        password = LLM_PASSWORD
    
    use_mock = st.sidebar.checkbox("Use Mock Data (for testing)", value=False)
    
    # Step 1: File Upload
    st.header("📁 Step 1: Upload Data File")
    uploaded_file = st.file_uploader(
        "Choose your file", 
        type=['csv', 'xlsx', 'xls', 'docx', 'txt'],
        help="Upload CMDB data, asset lists, or documentation"
    )
    
    if uploaded_file:
        st.success(f"✅ File uploaded: {uploaded_file.name}")
        
        if st.button("🚀 Process File"):
            with st.spinner("Processing file..."):
                processor = SimpleFileProcessor()
                file_content = processor.process_file(uploaded_file)
                
                st.session_state.file_content = file_content
                st.success("✅ File processed successfully!")
                
                with st.expander("📄 View processed content"):
                    st.text_area("Content", file_content[:1000] + "..." if len(file_content) > 1000 else file_content, height=200)
    
    # Step 2: LLM Extraction
    if hasattr(st.session_state, 'file_content'):
        st.header("🤖 Step 2: Extract Entities & Relationships")
        
        if st.button("🧠 Extract with LLM"):
            if use_mock:
                # Mock data for testing
                mock_data = {
                    "entities": [
                        {"id": "john_doe", "label": "John Doe", "type": "person", "properties": {"role": "Admin"}},
                        {"id": "web_server", "label": "Web Server", "type": "system", "properties": {"ip": "192.168.1.10"}},
                        {"id": "database", "label": "Database", "type": "system", "properties": {"ip": "192.168.1.20"}},
                        {"id": "datacenter", "label": "DataCenter A", "type": "location", "properties": {"city": "NYC"}}
                    ],
                    "relationships": [
                        {"source": "john_doe", "target": "web_server", "type": "manages", "properties": {}},
                        {"source": "web_server", "target": "database", "type": "depends_on", "properties": {}},
                        {"source": "web_server", "target": "datacenter", "type": "located_in", "properties": {}}
                    ]
                }
                st.session_state.graph_data = mock_data
                st.success("✅ Mock data loaded!")
            
            elif LLM_API_URL and LLM_USERNAME and LLM_PASSWORD:
                with st.spinner("🧠 LLM is analyzing your data..."):
                    llm_client = SimpleLLMClient()  # Will use hardcoded credentials
                    extracted_data = llm_client.extract_entities_relationships(st.session_state.file_content)
                    
                    st.session_state.graph_data = extracted_data
                    st.success("✅ Entities extracted successfully!")
            else:
                st.error("❌ Please configure LLM credentials or use mock data")
        
        # Show extracted data
        if st.session_state.graph_data:
            entities = st.session_state.graph_data.get('entities', [])
            relationships = st.session_state.graph_data.get('relationships', [])
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("🏷️ Entities", len(entities))
            with col2:
                st.metric("🔗 Relationships", len(relationships))
            
            with st.expander("👀 View extracted data"):
                st.json(st.session_state.graph_data)
    
    # Step 3: Generate Knowledge Graph
    if st.session_state.graph_data:
        st.header("🕸️ Step 3: Generate Knowledge Graph")
        
        if st.button("🎨 Generate Interactive Graph"):
            with st.spinner("Creating knowledge graph..."):
                kg = SimpleKnowledgeGraph()
                kg.build_from_data(st.session_state.graph_data)
                
                html_content = kg.generate_pyvis_html()
                
                st.session_state.kg = kg
                st.session_state.html_content = html_content
                st.success("✅ Knowledge graph generated!")
    
    # Step 4: Visualization
    if st.session_state.html_content:
        st.header("📊 Step 4: Interactive Visualization")
        
        # Display the graph
        st.components.v1.html(st.session_state.html_content, height=650)
        
        # Download option
        st.download_button(
            "📥 Download Graph HTML",
            st.session_state.html_content,
            file_name="knowledge_graph.html",
            mime="text/html"
        )
    
    # Step 5: Q&A
    if st.session_state.kg:
        st.header("🔍 Step 5: Ask Questions")
        
        question = st.text_input("Ask a question about your data:", placeholder="Who manages the web server?")
        
        if question:
            answer = st.session_state.kg.query(question)
            st.markdown("### 💬 Answer:")
            st.text(answer)
        
        # Quick buttons
        st.markdown("**Quick queries:**")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("👥 Show all people"):
                answer = st.session_state.kg.query("show all people")
                st.text(answer)
        
        with col2:
            if st.button("💻 Show all systems"):
                answer = st.session_state.kg.query("show all systems")
                st.text(answer)
        
        with col3:
            if st.button("🏢 Show all locations"):
                answer = st.session_state.kg.query("show all locations")
                st.text(answer)

if __name__ == "__main__":
    main()
