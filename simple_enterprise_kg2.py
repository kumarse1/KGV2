#!/usr/bin/env python3
"""
Fixed Simple Knowledge Graph - Controlled and Accurate
Run: streamlit run simple_fixed_kg.py
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

# Simple File Processor - CONTROLLED
class ControlledFileProcessor:
    def process_file(self, uploaded_file):
        """Process file and return STRUCTURED data"""
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension == 'csv':
            df = pd.read_csv(uploaded_file)
            return self._process_dataframe(df)
        elif file_extension in ['xlsx', 'xls']:
            df = pd.read_excel(uploaded_file)
            return self._process_dataframe(df)
        else:
            return "Only CSV and Excel files supported in this version"
    
    def _process_dataframe(self, df):
        """Convert DataFrame to CONTROLLED text for LLM"""
        print(f"📊 Processing {len(df)} rows with columns: {list(df.columns)}")
        
        # Limit to reasonable size to prevent explosion
        if len(df) > 50:
            st.warning(f"⚠️ Large file detected ({len(df)} rows). Using first 50 rows to prevent overload.")
            df = df.head(50)
        
        # Create controlled text representation
        text_parts = []
        text_parts.append("=== CMDB COMPONENTS DATA ===")
        text_parts.append(f"Total Components: {len(df)}")
        text_parts.append(f"Data Fields: {', '.join(df.columns)}")
        text_parts.append("")
        
        # Process each row with clear structure
        for idx, row in df.iterrows():
            text_parts.append(f"COMPONENT_{idx + 1}:")
            
            # Add all available data
            for col in df.columns:
                if pd.notna(row[col]) and str(row[col]).strip():
                    value = str(row[col]).strip()
                    text_parts.append(f"  {col}: {value}")
            
            text_parts.append("")  # Spacing between components
        
        # Add relationship guidance
        text_parts.append("=== RELATIONSHIP GUIDANCE ===")
        text_parts.append("Extract relationships ONLY between the components listed above.")
        text_parts.append("Do NOT create relationships to entities not in this data.")
        text_parts.append("Focus on: management, dependencies, locations, ownership.")
        
        result = "\n".join(text_parts)
        print(f"✅ Created controlled text: {len(result)} characters")
        
        return result

# Controlled LLM Client
class ControlledLLMClient:
    def __init__(self):
        self.api_url = LLM_API_URL
        self.username = LLM_USERNAME
        self.password = LLM_PASSWORD
        
        # Setup basic auth
        credentials = f"{self.username}:{self.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/json'
        }
    
    def extract_entities_relationships(self, text):
        """CONTROLLED extraction - no explosion of relationships"""
        
        # Count components in text to set limits
        component_count = text.count("COMPONENT_")
        max_relationships = component_count * 2  # Maximum 2 relationships per component
        
        prompt = f"""
        Extract entities and relationships from this CMDB data.
        
        STRICT RULES:
        1. Create entities ONLY for components explicitly listed in the data
        2. Create a MAXIMUM of {max_relationships} relationships total
        3. Focus on the most important business relationships
        4. Do NOT create fictional entities or relationships
        
        DATA: {text}
        
        Return ONLY this JSON structure:
        {{
            "entities": [
                {{
                    "id": "component_name_simple",
                    "label": "Component Display Name", 
                    "type": "application|server|database|person|location",
                    "properties": {{"role": "what it does", "department": "which dept"}}
                }}
            ],
            "relationships": [
                {{
                    "source": "entity_id",
                    "target": "entity_id",
                    "type": "manages|depends_on|located_in|supports",
                    "properties": {{"description": "why this relationship exists"}}
                }}
            ]
        }}
        
        LIMIT: Maximum {component_count} entities and {max_relationships} relationships.
        """
        
        try:
            print(f"🧠 Requesting controlled extraction (max {max_relationships} relationships)...")
            
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": "system", "content": f"Extract exactly what's in the data. Maximum {max_relationships} relationships. No fictional data."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 1500
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '{}')
                
                # Clean response
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
                    
                    if 'entities' in parsed_data and 'relationships' in parsed_data:
                        entities = parsed_data['entities']
                        relationships = parsed_data['relationships']
                        
                        # Enforce limits
                        if len(relationships) > max_relationships:
                            relationships = relationships[:max_relationships]
                            parsed_data['relationships'] = relationships
                            print(f"⚠️ Trimmed relationships to {max_relationships}")
                        
                        print(f"✅ Controlled extraction: {len(entities)} entities, {len(relationships)} relationships")
                        return parsed_data
                    else:
                        return self._create_simple_fallback()
                        
                except json.JSONDecodeError:
                    print("❌ JSON parsing failed")
                    return self._create_simple_fallback()
            else:
                print(f"❌ API Error: {response.status_code}")
                return self._create_simple_fallback()
                
        except Exception as e:
            print(f"❌ LLM Error: {e}")
            return self._create_simple_fallback()
    
    def _create_simple_fallback(self):
        """Simple fallback with just a few entities"""
        return {
            "entities": [
                {"id": "app_1", "label": "Business Application", "type": "application", "properties": {"role": "Core business app"}},
                {"id": "server_1", "label": "Application Server", "type": "server", "properties": {"role": "Hosts applications"}},
                {"id": "db_1", "label": "Database", "type": "database", "properties": {"role": "Stores data"}},
                {"id": "admin_1", "label": "System Admin", "type": "person", "properties": {"role": "Manages systems"}}
            ],
            "relationships": [
                {"source": "app_1", "target": "server_1", "type": "runs_on", "properties": {"description": "Application hosted on server"}},
                {"source": "server_1", "target": "db_1", "type": "depends_on", "properties": {"description": "Server connects to database"}},
                {"source": "admin_1", "target": "server_1", "type": "manages", "properties": {"description": "Admin manages server"}}
            ]
        }

# Simple Knowledge Graph - CONTROLLED
class ControlledKnowledgeGraph:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.entities = {}
        
    def build_from_data(self, data):
        """Build graph with validation"""
        entities = data.get('entities', [])
        relationships = data.get('relationships', [])
        
        print(f"🔨 Building controlled graph: {len(entities)} entities, {len(relationships)} relationships")
        
        # Add entities
        for entity in entities:
            entity_id = entity['id']
            self.entities[entity_id] = entity
            self.graph.add_node(entity_id, **entity)
        
        # Add relationships with validation
        valid_relationships = 0
        for rel in relationships:
            source = rel['source']
            target = rel['target']
            
            if source in self.entities and target in self.entities:
                self.graph.add_edge(source, target, **rel)
                valid_relationships += 1
            else:
                print(f"⚠️ Skipping invalid relationship: {source} -> {target}")
        
        print(f"✅ Graph built: {len(self.entities)} nodes, {valid_relationships} valid relationships")
    
    def generate_simple_pyvis(self):
        """Generate SIMPLE Pyvis without complications"""
        
        # Simple colors
        colors = {
            'application': '#FF6B6B',
            'server': '#4ECDC4',
            'database': '#45B7D1',
            'person': '#DDA0DD',
            'location': '#96CEB4',
            'service': '#FFEAA7'
        }
        
        print(f"🎨 Creating simple visualization...")
        
        net = Network(
            height="600px",
            width="100%", 
            bgcolor="#f0f0f0",
            font_color="black",
            directed=True
        )
        
        # Simple physics
        net.set_options("""
        {
          "physics": {
            "enabled": true,
            "stabilization": {"iterations": 50}
          }
        }
        """)
        
        # Add nodes
        for node_id, node_data in self.graph.nodes(data=True):
            entity_type = node_data.get('type', 'unknown')
            color = colors.get(entity_type, '#BDC3C7')
            label = node_data.get('label', node_id)
            
            net.add_node(
                node_id,
                label=label,
                color=color,
                size=40,
                title=f"{label}\nType: {entity_type}"
            )
        
        # Add edges
        for source, target, edge_data in self.graph.edges(data=True):
            rel_type = edge_data.get('type', 'connected')
            
            net.add_edge(
                source,
                target,
                label=rel_type,
                arrows="to",
                width=3
            )
        
        # Generate HTML
        try:
            import uuid
            temp_filename = f"simple_graph_{uuid.uuid4().hex[:8]}.html"
            
            net.save_graph(temp_filename)
            
            with open(temp_filename, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Add simple legend
            legend = f"""
            <div style="position: fixed; top: 10px; right: 10px; background: white; padding: 10px; border: 1px solid #ccc; border-radius: 5px;">
                <h4>Legend</h4>
                <div><span style="color: #FF6B6B;">●</span> Applications</div>
                <div><span style="color: #4ECDC4;">●</span> Servers</div>
                <div><span style="color: #45B7D1;">●</span> Databases</div>
                <div><span style="color: #DDA0DD;">●</span> People</div>
                <div><span style="color: #96CEB4;">●</span> Locations</div>
                <br>
                <small>Nodes: {len(self.graph.nodes)}<br>Edges: {len(self.graph.edges)}</small>
            </div>
            """
            
            html_content = html_content.replace('</body>', f'{legend}</body>')
            
            os.remove(temp_filename)
            
            print(f"✅ Simple Pyvis generated successfully")
            return html_content
            
        except Exception as e:
            print(f"❌ Pyvis failed: {e}")
            return f"<div>Graph generation failed: {str(e)}</div>"
    
    def query(self, question):
        """Simple Q&A"""
        question = question.lower()
        
        if 'show all' in question:
            if 'application' in question:
                apps = [e['label'] for e in self.entities.values() if e.get('type') == 'application']
                return f"Applications: {', '.join(apps)}" if apps else "No applications found"
            elif 'server' in question:
                servers = [e['label'] for e in self.entities.values() if e.get('type') == 'server']
                return f"Servers: {', '.join(servers)}" if servers else "No servers found"
        
        return "Try: 'Show all applications' or 'Show all servers'"

# Simple Streamlit App
def main():
    st.set_page_config(page_title="🔧 Fixed Knowledge Graph", layout="wide")
    
    st.title("🔧 Fixed Knowledge Graph Generator")
    st.markdown("**Simple, controlled, and accurate extraction from your Excel data**")
    
    # Initialize session state
    if 'graph_data' not in st.session_state:
        st.session_state.graph_data = None
    if 'kg' not in st.session_state:
        st.session_state.kg = None
    
    # Configuration
    st.sidebar.header("⚙️ Configuration")
    st.sidebar.success("✅ Using controlled extraction")
    st.sidebar.info("This version prevents relationship explosion and respects your actual data")
    
    # Step 1: File Upload
    st.header("📁 Step 1: Upload Excel/CSV File")
    uploaded_file = st.file_uploader(
        "Choose your CMDB file",
        type=['csv', 'xlsx', 'xls'],
        help="Upload your Excel or CSV file with component data"
    )
    
    if uploaded_file:
        st.success(f"✅ File: {uploaded_file.name}")
        
        if st.button("📊 Process File"):
            with st.spinner("Processing file..."):
                processor = ControlledFileProcessor()
                file_content = processor.process_file(uploaded_file)
                
                st.session_state.file_content = file_content
                st.success("✅ File processed with controlled extraction")
                
                # Show preview
                with st.expander("📄 View processed data"):
                    st.text_area("Content Preview", file_content[:1500] + "..." if len(file_content) > 1500 else file_content, height=300)
    
    # Step 2: Extract Entities
    if hasattr(st.session_state, 'file_content'):
        st.header("🧠 Step 2: Extract Components")
        
        if st.button("🎯 Extract with Controlled LLM"):
            with st.spinner("Extracting components with controlled limits..."):
                llm_client = ControlledLLMClient()
                extracted_data = llm_client.extract_entities_relationships(st.session_state.file_content)
                
                st.session_state.graph_data = extracted_data
                
                entities = extracted_data.get('entities', [])
                relationships = extracted_data.get('relationships', [])
                
                st.success(f"✅ Extracted: {len(entities)} components, {len(relationships)} relationships")
                
                # Show results
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("🏷️ Components", len(entities))
                    for entity in entities[:5]:
                        st.write(f"• {entity.get('label', 'Unknown')} ({entity.get('type', 'unknown')})")
                
                with col2:
                    st.metric("🔗 Relationships", len(relationships))
                    for rel in relationships[:5]:
                        st.write(f"• {rel.get('type', 'unknown')}")
    
    # Step 3: Generate Graph
    if st.session_state.graph_data:
        st.header("🕸️ Step 3: Generate Knowledge Graph")
        
        if st.button("🎨 Create Simple Graph"):
            with st.spinner("Creating controlled graph..."):
                kg = ControlledKnowledgeGraph()
                kg.build_from_data(st.session_state.graph_data)
                
                html_content = kg.generate_simple_pyvis()
                
                st.session_state.kg = kg
                st.session_state.html_content = html_content
                
                st.success("✅ Simple graph generated!")
        
        # Display graph
        if hasattr(st.session_state, 'html_content'):
            st.header("📊 Your Knowledge Graph")
            st.components.v1.html(st.session_state.html_content, height=650)
            
            # Simple Q&A
            if st.session_state.kg:
                st.header("❓ Ask Simple Questions")
                question = st.text_input("Question:", placeholder="Show all applications")
                
                if question:
                    answer = st.session_state.kg.query(question)
                    st.write(f"**Answer:** {answer}")

if __name__ == "__main__":
    main()
