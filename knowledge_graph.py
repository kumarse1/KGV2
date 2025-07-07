#!/usr/bin/env python3
"""
Step 5: Knowledge Graph Generator
Creates interactive visualizations using NetworkX and Pyvis
Run: python knowledge_graph.py
"""

import networkx as nx
from pyvis.network import Network
import json
from typing import Dict, List, Any
import os

class KnowledgeGraphGenerator:
    """Generate and visualize knowledge graphs using NetworkX and Pyvis"""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        
        # Color scheme for different entity types
        self.entity_colors = {
            'person': '#FF6B6B',        # Red
            'organization': '#4ECDC4',   # Teal
            'system': '#45B7D1',        # Blue
            'location': '#96CEB4',      # Green
            'asset': '#FFEAA7',         # Yellow
            'process': '#DDA0DD',       # Purple
            'application': '#FFA07A',   # Light Salmon
            'unknown': '#BDC3C7'        # Gray
        }
        
        # Color scheme for different relationship types
        self.relationship_colors = {
            'works_for': '#E74C3C',     # Red
            'manages': '#3498DB',       # Blue
            'reports_to': '#9B59B6',    # Purple
            'located_in': '#2ECC71',    # Green
            'hosted_on': '#F39C12',     # Orange
            'depends_on': '#E67E22',    # Dark Orange
            'owns': '#1ABC9C',          # Turquoise
            'uses': '#34495E',          # Dark Gray
            'maintains': '#8E44AD',     # Dark Purple
            'runs_on': '#16A085',       # Dark Turquoise
            'hosted_in': '#27AE60'      # Dark Green
        }
        
        print("🕸️ KnowledgeGraphGenerator initialized")
        print(f"   Entity types supported: {len(self.entity_colors)}")
        print(f"   Relationship types supported: {len(self.relationship_colors)}")
    
    def add_entities(self, entities: List[Dict[str, Any]]):
        """Add entities to the graph"""
        print(f"📝 Adding {len(entities)} entities to graph...")
        
        for entity in entities:
            entity_id = entity.get('id', 'unknown')
            label = entity.get('label', entity_id)
            entity_type = entity.get('type', 'unknown')
            properties = entity.get('properties', {})
            
            # Add node to NetworkX graph
            self.graph.add_node(
                entity_id,
                label=label,
                type=entity_type,
                color=self.entity_colors.get(entity_type, '#BDC3C7'),
                **properties
            )
            
            print(f"   ✓ {label} ({entity_type})")
    
    def add_relationships(self, relationships: List[Dict[str, Any]]):
        """Add relationships to the graph"""
        print(f"🔗 Adding {len(relationships)} relationships to graph...")
        
        for relationship in relationships:
            source = relationship.get('source', '')
            target = relationship.get('target', '')
            rel_type = relationship.get('type', 'unknown')
            properties = relationship.get('properties', {})
            
            # Check if both nodes exist
            if source in self.graph.nodes and target in self.graph.nodes:
                self.graph.add_edge(
                    source,
                    target,
                    type=rel_type,
                    color=self.relationship_colors.get(rel_type, '#BDC3C7'),
                    **properties
                )
                
                source_label = self.graph.nodes[source].get('label', source)
                target_label = self.graph.nodes[target].get('label', target)
                print(f"   ✓ {source_label} --{rel_type}--> {target_label}")
            else:
                print(f"   ⚠️ Skipping {source} -> {target} (missing nodes)")
    
    def create_graph_from_data(self, graph_data: Dict[str, Any]):
        """Create graph from extracted data"""
        print("🚀 Creating knowledge graph from extracted data...")
        
        # Clear existing graph
        self.graph.clear()
        
        entities = graph_data.get('entities', [])
        relationships = graph_data.get('relationships', [])
        
        print(f"📊 Input data: {len(entities)} entities, {len(relationships)} relationships")
        
        # Add entities first
        self.add_entities(entities)
        
        # Then add relationships
        self.add_relationships(relationships)
        
        print(f"✅ Knowledge graph created successfully!")
        print(f"   Final graph: {len(self.graph.nodes)} nodes, {len(self.graph.edges)} edges")
    
    def generate_pyvis_network(self, height: str = "600px", width: str = "100%") -> Network:
        """Generate Pyvis network for visualization"""
        print("🎨 Generating interactive visualization...")
        
        net = Network(
            height=height,
            width=width,
            bgcolor="#222222",
            font_color="white",
            directed=True
        )
        
        # Configure physics for better layout
        net.set_options("""
        var options = {
            "physics": {
                "enabled": true,
                "stabilization": {"iterations": 100},
                "barnesHut": {
                    "gravitationalConstant": -8000,
                    "centralGravity": 0.3,
                    "springLength": 95,
                    "springConstant": 0.04,
                    "damping": 0.09
                }
            }
        }
        """)
        
        # Add nodes with enhanced styling
        for node_id, node_data in self.graph.nodes(data=True):
            # Create detailed hover info
            properties_text = "\n".join([f"{k}: {v}" for k, v in node_data.items() 
                                       if k not in ['label', 'type', 'color']])
            hover_info = f"Type: {node_data.get('type', 'unknown')}\n{properties_text}"
            
            net.add_node(
                node_id,
                label=node_data.get('label', node_id),
                color=node_data.get('color', '#BDC3C7'),
                title=hover_info,
                size=25,
                font={'size': 12, 'color': 'white'}
            )
        
        # Add edges with enhanced styling
        for source, target, edge_data in self.graph.edges(data=True):
            # Create detailed hover info for edges
            properties_text = "\n".join([f"{k}: {v}" for k, v in edge_data.items() 
                                       if k not in ['type', 'color']])
            hover_info = f"Relationship: {edge_data.get('type', 'unknown')}\n{properties_text}"
            
            net.add_edge(
                source,
                target,
                label=edge_data.get('type', ''),
                color=edge_data.get('color', '#BDC3C7'),
                title=hover_info,
                arrows="to",
                width=2
            )
        
        print(f"✅ Visualization generated: {len(self.graph.nodes)} nodes, {len(self.graph.edges)} edges")
        return net
    
    def save_graph_html(self, filename: str = "knowledge_graph.html") -> str:
        """Save the graph as HTML file"""
        print(f"💾 Saving graph to {filename}...")
        
        net = self.generate_pyvis_network()
        net.save_graph(filename)
        
        # Get absolute path
        abs_path = os.path.abspath(filename)
        
        print(f"✅ Graph saved successfully!")
        print(f"   File: {abs_path}")
        print(f"   Open in browser to view interactive graph")
        
        return filename
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """Get statistics about the graph"""
        print("📊 Calculating graph statistics...")
        
        stats = {
            'total_nodes': len(self.graph.nodes),
            'total_edges': len(self.graph.edges),
            'node_types': {},
            'relationship_types': {},
            'connected_components': nx.number_weakly_connected_components(self.graph)
        }
        
        # Count node types
        for node_id, node_data in self.graph.nodes(data=True):
            node_type = node_data.get('type', 'unknown')
            stats['node_types'][node_type] = stats['node_types'].get(node_type, 0) + 1
        
        # Count relationship types
        for source, target, edge_data in self.graph.edges(data=True):
            rel_type = edge_data.get('type', 'unknown')
            stats['relationship_types'][rel_type] = stats['relationship_types'].get(rel_type, 0) + 1
        
        return stats

