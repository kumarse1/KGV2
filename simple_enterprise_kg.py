#!/usr/bin/env python3
"""
Simple Enterprise Knowledge Graph with LLM Basic Auth
Run: streamlit run simple_enterprise_kg.py
"""

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
    def __init__(self, api_url, username, password):
        self.api_url = api_url
        self.username = username
        self.password = password
        
        # Setup basic auth
        credentials = f"{username}:{password}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.headers = {
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/json'
        }
    
    def extract_entities_relationships(self, text):
        """Extract entities and relationships from text"""
        prompt = f"""
        Analyze this text and extract entities and relationships for a knowledge graph.
        
        Text: {text}
        
        Return JSON in this exact format:
        {{
            "entities": [
                {{"id": "unique_id", "label": "Name", "type": "person|system|location|organization", "properties": {{"key": "value"}}}}
            ],
            "relationships": [
                {{"source": "entity_id", "target": "entity_id", "type": "manages|depends_on|located_in|works_for", "properties": {{}}}}
            ]
        }}
        
        Focus on: People, Systems, Applications, Locations, Departments and their relationships.
        """
        
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": "system", "content": "You are a knowledge graph expert. Return only valid JSON."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 2000
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '{}')
                try:
                    return json.loads(content)
                except:
                    return self._fallback_extraction(text)
            else:
                st.error(f"API Error: {response.status_code}")
                return self._fallback_extraction(text)
                
        except Exception as e:
            st.error(f"LLM Error: {str(e)}")
            return self._fallback_extraction(text)
    
    def _fallback_extraction(self, text):
        """Simple fallback extraction without LLM"""
        return {
            "entities": [
                {"id": "sample_entity", "label": "Sample Entity", "type": "system", "properties": {"note": "LLM failed, using fallback"}}
            ],
            "relationships": []
        }

# Simple File Processor
class SimpleFileProcessor:
    def process_file(self, uploaded_file):
        """Process uploaded file and return text content"""
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension == 'csv':
            df = pd.read_csv(uploaded_file)
            return self._df_to_text(df)
        elif file_extension in ['xlsx', 'xls']:
            df = pd.read_excel(uploaded_file)
            return self._df_to_text(df)
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
    
    def _df_to_text(self, df):
        """Convert DataFrame to descriptive text"""
        text_content = []
        text_content.append(f"Data contains {len(df)} rows and {len(df.columns)} columns")
        text_content.append(f"Columns: {', '.join(df.columns.tolist())}")
        text_content.append("\nData samples:")
        
        for idx, row in df.head(10).iterrows():
            row_text = []
            for col in df.columns:
                if pd.notna(row[col]):
                    row_text.append(f"{col}: {row[col]}")
            text_content.append(f"Record {idx + 1}: {', '.join(row_text)}")
        
        return "\n".join(text_content)

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
        """Generate Pyvis visualization"""
        net = Network(height="600px", width="100%", bgcolor="#222222", font_color="white", directed=True)
        
        # Colors for different entity types
        colors = {
            'person': '#FF6B6B',
            'system': '#4ECDC4',
            'application': '#45B7D1',
            'location': '#96CEB4',
            'organization': '#FFEAA7'
        }
        
        # Add nodes
        for node_id, node_data in self.graph.nodes(data=True):
            color = colors.get(node_data.get('type', 'unknown'), '#BDC3C7')
            net.add_node(
                node_id,
                label=node_data.get('label', node_id),
                color=color,
                title=f"Type: {node_data.get('type', 'unknown')}",
                size=25
            )
        
        # Add edges
        for source, target, edge_data in self.graph.edges(data=True):
            net.add_edge(
                source,
                target,
                label=edge_data.get('type', ''),
                color='#848484',
                arrows="to"
            )
        
        # Generate HTML
        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp_file:
            net.save_graph(tmp_file.name)
            with open(tmp_file.name, 'r') as f:
                html_content = f.read()
            os.unlink(tmp_file.name)
        
        return html_content
    
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
    
    # Sidebar - LLM Configuration
    st.sidebar.header("🤖 LLM Configuration")
    api_url = st.sidebar.text_input("API URL", value="https://api.openai.com/v1/chat/completions")
    username = st.sidebar.text_input("Username")
    password = st.sidebar.text_input("Password", type="password")
    
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
            
            elif api_url and username and password:
                with st.spinner("🧠 LLM is analyzing your data..."):
                    llm_client = SimpleLLMClient(api_url, username, password)
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
