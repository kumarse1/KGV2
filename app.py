#!/usr/bin/env python3
"""
Step 7: Complete Knowledge Graph Generator Application
Full Streamlit web interface with all features
Run: streamlit run app.py
"""

import streamlit as st
import tempfile
import os
import json
from datetime import datetime

# Import our modules
from file_processor import FileProcessor
from llm_client import LLMClient, MockLLMClient
from knowledge_graph_enterprise import EnterpriseKnowledgeGraphGenerator
from knowledge_graph_query import KnowledgeGraphQueryEngine

# Page configuration
st.set_page_config(
    page_title="🕸️ Knowledge Graph Generator",
    page_icon="🕸️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #ff7f0e;
        margin-top: 2rem;
        margin-bottom: 1rem;
        border-bottom: 2px solid #ff7f0e;
        padding-bottom: 0.5rem;
    }
    .info-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .success-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .feature-box {
        background-color: #f8f9fa;
        border-left: 4px solid #28a745;
        padding: 1rem;
        margin: 0.5rem 0;
        border-radius: 0 8px 8px 0;
    }
    .metric-container {
        background-color: #f0f8ff;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
        margin: 0.5rem;
    }
    .query-result {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 8px rgba(0,0,0,0.2);
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize all session state variables"""
    defaults = {
        'file_processed': False,
        'file_content': None,
        'extracted_data': None,
        'graph_generated': False,
        'graph_html': None,
        'query_engine': None,
        'kg_generator': None,
        'processing_log': [],
        'current_step': 1
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value

def log_event(message: str):
    """Add event to processing log"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    st.session_state.processing_log.append(f"[{timestamp}] {message}")

def create_llm_client():
    """Create LLM client based on user configuration"""
    st.sidebar.markdown("### 🤖 LLM Configuration")
    
    use_mock = st.sidebar.checkbox(
        "Use Mock LLM (for testing)", 
        value=True,
        help="Use mock LLM for testing without API costs"
    )
    
    if use_mock:
        st.sidebar.success("✅ Mock LLM Client Selected")
        st.sidebar.info("Perfect for testing and demonstrations")
        return MockLLMClient()
    else:
        st.sidebar.markdown("#### Real LLM API Settings")
        
        with st.sidebar.expander("🔧 API Configuration", expanded=True):
            api_url = st.text_input(
                "API URL", 
                value="https://api.openai.com/v1/chat/completions",
                help="Your LLM API endpoint"
            )
            username = st.text_input("Username", help="API username")
            password = st.text_input("Password", type="password", help="API password")
            
            if api_url and username and password:
                client = LLMClient(api_url, username, password)
                
                if st.button("🔍 Test Connection"):
                    with st.spinner("Testing API connection..."):
                        if client.test_connection():
                            st.success("✅ Connection successful!")
                            log_event("LLM API connection successful")
                        else:
                            st.error("❌ Connection failed!")
                            log_event("LLM API connection failed")
                
                return client
            else:
                st.sidebar.warning("⚠️ Please provide all API credentials")
                return None

def display_file_upload_section():
    """Display file upload and processing section"""
    st.markdown('<div class="sub-header">📁 Step 1: Upload Your Data File</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        <h4>📊 Supported File Types</h4>
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-top: 1rem;">
            <div class="feature-box">
                <strong>📈 Excel Files:</strong> .xlsx, .xls<br>
                <small>CMDB data, asset inventories, organizational charts</small>
            </div>
            <div class="feature-box">
                <strong>📄 Word Documents:</strong> .docx<br>
                <small>Process documentation, system descriptions</small>
            </div>
            <div class="feature-box">
                <strong>📋 CSV Files:</strong> .csv<br>
                <small>Structured data exports, database dumps</small>
            </div>
            <div class="feature-box">
                <strong>📝 Text Files:</strong> .txt<br>
                <small>Documentation, configuration files</small>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    uploaded_file = st.file_uploader(
        "Choose your data file",
        type=['xlsx', 'xls', 'docx', 'csv', 'txt'],
        help="Upload your CMDB data or any structured data file"
    )
    
    if uploaded_file is not None:
        st.success(f"✅ File uploaded: **{uploaded_file.name}** ({uploaded_file.size:,} bytes)")
        
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.info(f"📋 File type: **{uploaded_file.type}** | Size: **{uploaded_file.size:,} bytes**")
        
        with col2:
            if st.button("🚀 Process File", type="primary"):
                process_uploaded_file(uploaded_file)
    
    # Show processing log
    if st.session_state.processing_log:
        with st.expander("📜 Processing Log", expanded=False):
            for log_entry in st.session_state.processing_log[-10:]:  # Show last 10 entries
                st.text(log_entry)

def process_uploaded_file(uploaded_file):
    """Process the uploaded file"""
    with st.spinner("🔄 Processing file..."):
        try:
            processor = FileProcessor()
            file_content = processor.process_file(uploaded_file.read(), uploaded_file.name)
            
            st.session_state.file_content = file_content
            st.session_state.file_processed = True
            st.session_state.current_step = 2
            
            log_event(f"File processed: {uploaded_file.name}")
            st.success("✅ File processed successfully!")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
            log_event(f"File processing error: {str(e)}")

def display_file_content_section():
    """Display processed file content"""
    if not st.session_state.get('file_processed', False):
        return
    
    st.markdown('<div class="sub-header">📄 Processed File Content</div>', unsafe_allow_html=True)
    
    content_length = len(st.session_state.file_content)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Content Length", f"{content_length:,} characters")
    with col2:
        st.metric("Word Count", f"{len(st.session_state.file_content.split()):,} words")
    with col3:
        st.metric("Line Count", f"{len(st.session_state.file_content.splitlines()):,} lines")
    
    with st.expander("👀 View File Content", expanded=False):
        # Show preview
        preview = st.session_state.file_content[:2000]
        if len(st.session_state.file_content) > 2000:
            preview += f"\n\n... (showing first 2000 of {content_length:,} characters)"
        
        st.text_area("File Content Preview", preview, height=300, disabled=True)

def display_extraction_section(llm_client):
    """Display entity extraction section"""
    if not st.session_state.get('file_processed', False):
        return
    
    st.markdown('<div class="sub-header">🤖 Step 2: Extract Entities and Relationships</div>', unsafe_allow_html=True)
    
    if llm_client is None:
        st.warning("⚠️ Please configure LLM client in the sidebar to proceed.")
        return
    
    st.markdown("""
    <div class="info-box">
        <h4>🧠 AI-Powered Entity Extraction</h4>
        <p>Our LLM will analyze your data and identify:</p>
        <ul>
            <li><strong>👥 People:</strong> Employees, managers, contacts, users</li>
            <li><strong>🏢 Organizations:</strong> Departments, teams, companies</li>
            <li><strong>💻 Systems:</strong> Servers, databases, applications, networks</li>
            <li><strong>📍 Locations:</strong> Offices, data centers, cities, regions</li>
            <li><strong>🔗 Relationships:</strong> Management, dependencies, locations, ownership</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🎯 Extract Knowledge Graph Data", type="primary"):
        extract_entities_and_relationships(llm_client)

def extract_entities_and_relationships(llm_client):
    """Extract entities and relationships using LLM"""
    with st.spinner("🧠 AI is analyzing your data and extracting entities..."):
        try:
            extracted_data = llm_client.extract_entities_and_relationships(
                st.session_state.file_content
            )
            
            st.session_state.extracted_data = extracted_data
            st.session_state.current_step = 3
            
            log_event(f"Entities extracted: {len(extracted_data.get('entities', []))} entities, {len(extracted_data.get('relationships', []))} relationships")
            
            st.success("✅ Entities and relationships extracted successfully!")
            
            # Display extraction results
            display_extraction_results(extracted_data)
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error during extraction: {str(e)}")
            log_event(f"Extraction error: {str(e)}")

def display_extraction_results(extracted_data):
    """Display the extraction results"""
    entities = extracted_data.get('entities', [])
    relationships = extracted_data.get('relationships', [])
    
    # Summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("🏷️ Total Entities", len(entities))
    with col2:
        st.metric("🔗 Total Relationships", len(relationships))
    with col3:
        entity_types = len(set(e.get('type', 'unknown') for e in entities))
        st.metric("📊 Entity Types", entity_types)
    with col4:
        rel_types = len(set(r.get('type', 'unknown') for r in relationships))
        st.metric("🔄 Relationship Types", rel_types)
    
    # Detailed breakdown
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 🏷️ Entities Preview")
        for i, entity in enumerate(entities[:5]):
            with st.expander(f"{entity.get('label', 'Unknown')} ({entity.get('type', 'unknown')})"):
                st.json(entity)
        
        if len(entities) > 5:
            st.info(f"... and {len(entities) - 5} more entities")
    
    with col2:
        st.markdown("#### 🔗 Relationships Preview")
        for i, rel in enumerate(relationships[:5]):
            source = rel.get('source', 'Unknown')
            target = rel.get('target', 'Unknown')
            rel_type = rel.get('type', 'unknown')
            st.write(f"**{i+1}.** `{source}` --**{rel_type}**--> `{target}`")
        
        if len(relationships) > 5:
            st.info(f"... and {len(relationships) - 5} more relationships")

def display_graph_generation_section():
    """Display graph generation section"""
    if st.session_state.get('extracted_data') is None:
        return
    
    st.markdown('<div class="sub-header">🕸️ Step 3: Generate Knowledge Graph</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        <h4>🎨 Interactive Graph Visualization</h4>
        <p>Create an enterprise-safe, interactive knowledge graph with:</p>
        <ul>
            <li><strong>🔒 Security:</strong> No external dependencies, self-contained HTML</li>
            <li><strong>🎯 Interactivity:</strong> Click, drag, zoom, and explore</li>
            <li><strong>🎨 Visual Appeal:</strong> Color-coded entities and relationships</li>
            <li><strong>📊 Rich Details:</strong> Hover for detailed information</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🚀 Generate Interactive Knowledge Graph", type="primary"):
        generate_knowledge_graph()

def generate_knowledge_graph():
    """Generate the knowledge graph"""
    with st.spinner("🎨 Generating enterprise-safe interactive knowledge graph..."):
        try:
            kg = EnterpriseKnowledgeGraphGenerator()
            kg.create_graph_from_data(st.session_state.extracted_data)
            
            # Save graph as HTML
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as tmp_file:
                html_content = kg.generate_self_contained_html("Knowledge Graph Visualization")
                tmp_file.write(html_content)
                tmp_file.flush()
                
                # Read the HTML content
                with open(tmp_file.name, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                st.session_state.graph_html = html_content
                st.session_state.kg_generator = kg
                st.session_state.graph_generated = True
                st.session_state.current_step = 4
                
                # Create query engine
                query_engine = KnowledgeGraphQueryEngine(
                    kg.graph, 
                    st.session_state.extracted_data['entities'],
                    st.session_state.extracted_data['relationships']
                )
                st.session_state.query_engine = query_engine
                
                # Clean up temp file
                os.unlink(tmp_file.name)
            
            log_event("Knowledge graph generated successfully")
            st.success("✅ Knowledge graph generated successfully!")
            
            # Display graph statistics
            display_graph_statistics(kg)
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error generating graph: {str(e)}")
            log_event(f"Graph generation error: {str(e)}")

def display_graph_statistics(kg):
    """Display graph statistics"""
    stats = kg.get_graph_stats()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("🎯 Total Nodes", stats['total_nodes'])
    with col2:
        st.metric("🔗 Total Edges", stats['total_edges'])
    with col3:
        st.metric("📊 Node Types", len(stats['node_types']))
    with col4:
        st.metric("🔄 Relationship Types", len(stats['relationship_types']))
    
    # Detailed statistics
    with st.expander("📊 Detailed Graph Statistics", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("##### 🏷️ Node Types")
            for node_type, count in stats['node_types'].items():
                st.write(f"• **{node_type}:** {count}")
        
        with col2:
            st.markdown("##### 🔗 Relationship Types")
            for rel_type, count in stats['relationship_types'].items():
                st.write(f"• **{rel_type}:** {count}")

def display_graph_visualization():
    """Display the interactive graph visualization"""
    if not st.session_state.get('graph_generated', False):
        return
    
    st.markdown('<div class="sub-header">📊 Step 4: Explore Your Knowledge Graph</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="success-box">
        <h4>🎉 Your Enterprise-Safe Knowledge Graph is Ready!</h4>
        <p>🔒 <strong>Security Features:</strong> No external dependencies • Self-contained HTML • Data sanitized</p>
        <p>🎮 <strong>Interactive Features:</strong> Click & drag nodes • Hover for details • Zoom & pan • Physics simulation</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Display the graph
    st.components.v1.html(st.session_state.graph_html, height=700)
    
    # Download options
    st.markdown("### 💾 Download Options")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.download_button(
            label="📥 Download Graph (HTML)",
            data=st.session_state.graph_html,
            file_name=f"knowledge_graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html",
            mime="text/html",
            help="Enterprise-safe HTML file with embedded visualization"
        )
    
    with col2:
        json_data = json.dumps(st.session_state.extracted_data, indent=2)
        st.download_button(
            label="📥 Download Data (JSON)",
            data=json_data,
            file_name=f"knowledge_graph_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
            help="Raw entities and relationships data"
        )
    
    with col3:
        if st.session_state.kg_generator:
            stats = st.session_state.kg_generator.get_graph_stats()
            stats_json = json.dumps(stats, indent=2)
            st.download_button(
                label="📥 Download Stats (JSON)",
                data=stats_json,
                file_name=f"graph_statistics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                help="Graph statistics and metrics"
            )

def display_query_section():
    """Display the interactive Q&A section"""
    if st.session_state.get('query_engine') is None:
        return
    
    st.markdown('<div class="sub-header">🤖 Step 5: Ask Questions About Your Data</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        <h4>💬 Natural Language Q&A</h4>
        <p>Ask questions about your knowledge graph in plain English! No complex syntax needed.</p>
        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-top: 1rem;">
            <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px;">
                <strong>🔍 Example Questions:</strong><br>
                • "Who manages Web Server 01?"<br>
                • "What does John Doe manage?"<br>
                • "Dependencies for CRM Application?"
            </div>
            <div style="background: rgba(255,255,255,0.1); padding: 1rem; border-radius: 8px;">
                <strong>📊 Query Types:</strong><br>
                • Management & Ownership<br>
                • Dependencies & Relationships<br>
                • Location-based searches
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Question input
    question = st.text_input(
        "🔍 Ask a question about your data:",
        placeholder="e.g., Who manages the web server?",
        help="Ask questions about entities, relationships, and dependencies"
    )
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if question and st.button("🚀 Search Knowledge Graph", type="primary"):
            process_query(question)
    
    with col2:
        if st.button("🎲 Random Example"):
            examples = [
                "Who manages Web Server 01?",
                "What does John Doe manage?",
                "Dependencies for Database Server?",
                "What is in NYC DataCenter 1?",
                "Show all servers",
                "Show all people"
            ]
            import random
            random_question = random.choice(examples)
            st.session_state.example_question = random_question
            st.rerun()
    
    # Show random example
    if hasattr(st.session_state, 'example_question'):
        st.info(f"💡 Example: {st.session_state.example_question}")
    
    # Quick action buttons
    st.markdown("#### 🚀 Quick Actions")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("👥 All People", use_container_width=True):
            display_query_result("Show all people", st.session_state.query_engine.find_by_type("person"))
    
    with col2:
        if st.button("💻 All Systems", use_container_width=True):
            display_query_result("Show all systems", st.session_state.query_engine.find_by_type("system"))
    
    with col3:
        if st.button("📍 All Locations", use_container_width=True):
            display_query_result("Show all locations", st.session_state.query_engine.find_by_type("location"))

def process_query(question):
    """Process a natural language query"""
    with st.spinner("🔍 Searching knowledge graph..."):
        try:
            result = st.session_state.query_engine.natural_language_query(question)
            log_event(f"Query processed: {question}")
            display_query_result(question, result)
            
        except Exception as e:
            st.error(f"❌ Error processing query: {str(e)}")
            log_event(f"Query error: {str(e)}")

def display_query_result(question, result):
    """Display query results"""
    st.markdown("### 📋 Answer")
    
    if isinstance(result, list):
        # Handle list results (from quick actions)
        if result and 'error' not in result[0] and 'result' not in result[0]:
            st.success(f"✅ Found {len(result)} results:")
            for item in result[:10]:  # Show first 10
                if 'item' in item:
                    with st.expander(f"{item['item']} ({item.get('item_type', 'unknown')})"):
                        st.json(item)
            if len(result) > 10:
                st.info(f"... and {len(result) - 10} more results")
        else:
            st.info("ℹ️ No results found")
        return
    
    query_type = result.get('query_type', 'unknown')
    results = result.get('results', [])
    
    if query_type == 'unknown':
        st.warning("❓ I couldn't understand that question. Here are some suggestions:")
        for suggestion in result.get('suggestions', []):
            st.write(f"💡 {suggestion}")
    
    elif results:
        if isinstance(results, list) and results and 'error' in results[0]:
            st.error(f"❌ {results[0]['error']}")
        
        elif isinstance(results, list) and results and 'result' in results[0]:
            st.info(f"ℹ️ {results[0]['result']}")
        
        else:
            # Process different query types
            if query_type == 'who_manages':
                st.success("👤 **Management Information:**")
                for manager in results:
                    if 'manager' in manager:
                        with st.expander(f"{manager['manager']} ({manager.get('manager_type', 'unknown')})"):
                            st.write(f"**Relationship:** {manager.get('relationship', 'unknown')}")
                            if manager.get('manager_properties'):
                                st.write("**Properties:**")
                                st.json(manager['manager_properties'])
            
            elif query_type == 'what_manages':
                st.success("🔧 **Managed Items:**")
                for item in results:
                    if 'item' in item:
                        with st.expander(f"{item['item']} ({item.get('item_type', 'unknown')})"):
                            st.write(f"**Relationship:** {item.get('relationship', 'unknown')}")
                            if item.get('item_properties'):
                                st.write("**Properties:**")
                                st.json(item['item_properties'])
            
            elif query_type == 'dependencies':
                entity_name = results.get('entity', 'Unknown')
                st.success(f"🔗 **Dependencies for {entity_name}:**")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**🔗 Depends on:**")
                    depends_on = results.get('depends_on', [])
                    if depends_on:
                        for dep in depends_on:
                            st.write(f"• {dep['dependency']} ({dep['dependency_type']})")
                    else:
                        st.write("• No dependencies found")
                
                with col2:
                    st.markdown("**⬅️ What depends on it:**")
                    dependents = results.get('dependents', [])
                    if dependents:
                        for dep in dependents:
                            st.write(f"• {dep['dependent']} ({dep['dependent_type']})")
                    else:
                        st.write("• Nothing depends on this")
            
            elif query_type in ['by_location', 'by_type']:
                st.success(f"📍 **Results:**")
                for item in results[:10]:  # Show first 10
                    if 'item' in item:
                        with st.expander(f"{item['item']} ({item.get('item_type', 'unknown')})"):
                            if item.get('properties'):
                                st.json(item['properties'])
                            st.write(f"**Connections:** {item.get('connections', 0)}")
                
                if len(results) > 10:
                    st.info(f"... and {len(results) - 10} more results")
    
    else:
        st.warning("⚠️ No results found for your query.")

def display_sidebar_info():
    """Display information in the sidebar"""
    st.sidebar.markdown("### 📊 Application Status")
    
    # Progress indicator
    steps = [
        ("📁 File Upload", st.session_state.get('file_processed', False)),
        ("🤖 Entity Extraction", st.session_state.get('extracted_data') is not None),
        ("🕸️ Graph Generation", st.session_state.get('graph_generated', False)),
        ("🔍 Q&A Ready", st.session_state.get('query_engine') is not None)
    ]
    
    for step_name, completed in steps:
        if completed:
            st.sidebar.success(f"✅ {step_name}")
        else:
            st.sidebar.info(f"⏳ {step_name}")
    
    # Statistics
    if st.session_state.get('extracted_data'):
        st.sidebar.markdown("### 📈 Data Statistics")
        entities = st.session_state.extracted_data.get('entities', [])
        relationships = st.session_state.extracted_data.get('relationships', [])
        
        st.sidebar.metric("Entities", len(entities))
        st.sidebar.metric("Relationships", len(relationships))
        
        if st.session_state.get('kg_generator'):
            stats = st.session_state.kg_generator.get_graph_stats()
            st.sidebar.metric("Connected Components", stats.get('connected_components', 0))
    
    # Help section
    st.sidebar.markdown("### ❓ Help & Tips")
    
    with st.sidebar.expander("🚀 Getting Started"):
        st.markdown("""
        1. **Upload** your data file
        2. **Configure** LLM (use Mock for testing)
        3. **Extract** entities and relationships
        4. **Generate** interactive graph
        5. **Ask questions** about your data
        """)
    
    with st.sidebar.expander("💡 Query Examples"):
        st.markdown("""
        • "Who manages [system name]?"
        • "What does [person] manage?"
        • "Dependencies for [application]?"
        • "What is in [location]?"
        • "Show all [entity type]"
        """)
    
    with st.sidebar.expander("🔒 Security Features"):
        st.markdown("""
        • **No external dependencies**
        • **Self-contained HTML**
        • **Data sanitization**
        • **Enterprise-safe**
        • **Offline capable**
        """)

def main():
    """Main application function"""
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.markdown('<div class="main-header">🕸️ Knowledge Graph Generator</div>', unsafe_allow_html=True)
    
    st.markdown("""
    <div class="info-box">
        <h3>🚀 Transform Your Data into Interactive Knowledge Graphs</h3>
        <p>Upload CMDB data, documents, or any structured information and watch it come alive as an interactive, 
        enterprise-safe knowledge graph with powerful Q&A capabilities!</p>
        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 1rem; margin-top: 1rem;">
            <div style="text-align: center;">
                <div style="font-size: 2rem;">📊</div>
                <strong>Multi-Format Support</strong><br>
                <small>Excel, Word, CSV, Text</small>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 2rem;">🔒</div>
                <strong>Enterprise-Safe</strong><br>
                <small>No external dependencies</small>
            </div>
            <div style="text-align: center;">
                <div style="font-size: 2rem;">🤖</div>
                <strong>AI-Powered</strong><br>
                <small>Natural language Q&A</small>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar configuration
    display_sidebar_info()
    llm_client = create_llm_client()
    
    # Main content sections
    display_file_upload_section()
    
    if st.session_state.get('file_processed'):
        display_file_content_section()
        display_extraction_section(llm_client)
    
    if st.session_state.get('extracted_data'):
        display_graph_generation_section()
    
    if st.session_state.get('graph_generated'):
        display_graph_visualization()
        display_query_section()
    
    # Footer
    st.markdown("---")
    st.markdown("### 💡 Pro Tips for Better Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **📁 File Preparation:**
        - Use clear, descriptive entity names
        - Include relationship indicators ("reports to", "manages", "located in")
        - Maintain consistent naming conventions
        - Add relevant metadata and properties
        """)
    
    with col2:
        st.markdown("""
        **🔍 Querying Tips:**
        - Start with simple questions
        - Use entity names as they appear in your data
        - Try different phrasings if first attempt doesn't work
        - Use "Show all [type]" for broad searches
        """)
    
    # Version info
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.caption("🕸️ Knowledge Graph Generator v1.0")
    with col2:
        st.caption("🔒 Enterprise-Safe | 🚀 AI-Powered")
    with col3:
        st.caption(f"📅 Session: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

if __name__ == "__main__":
    main()
        st.sidebar.markdown("
