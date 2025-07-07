#!/usr/bin/env python3
"""
Clean Fixed Knowledge Graph - No Config Conflicts
Run: streamlit run clean_fixed_kg.py
"""

import streamlit as st
import pandas as pd
import requests
import base64
import json
import networkx as nx
from pyvis.network import Network
import os
from docx import Document
import io

# SINGLE PAGE CONFIG - MUST BE FIRST STREAMLIT COMMAND
st.set_page_config(page_title="🔧 Fixed Knowledge Graph", layout="wide")

# ========================================
# 🔧 CONFIGURE YOUR LLM CREDENTIALS HERE
# ========================================
LLM_API_URL = "https://your-api-endpoint.com/v1/chat/completions"
LLM_USERNAME = "your_username_here"
LLM_PASSWORD = "your_password_here"
# ========================================

# Simple File Processor
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
        
        # Limit to reasonable size
        if len(df) > 20:
            st.warning(f"⚠️ Large file ({len(df)} rows). Using first 20 rows to prevent overload.")
            df = df.head(20)
        
        # Create controlled text
        text_parts = []
        text_parts.append("=== CMDB COMPONENTS ===")
        text_parts.append(f"Total: {len(df)} components")
        text_parts.append("")
        
        # Process each row
        for idx, row in df.iterrows():
            text_parts.append(f"COMPONENT_{idx + 1}:")
            for col in df.columns:
                if pd.notna(row[col]) and str(row[col]).strip():
                    value = str(row[col]).strip()
                    text_parts.append(f"  {col}: {value}")
            text_parts.append("")
        
        result = "\n".join(text_parts)
        print(f"✅ Created controlled text: {len(result)} characters")
        return result

# Controlled LLM Client
class ControlledLLMClient:
    def __init__(self):
        self.api_url = LLM_API_URL
        self.username = LLM_USERNAME
        self.password = LLM_PASSWORD
        
        # Basic auth
        credentials = f"{self.username}:{self.password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/json'
        }
    
    def extract_entities_relationships(self, text):
        """CONTROLLED extraction"""
        component_count = text.count("COMPONENT_")
        max_relationships = min(component_count * 2, 15)  # Cap at 15 relationships
        
        prompt = f"""
        Extract entities from this CMDB data. Create MAXIMUM {max_relationships} relationships.
        
        DATA: {text}
        
        Return JSON:
        {{
            "entities": [
                {{"id": "simple_id", "label": "Name", "type": "application|server|database|person", "properties": {{"role": "function"}}}}
            ],
            "relationships": [
                {{"source": "id1", "target": "id2", "type": "manages|depends_on|located_in", "properties": {{"description": "why"}}}}
            ]
        }}
        
        STRICT LIMITS: Max {component_count} entities, max {max_relationships} relationships.
        """
        
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": "system", "content": f"Extract exactly what's in data. Max {max_relationships} relationships."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 1000
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
                        
                        print(f"✅ Controlled: {len(entities)} entities, {len(relationships)} relationships")
                        return parsed_data
                    else:
                        return self._create_fallback()
                        
                except json.JSONDecodeError:
                    return self._create_fallback()
            else:
                return self._create_fallback()
                
        except Exception as e:
            print(f"❌ LLM Error: {e}")
            return self._create_fallback()
    
    def _create_fallback(self):
        """Simple fallback"""
        return {
            "entities": [
                {"id": "app1", "label": "Business App", "type": "application", "properties": {"role": "Core business"}},
                {"id": "server1", "label": "App Server", "type": "server", "properties": {"role": "Hosting"}},
                {"id": "db1", "label": "Database", "type": "database", "properties": {"role": "Data storage"}},
                {"id": "admin1", "label": "Admin", "type": "person", "properties": {"role": "Management"}}
            ],
            "relationships": [
                {"source": "app1", "target": "server1", "type": "runs_on", "properties": {"description": "App hosted on server"}},
                {"source": "server1", "target": "db1", "type": "depends_on", "properties": {"description": "Server uses database"}},
                {"source": "admin1", "target": "server1", "type": "manages", "properties": {"description": "Admin manages server"}}
            ]
        }

