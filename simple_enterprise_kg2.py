import streamlit as st

# MUST BE FIRST STREAMLIT COMMAND - BEFORE ANYTHING ELSE
st.set_page_config(page_title="🔧 Knowledge Graph", layout="wide")

import pandas as pd
import requests
import base64
import json
import networkx as nx
from pyvis.network import Network
import os
import io

# Credentials
LLM_API_URL = "https://your-api-endpoint.com/v1/chat/completions"
LLM_USERNAME = "your_username_here"
LLM_PASSWORD = "your_password_here"

class FileProcessor:
    def process_file(self, uploaded_file):
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension == 'csv':
            df = pd.read_csv(uploaded_file)
            return self._process_dataframe(df)
        elif file_extension in ['xlsx', 'xls']:
            df = pd.read_excel(uploaded_file)
            return self._process_dataframe(df)
        else:
            return "Only CSV and Excel supported"
    
    def _process_dataframe(self, df):
        # Limit size
        if len(df) > 15:
            st.warning(f"Large file ({len(df)} rows). Using first 15 rows.")
            df = df.head(15)
        
        text_parts = ["=== COMPONENTS ==="]
        
        for idx, row in df.iterrows():
            text_parts.append(f"COMPONENT_{idx + 1}:")
            for col in df.columns:
                if pd.notna(row[col]):
                    text_parts.append(f"  {col}: {row[col]}")
            text_parts.append("")
        
        return "\n".join(text_parts)

class LLMClient:
    def __init__(self):
        credentials = f"{LLM_USERNAME}:{LLM_PASSWORD}"
        encoded = base64.b64encode(credentials.encode()).decode()
        self.headers = {
            'Authorization': f'Basic {encoded}',
            'Content-Type': 'application/json'
        }
    
    def extract(self, text):
        component_count = text.count("COMPONENT_")
        max_rels = min(component_count * 2, 10)
        
        prompt = f"""Extract from: {text}
        
        JSON format:
        {{"entities": [{{"id": "id", "label": "name", "type": "application|server|person", "properties": {{"role": "function"}}}}],
          "relationships": [{{"source": "id1", "target": "id2", "type": "manages|depends_on", "properties": {{"description": "why"}}}}]}}
        
        Max {max_rels} relationships."""
        
        try:
            response = requests.post(
                LLM_API_URL,
                headers=self.headers,
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.1,
                    "max_tokens": 800
                },
                timeout=30
            )
            
            if response.status_code == 200:
                content = response.json()['choices'][0]['message']['content']
                content = content.strip()
                if content.startswith('```'):
                    content = content[content.find('{'):content.rfind('}')+1]
                
                data = json.loads(content)
                
                # Limit relationships
                if len(data.get('relationships', [])) > max_rels:
                    data['relationships'] = data['relationships'][:max_rels]
                
                return data
            else:
                return self._fallback()
                
        except Exception:
            return self._fallback()
    
    def _fallback(self):
        return {
            "entities": [
                {"id": "app1", "label": "App", "type": "application", "properties": {"role": "business"}},
                {"id": "server1", "label": "Server", "type": "server", "properties": {"role": "hosting"}},
                {"id": "admin1", "label": "Admin", "type": "person", "properties": {"role": "management"}}
            ],
            "relationships": [
                {"source": "app1", "target": "server1", "type": "runs_on", "properties": {"description": "hosted"}},
                {"source": "admin1", "target": "server1", "type": "manages", "properties": {"description": "responsible"}}
            ]
        }

class KnowledgeGraph:
    def __init__(self):
        self.graph = nx.DiGraph()
        self.entities = {}
        
    def build(self, data):
        for entity in data.get('entities', []):
            self.entities[entity['id']] = entity
            self.graph.add_node(entity['id'], **entity)
        
        for rel in data.get('relationships', []):
            if rel['source'] in self.entities and rel['target'] in self.entities:
                self.graph.add_edge(rel['source'], rel['target'], **rel)
    
    def generate_html(self):
        colors = {
            'application': '#FF6B6B',
            'server': '#4ECDC4', 
            'database': '#45B7D1',
            'person': '#DDA0DD'
        }
        
        net = Network(height="400px", width="100%", bgcolor="#f0f0f0")
        
        for node_id, node_data in self.graph.nodes(data=True):
            color = colors.get(node_data.get('type'), '#BDC3C7')
            net.add_node(
                node_id,
                label=node_data.get('label', node_id),
                color=color,
                size=25
            )
        
        for source, target, edge_data in self.graph.edges(data=True):
            net.add_edge(source, target, label=edge_data.get('type', ''))
        
        try:
            import uuid
            filename = f"temp_{uuid.uuid4().hex[:6]}.html"
            net.save_graph(filename)
            
            with open(filename, 'r') as f:
                content = f.read()
            
            os.remove(filename)
            return content
        except:
            return "<div>Graph generation failed</div>"

def main():
    st.title("🔧 Simple Knowledge Graph")
    
    # Session state
    if 'data' not in st.session_state:
        st.session_state.data = None
    
    # Upload
    st.header("📁 Upload File")
    file = st.file_uploader("Choose CSV/Excel", type=['csv', 'xlsx'])
    
    if file:
        if st.button("Process"):
            processor = FileProcessor()
            content = processor.process_file(file)
            st.session_state.content = content
            st.success("Processed")
            
            with st.expander("Preview"):
                st.text(content[:500])
    
    # Extract
    if hasattr(st.session_state, 'content'):
        st.header("🧠 Extract")
        if st.button("Extract"):
            client = LLMClient()
            data = client.extract(st.session_state.content)
            st.session_state.data = data
            
            entities = data.get('entities', [])
            relationships = data.get('relationships', [])
            st.success(f"Found {len(entities)} entities, {len(relationships)} relationships")
    
    # Graph
    if st.session_state.data:
        st.header("🕸️ Graph")
        if st.button("Generate"):
            kg = KnowledgeGraph()
            kg.build(st.session_state.data)
            html = kg.generate_html()
            st.session_state.html = html
            st.success("Graph created")
        
        if hasattr(st.session_state, 'html'):
            st.components.v1.html(st.session_state.html, height=450)

if __name__ == "__main__":
    main()