def test_knowledge_graph():
    """Test the knowledge graph generator with sample CMDB data"""
    print("🧪 Testing Knowledge Graph Generator...")
    print("=" * 60)
    
    # Create comprehensive sample data
    sample_data = {
        "entities": [
            # People
            {
                "id": "john_doe",
                "label": "John Doe",
                "type": "person",
                "properties": {"department": "IT", "role": "System Administrator", "email": "john.doe@company.com"}
            },
            {
                "id": "jane_smith",
                "label": "Jane Smith",
                "type": "person",
                "properties": {"department": "IT", "role": "Database Administrator", "email": "jane.smith@company.com"}
            },
            {
                "id": "mike_wilson",
                "label": "Mike Wilson",
                "type": "person",
                "properties": {"department": "IT", "role": "IT Manager", "email": "mike.wilson@company.com"}
            },
            # Systems
            {
                "id": "web_server_01",
                "label": "Web Server 01",
                "type": "system",
                "properties": {"ip": "192.168.1.10", "status": "Active", "os": "Linux", "cpu": "4 cores"}
            },
            {
                "id": "database_01",
                "label": "Database Server",
                "type": "system",
                "properties": {"ip": "192.168.1.20", "status": "Active", "type": "MySQL", "storage": "1TB"}
            },
            {
                "id": "crm_app",
                "label": "CRM Application",
                "type": "application",
                "properties": {"version": "2.1", "status": "Production", "users": "500"}
            },
            # Locations
            {
                "id": "nyc_dc1",
                "label": "NYC DataCenter 1",
                "type": "location",
                "properties": {"address": "123 Main St, NYC", "capacity": "100 racks"}
            },
            # Organizations
            {
                "id": "it_department",
                "label": "IT Department",
                "type": "organization",
                "properties": {"budget": "$2M", "headcount": "25"}
            }
        ],
        "relationships": [
            # Management structure
            {"source": "john_doe", "target": "mike_wilson", "type": "reports_to", "properties": {}},
            {"source": "jane_smith", "target": "mike_wilson", "type": "reports_to", "properties": {}},
            
            # System ownership
            {"source": "john_doe", "target": "web_server_01", "type": "manages", "properties": {}},
            {"source": "jane_smith", "target": "database_01", "type": "manages", "properties": {}},
            
            # Technical dependencies
            {"source": "web_server_01", "target": "database_01", "type": "depends_on", "properties": {}},
            {"source": "crm_app", "target": "web_server_01", "type": "runs_on", "properties": {}},
            
            # Location relationships
            {"source": "web_server_01", "target": "nyc_dc1", "type": "located_in", "properties": {}},
            {"source": "database_01", "target": "nyc_dc1", "type": "located_in", "properties": {}},
            
            # Department relationships
            {"source": "john_doe", "target": "it_department", "type": "works_for", "properties": {}},
            {"source": "jane_smith", "target": "it_department", "type": "works_for", "properties": {}},
            {"source": "mike_wilson", "target": "it_department", "type": "manages", "properties": {}}
        ]
    }
    
    print(f"\n📋 Test data prepared:")
    print(f"   Entities: {len(sample_data['entities'])}")
    print(f"   Relationships: {len(sample_data['relationships'])}")
    
    # Create knowledge graph
    kg = KnowledgeGraphGenerator()
    kg.create_graph_from_data(sample_data)
    
    # Get and display statistics
    stats = kg.get_graph_stats()
    print(f"\n📊 Graph Statistics:")
    print(f"   Total nodes: {stats['total_nodes']}")
    print(f"   Total edges: {stats['total_edges']}")
    print(f"   Connected components: {stats['connected_components']}")
    
    print(f"\n🏷️ Node types:")
    for node_type, count in stats['node_types'].items():
        print(f"   • {node_type}: {count}")
    
    print(f"\n🔗 Relationship types:")
    for rel_type, count in stats['relationship_types'].items():
        print(f"   • {rel_type}: {count}")
    
    # Save as HTML
    html_file = kg.save_graph_html("test_knowledge_graph.html")
    
    print(f"\n" + "=" * 60)
    print("✅ Step 5 PASSED - Knowledge Graph Generation works!")
    print(f"🌐 Interactive graph saved as: {html_file}")
    print("👉 Open the HTML file in your browser to see the graph!")
    print("👉 Ready for Step 6: Query Engine")
    
    return kg

if __name__ == "__main__":
    test_kg = test_knowledge_graph()