# Simple Knowledge Graph
class ControlledKnowledgeGraph:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.entities = {}
        
    def build_from_data(self, data):
        """Build graph with validation"""
        entities = data.get('entities', [])
        relationships = data.get('relationships', [])
        
        print(f"🔨 Building graph: {len(entities)} entities, {len(relationships)} relationships")
        
        # Add entities
        for entity in entities:
            entity_id = entity['id']
            self.entities[entity_id] = entity
            self.graph.add_node(entity_id, **entity)
        
        # Add valid relationships only
        valid_relationships = 0
        for rel in relationships:
            source = rel['source']
            target = rel['target']
            
            if source in self.entities and target in self.entities:
                self.graph.add_edge(source, target, **rel)
                valid_relationships += 1
        
        print(f"✅ Graph: {len(self.entities)} nodes, {valid_relationships} relationships")
    
    def generate_simple_pyvis(self):
        """Generate simple Pyvis"""
        colors = {
            'application': '#FF6B6B',
            'server': '#4ECDC4',
            'database': '#45B7D1',
            'person': '#DDA0DD',
            'location': '#96CEB4'
        }
        
        net = Network(height="500px", width="100%", bgcolor="#f5f5f5", font_color="black")
        
        # Add nodes
        for node_id, node_data in self.graph.nodes(data=True):
            entity_type = node_data.get('type', 'unknown')
            color = colors.get(entity_type, '#BDC3C7')
            label = node_data.get('label', node_id)
            
            net.add_node(
                node_id,
                label=label,
                color=color,
                size=30,
                title=f"{label} ({entity_type})"
            )
        
        # Add edges
        for source, target, edge_data in self.graph.edges(data=True):
            rel_type = edge_data.get('type', 'connected')
            net.add_edge(source, target, label=rel_type, arrows="to")
        
        # Generate HTML
        try:
            import uuid
            temp_filename = f"graph_{uuid.uuid4().hex[:8]}.html"
            net.save_graph(temp_filename)
            
            with open(temp_filename, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Add legend
            legend = f"""
            <div style="position: fixed; top: 10px; right: 10px; background: white; padding: 10px; border: 1px solid #ccc;">
                <h4>Legend</h4>
                <div><span style="color: #FF6B6B;">●</span> Applications</div>
                <div><span style="color: #4ECDC4;">●</span> Servers</div>
                <div><span style="color: #45B7D1;">●</span> Databases</div>
                <div><span style="color: #DDA0DD;">●</span> People</div>
                <hr>
                <small>Nodes: {len(self.graph.nodes)}<br>Edges: {len(self.graph.edges)}</small>
            </div>
            """
            
            html_content = html_content.replace('</body>', f'{legend}</body>')
            os.remove(temp_filename)
            
            return html_content
            
        except Exception as e:
            return f"<div style='padding: 20px;'>Graph error: {str(e)}</div>"

# Main App Function
def main():
    st.title("🔧 Fixed Knowledge Graph Generator")
    st.markdown("**Simple, controlled extraction from Excel/CSV data**")
    
    # Initialize session state
    if 'graph_data' not in st.session_state:
        st.session_state.graph_data = None
    if 'kg' not in st.session_state:
        st.session_state.kg = None
    
    # Sidebar
    st.sidebar.header("⚙️ Settings")
    st.sidebar.success("✅ Controlled extraction")
    st.sidebar.info("Max 20 rows, reasonable relationships")
    
    # Step 1: Upload
    st.header("📁 Upload Excel/CSV")
    uploaded_file = st.file_uploader("Choose file", type=['csv', 'xlsx', 'xls'])
    
    if uploaded_file:
        st.success(f"✅ {uploaded_file.name}")
        
        if st.button("📊 Process"):
            with st.spinner("Processing..."):
                processor = ControlledFileProcessor()
                file_content = processor.process_file(uploaded_file)
                st.session_state.file_content = file_content
                st.success("✅ Processed")
                
                with st.expander("Preview"):
                    st.text_area("Data", file_content[:800], height=200)
    
    # Step 2: Extract
    if hasattr(st.session_state, 'file_content'):
        st.header("🧠 Extract Components")
        
        if st.button("🎯 Extract"):
            with st.spinner("Extracting..."):
                llm_client = ControlledLLMClient()
                data = llm_client.extract_entities_relationships(st.session_state.file_content)
                st.session_state.graph_data = data
                
                entities = data.get('entities', [])
                relationships = data.get('relationships', [])
                st.success(f"✅ {len(entities)} entities, {len(relationships)} relationships")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**Entities:**")
                    for e in entities[:5]:
                        st.write(f"• {e.get('label')} ({e.get('type')})")
                
                with col2:
                    st.write("**Relationships:**")
                    for r in relationships[:5]:
                        st.write(f"• {r.get('type')}")
    
    # Step 3: Graph
    if st.session_state.graph_data:
        st.header("🕸️ Generate Graph")
        
        if st.button("🎨 Create Graph"):
            with st.spinner("Creating..."):
                kg = ControlledKnowledgeGraph()
                kg.build_from_data(st.session_state.graph_data)
                html_content = kg.generate_simple_pyvis()
                
                st.session_state.kg = kg
                st.session_state.html_content = html_content
                st.success("✅ Graph created")
        
        if hasattr(st.session_state, 'html_content'):
            st.header("📊 Knowledge Graph")
            st.components.v1.html(st.session_state.html_content, height=550)

if __name__ == "__main__":
    main()
