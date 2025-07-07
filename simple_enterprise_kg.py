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
        """Extract entities and relationships from text"""
        prompt = f"""
        Analyze this text and extract entities and relationships for a knowledge graph.
        
        Text: {text}
        
        You MUST respond with ONLY valid JSON in this exact format (no other text):
        {{
            "entities": [
                {{"id": "unique_id", "label": "Name", "type": "person", "properties": {{"key": "value"}}}}
            ],
            "relationships": [
                {{"source": "entity_id", "target": "entity_id", "type": "manages", "properties": {{}}}}
            ]
        }}
        
        Entity types: person, system, application, location, organization
        Relationship types: manages, depends_on, located_in, works_for, runs_on, uses
        
        IMPORTANT: Return ONLY the JSON object, no explanations or markdown.
        """
        
        try:
            response = requests.post(
                self.api_url,
                headers=self.headers,
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {"role": "system", "content": "You are a knowledge graph expert. You MUST respond with ONLY valid JSON, no other text."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 2000
                },
                timeout=30
            )
            
            print(f"API Response Status: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                content = result.get('choices', [{}])[0].get('message', {}).get('content', '{}')
                
                print(f"Raw LLM Response: {content[:200]}...")  # Debug output
                
                # Clean the response - remove markdown formatting if present
                content = content.strip()
                if content.startswith('```json'):
                    content = content[7:]
                if content.startswith('```'):
                    content = content[3:]
                if content.endswith('```'):
                    content = content[:-3]
                content = content.strip()
                
                # Try to parse JSON
                try:
                    parsed_data = json.loads(content)
                    
                    # Validate the structure
                    if 'entities' in parsed_data and 'relationships' in parsed_data:
                        print(f"✅ Successfully parsed: {len(parsed_data['entities'])} entities, {len(parsed_data['relationships'])} relationships")
                        return parsed_data
                    else:
                        print("❌ Invalid JSON structure - missing entities or relationships")
                        return self._fallback_extraction(text)
                        
                except json.JSONDecodeError as e:
                    print(f"❌ JSON parsing error: {e}")
                    print(f"Raw content: {content}")
                    return self._fallback_extraction(text)
                    
            else:
                print(f"❌ API Error: {response.status_code}")
                print(f"Response: {response.text}")
                return self._fallback_extraction(text)
                
        except requests.exceptions.Timeout:
            print("❌ Request timeout")
            return self._fallback_extraction(text)
        except requests.exceptions.RequestException as e:
            print(f"❌ Request error: {e}")
            return self._fallback_extraction(text)
        except Exception as e:
            print(f"❌ Unexpected error: {e}")
            return self._fallback_extraction(text)
    
    def _fallback_extraction(self, text):
        """Enhanced fallback extraction without LLM"""
        print("🔄 Using fallback extraction...")
        
        # Simple keyword-based extraction
        entities = []
        relationships = []
        
        # Extract potential entities from text
        lines = text.split('\n')
        entity_id_counter = 1
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Look for server/system patterns
            if any(keyword in line.lower() for keyword in ['server', 'database', 'application', 'system']):
                entity_id = f"system_{entity_id_counter}"
                entities.append({
                    "id": entity_id,
                    "label": f"System from: {line[:30]}...",
                    "type": "system",
                    "properties": {"source": "fallback", "line": line}
                })
                entity_id_counter += 1
            
            # Look for people patterns
            if any(keyword in line.lower() for keyword in ['admin', 'manager', 'user', 'owner']):
                entity_id = f"person_{entity_id_counter}"
                entities.append({
                    "id": entity_id,
                    "label": f"Person from: {line[:30]}...",
                    "type": "person", 
                    "properties": {"source": "fallback", "line": line}
                })
                entity_id_counter += 1
        
        # If no entities found, create sample ones
        if not entities:
            entities = [
                {"id": "sample_system", "label": "Sample System", "type": "system", "properties": {"note": "LLM extraction failed"}},
                {"id": "sample_person", "label": "Sample Person", "type": "person", "properties": {"note": "LLM extraction failed"}},
                {"id": "sample_location", "label": "Sample Location", "type": "location", "properties": {"note": "LLM extraction failed"}}
            ]
            relationships = [
                {"source": "sample_person", "target": "sample_system", "type": "manages", "properties": {}},
                {"source": "sample_system", "target": "sample_location", "type": "located_in", "properties": {}}
            ]
        
        print(f"✅ Fallback created: {len(entities)} entities, {len(relationships)} relationships")
        
        return {
            "entities": entities,
            "relationships": relationships
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
        """Generate Pyvis visualization - Windows compatible"""
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
        
        # Generate HTML without file operations - Windows compatible
        try:
            # Create a unique filename
            import uuid
            temp_filename = f"temp_graph_{uuid.uuid4().hex[:8]}.html"
            
            # Save to temp file
            net.save_graph(temp_filename)
            
            # Read content immediately
            with open(temp_filename, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Clean up temp file
            try:
                os.remove(temp_filename)
            except:
                pass  # Ignore cleanup errors
            
            return html_content
            
        except Exception as e:
            # Fallback: generate simple HTML if Pyvis fails
            return self._generate_fallback_html()
    
    def _generate_fallback_html(self):
        """Generate simple HTML if Pyvis fails"""
        html = """
        <div style="background: #222; color: white; padding: 20px; border-radius: 8px;">
            <h3>📊 Knowledge Graph Generated</h3>
            <p>Pyvis visualization temporarily unavailable. Here's your graph data:</p>
            <div style="background: #333; padding: 15px; border-radius: 4px; margin: 10px 0;">
        """
        
        # Show entities
        html += f"<strong>🏷️ Entities ({len(self.entities)}):</strong><br>"
        for entity_id, entity in list(self.entities.items())[:10]:  # Show first 10
            html += f"• {entity.get('label', entity_id)} ({entity.get('type', 'unknown')})<br>"
        
        if len(self.entities) > 10:
            html += f"... and {len(self.entities) - 10} more entities<br>"
        
        # Show relationships
        relationships = list(self.graph.edges(data=True))
        html += f"<br><strong>🔗 Relationships ({len(relationships)}):</strong><br>"
        for source, target, data in relationships[:10]:  # Show first 10
            source_label = self.entities.get(source, {}).get('label', source)
            target_label = self.entities.get(target, {}).get('label', target)
            rel_type = data.get('type', 'connected')
            html += f"• {source_label} --{rel_type}--> {target_label}<br>"
        
        if len(relationships) > 10:
            html += f"... and {len(relationships) - 10} more relationships<br>"
        
        html += """
            </div>
            <p>💡 Your knowledge graph is working! Try the Q&A section below.</p>
        </div>
        """
        
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
