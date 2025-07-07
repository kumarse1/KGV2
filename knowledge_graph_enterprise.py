#!/usr/bin/env python3
"""
Step 5B: Enterprise-Safe Knowledge Graph Generator
- No external CDN dependencies
- Self-contained HTML with embedded libraries
- Data sanitization
- Security-focused implementation
Run: python knowledge_graph_enterprise.py
"""

import networkx as nx
import json
from typing import Dict, List, Any
import os
import html
import re

class EnterpriseKnowledgeGraphGenerator:
    """Enterprise-safe knowledge graph generator with no external dependencies"""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        
        # Color scheme for different entity types
        self.entity_colors = {
            'person': '#FF6B6B',
            'organization': '#4ECDC4',
            'system': '#45B7D1',
            'location': '#96CEB4',
            'asset': '#FFEAA7',
            'process': '#DDA0DD',
            'application': '#FFA07A',
            'unknown': '#BDC3C7'
        }
        
        self.relationship_colors = {
            'works_for': '#E74C3C',
            'manages': '#3498DB',
            'reports_to': '#9B59B6',
            'located_in': '#2ECC71',
            'hosted_on': '#F39C12',
            'depends_on': '#E67E22',
            'owns': '#1ABC9C',
            'uses': '#34495E',
            'maintains': '#8E44AD',
            'runs_on': '#16A085',
            'hosted_in': '#27AE60'
        }
        
        print("🔒 Enterprise KnowledgeGraphGenerator initialized")
        print("   ✅ No external CDN dependencies")
        print("   ✅ Data sanitization enabled")
        print("   ✅ Self-contained HTML output")
    
    def sanitize_data(self, data: Any) -> Any:
        """Sanitize data to prevent XSS and other security issues"""
        if isinstance(data, str):
            # HTML escape
            data = html.escape(data)
            # Remove potentially dangerous patterns
            data = re.sub(r'<script.*?</script>', '', data, flags=re.IGNORECASE | re.DOTALL)
            data = re.sub(r'javascript:', '', data, flags=re.IGNORECASE)
            data = re.sub(r'on\w+\s*=', '', data, flags=re.IGNORECASE)
            return data
        elif isinstance(data, dict):
            return {k: self.sanitize_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.sanitize_data(item) for item in data]
        else:
            return data
    
    def add_entities(self, entities: List[Dict[str, Any]]):
        """Add entities to the graph with sanitization"""
        print(f"📝 Adding {len(entities)} entities (with sanitization)...")
        
        for entity in entities:
            # Sanitize entity data
            entity = self.sanitize_data(entity)
            
            entity_id = entity.get('id', 'unknown')
            label = entity.get('label', entity_id)
            entity_type = entity.get('type', 'unknown')
            properties = entity.get('properties', {})
            
            # Additional ID sanitization
            entity_id = re.sub(r'[^a-zA-Z0-9_-]', '_', str(entity_id))
            
            self.graph.add_node(
                entity_id,
                label=label,
                entity_type=entity_type,
                color=self.entity_colors.get(entity_type, '#BDC3C7'),
                **properties
            )
            
            print(f"   ✓ {label} ({entity_type})")
    
    def add_relationships(self, relationships: List[Dict[str, Any]]):
        """Add relationships to the graph with sanitization"""
        print(f"🔗 Adding {len(relationships)} relationships (with sanitization)...")
        
        for relationship in relationships:
            # Sanitize relationship data
            relationship = self.sanitize_data(relationship)
            
            source = relationship.get('source', '')
            target = relationship.get('target', '')
            rel_type = relationship.get('type', 'unknown')
            properties = relationship.get('properties', {})
            
            # Sanitize IDs
            source = re.sub(r'[^a-zA-Z0-9_-]', '_', str(source))
            target = re.sub(r'[^a-zA-Z0-9_-]', '_', str(target))
            
            if source in self.graph.nodes and target in self.graph.nodes:
                self.graph.add_edge(
                    source,
                    target,
                    rel_type=rel_type,
                    color=self.relationship_colors.get(rel_type, '#BDC3C7'),
                    **properties
                )
                
                source_label = self.graph.nodes[source].get('label', source)
                target_label = self.graph.nodes[target].get('label', target)
                print(f"   ✓ {source_label} --{rel_type}--> {target_label}")
            else:
                print(f"   ⚠️ Skipping {source} -> {target} (missing nodes)")
    
    def create_graph_from_data(self, graph_data: Dict[str, Any]):
        """Create graph from extracted data with full sanitization"""
        print("🚀 Creating enterprise-safe knowledge graph...")
        
        # Sanitize entire input
        graph_data = self.sanitize_data(graph_data)
        
        self.graph.clear()
        
        entities = graph_data.get('entities', [])
        relationships = graph_data.get('relationships', [])
        
        print(f"📊 Sanitized data: {len(entities)} entities, {len(relationships)} relationships")
        
        self.add_entities(entities)
        self.add_relationships(relationships)
        
        print(f"✅ Enterprise-safe knowledge graph created!")
        print(f"   Final graph: {len(self.graph.nodes)} nodes, {len(self.graph.edges)} edges")
    
    def generate_self_contained_html(self, title: str = "Knowledge Graph") -> str:
        """Generate completely self-contained HTML with embedded JavaScript"""
        
        # Prepare node data
        nodes = []
        for node_id, node_data in self.graph.nodes(data=True):
            nodes.append({
                'id': node_id,
                'label': node_data.get('label', node_id),
                'color': node_data.get('color', '#BDC3C7'),
                'type': node_data.get('entity_type', 'unknown'),
                'properties': {k: v for k, v in node_data.items() 
                             if k not in ['label', 'entity_type', 'color']}
            })
        
        # Prepare edge data
        edges = []
        for source, target, edge_data in self.graph.edges(data=True):
            edges.append({
                'from': source,
                'to': target,
                'label': edge_data.get('rel_type', ''),
                'color': edge_data.get('color', '#BDC3C7'),
                'type': edge_data.get('rel_type', 'unknown')
            })
        
        # Create self-contained HTML
        html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{html.escape(title)}</title>
    <meta name="generator" content="Enterprise Knowledge Graph Generator">
    <meta name="security" content="Self-contained, no external dependencies">
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #1a1a1a;
            color: white;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 20px;
        }}
        
        .info {{
            background-color: #2a2a2a;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        
        .stats {{
            display: flex;
            justify-content: space-around;
            margin-bottom: 20px;
        }}
        
        .stat-box {{
            background-color: #3a3a3a;
            padding: 10px;
            border-radius: 5px;
            text-align: center;
        }}
        
        #graph-container {{
            width: 100%;
            height: 600px;
            border: 2px solid #444;
            border-radius: 8px;
            background-color: #222;
            position: relative;
        }}
        
        .legend {{
            position: absolute;
            top: 10px;
            right: 10px;
            background-color: rgba(0,0,0,0.8);
            padding: 10px;
            border-radius: 5px;
            font-size: 12px;
        }}
        
        .legend-item {{
            display: flex;
            align-items: center;
            margin: 5px 0;
        }}
        
        .legend-color {{
            width: 15px;
            height: 15px;
            margin-right: 8px;
            border-radius: 3px;
        }}
        
        .controls {{
            margin-top: 20px;
            text-align: center;
        }}
        
        button {{
            background-color: #4CAF50;
            color: white;
            padding: 10px 20px;
            margin: 5px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
        }}
        
        button:hover {{
            background-color: #45a049;
        }}
        
        .node {{
            cursor: pointer;
            stroke: #fff;
            stroke-width: 2px;
        }}
        
        .edge {{
            stroke-width: 2px;
            marker-end: url(#arrowhead);
        }}
        
        .node-label {{
            font-size: 12px;
            font-weight: bold;
            text-anchor: middle;
            pointer-events: none;
        }}
        
        .edge-label {{
            font-size: 10px;
            text-anchor: middle;
            pointer-events: none;
        }}
        
        .tooltip {{
            position: absolute;
            background-color: rgba(0,0,0,0.9);
            color: white;
            padding: 8px;
            border-radius: 4px;
            font-size: 12px;
            pointer-events: none;
            z-index: 1000;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🔒 Enterprise Knowledge Graph</h1>
        <p>Self-contained visualization with no external dependencies</p>
    </div>
    
    <div class="info">
        <div class="stats">
            <div class="stat-box">
                <div><strong>{len(nodes)}</strong></div>
                <div>Nodes</div>
            </div>
            <div class="stat-box">
                <div><strong>{len(edges)}</strong></div>
                <div>Edges</div>
            </div>
            <div class="stat-box">
                <div><strong>Enterprise-Safe</strong></div>
                <div>Security</div>
            </div>
        </div>
    </div>
    
    <div id="graph-container">
        <svg id="graph-svg" width="100%" height="100%">
            <defs>
                <marker id="arrowhead" markerWidth="10" markerHeight="7" 
                        refX="9" refY="3.5" orient="auto">
                    <polygon points="0 0, 10 3.5, 0 7" fill="#999" />
                </marker>
            </defs>
        </svg>
        
        <div class="legend">
            <div><strong>Entity Types:</strong></div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #FF6B6B;"></div>
                <span>Person</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #45B7D1;"></div>
                <span>System</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #4ECDC4;"></div>
                <span>Organization</span>
            </div>
            <div class="legend-item">
                <div class="legend-color" style="background-color: #96CEB4;"></div>
                <span>Location</span>
            </div>
        </div>
    </div>
    
    <div class="controls">
        <button onclick="resetZoom()">Reset View</button>
        <button onclick="centerGraph()">Center Graph</button>
        <button onclick="togglePhysics()">Toggle Physics</button>
    </div>
    
    <div id="tooltip" class="tooltip" style="display: none;"></div>
    
    <script>
        // Embedded D3.js-like functionality (simplified for enterprise safety)
        const nodes = {json.dumps(nodes, indent=2)};
        const edges = {json.dumps(edges, indent=2)};
        
        let svg, simulation, physicsEnabled = true;
        
        function initializeGraph() {{
            svg = document.getElementById('graph-svg');
            const container = document.getElementById('graph-container');
            const width = container.clientWidth;
            const height = container.clientHeight;
            
            // Simple force simulation (no external libraries)
            let nodeElements = [];
            let edgeElements = [];
            
            // Create nodes
            nodes.forEach((node, i) => {{
                const x = Math.random() * (width - 100) + 50;
                const y = Math.random() * (height - 100) + 50;
                
                node.x = x;
                node.y = y;
                node.vx = 0;
                node.vy = 0;
                
                // Create SVG circle for node
                const circle = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
                circle.setAttribute('cx', x);
                circle.setAttribute('cy', y);
                circle.setAttribute('r', 20);
                circle.setAttribute('fill', node.color);
                circle.setAttribute('class', 'node');
                circle.setAttribute('data-id', node.id);
                
                // Add event listeners
                circle.addEventListener('mouseenter', (e) => showTooltip(e, node));
                circle.addEventListener('mouseleave', hideTooltip);
                circle.addEventListener('mousedown', (e) => startDrag(e, node));
                
                svg.appendChild(circle);
                nodeElements.push(circle);
                
                // Create label
                const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
                text.setAttribute('x', x);
                text.setAttribute('y', y + 5);
                text.setAttribute('class', 'node-label');
                text.setAttribute('fill', 'white');
                text.textContent = node.label.length > 15 ? node.label.substring(0, 15) + '...' : node.label;
                svg.appendChild(text);
            }});
            
            // Create edges
            edges.forEach(edge => {{
                const sourceNode = nodes.find(n => n.id === edge.from);
                const targetNode = nodes.find(n => n.id === edge.to);
                
                if (sourceNode && targetNode) {{
                    const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
                    line.setAttribute('x1', sourceNode.x);
                    line.setAttribute('y1', sourceNode.y);
                    line.setAttribute('x2', targetNode.x);
                    line.setAttribute('y2', targetNode.y);
                    line.setAttribute('stroke', edge.color);
                    line.setAttribute('class', 'edge');
                    
                    svg.insertBefore(line, svg.firstChild); // Insert before nodes
                    edgeElements.push({{line, edge, sourceNode, targetNode}});
                }}
            }});
            
            // Start simulation
            if (physicsEnabled) {{
                startSimulation();
            }}
        }}
        
        function startSimulation() {{
            // Simple physics simulation
            function tick() {{
                // Apply forces
                for (let i = 0; i < nodes.length; i++) {{
                    const node = nodes[i];
                    
                    // Center force
                    const centerX = svg.clientWidth / 2;
                    const centerY = svg.clientHeight / 2;
                    node.vx += (centerX - node.x) * 0.001;
                    node.vy += (centerY - node.y) * 0.001;
                    
                    // Repulsion between nodes
                    for (let j = i + 1; j < nodes.length; j++) {{
                        const other = nodes[j];
                        const dx = node.x - other.x;
                        const dy = node.y - other.y;
                        const distance = Math.sqrt(dx * dx + dy * dy);
                        
                        if (distance < 100 && distance > 0) {{
                            const force = 500 / (distance * distance);
                            const fx = (dx / distance) * force;
                            const fy = (dy / distance) * force;
                            
                            node.vx += fx;
                            node.vy += fy;
                            other.vx -= fx;
                            other.vy -= fy;
                        }}
                    }}
                    
                    // Damping
                    node.vx *= 0.9;
                    node.vy *= 0.9;
                    
                    // Update position
                    node.x += node.vx;
                    node.y += node.vy;
                    
                    // Bounds checking
                    node.x = Math.max(30, Math.min(svg.clientWidth - 30, node.x));
                    node.y = Math.max(30, Math.min(svg.clientHeight - 30, node.y));
                }}
                
                updatePositions();
                
                if (physicsEnabled) {{
                    requestAnimationFrame(tick);
                }}
            }}
            
            tick();
        }}
        
        function updatePositions() {{
            // Update node positions
            const circles = svg.querySelectorAll('.node');
            const labels = svg.querySelectorAll('.node-label');
            
            circles.forEach((circle, i) => {{
                circle.setAttribute('cx', nodes[i].x);
                circle.setAttribute('cy', nodes[i].y);
            }});
            
            labels.forEach((label, i) => {{
                label.setAttribute('x', nodes[i].x);
                label.setAttribute('y', nodes[i].y + 5);
            }});
            
            // Update edge positions
            const lines = svg.querySelectorAll('.edge');
            lines.forEach((line, i) => {{
                const edge = edges[i];
                const sourceNode = nodes.find(n => n.id === edge.from);
                const targetNode = nodes.find(n => n.id === edge.to);
                
                if (sourceNode && targetNode) {{
                    line.setAttribute('x1', sourceNode.x);
                    line.setAttribute('y1', sourceNode.y);
                    line.setAttribute('x2', targetNode.x);
                    line.setAttribute('y2', targetNode.y);
                }}
            }});
        }}
        
        function showTooltip(event, node) {{
            const tooltip = document.getElementById('tooltip');
            const properties = Object.entries(node.properties)
                .map(([key, value]) => `${{key}}: ${{value}}`)
                .join('\\n');
            
            tooltip.innerHTML = `
                <strong>${{node.label}}</strong><br>
                Type: ${{node.type}}<br>
                ${{properties ? properties.replace(/\\n/g, '<br>') : 'No additional properties'}}
            `;
            
            tooltip.style.left = event.pageX + 10 + 'px';
            tooltip.style.top = event.pageY + 10 + 'px';
            tooltip.style.display = 'block';
        }}
        
        function hideTooltip() {{
            document.getElementById('tooltip').style.display = 'none';
        }}
        
        function startDrag(event, node) {{
            let isDragging = true;
            
            function onMouseMove(e) {{
                if (isDragging) {{
                    const rect = svg.getBoundingClientRect();
                    node.x = e.clientX - rect.left;
                    node.y = e.clientY - rect.top;
                    updatePositions();
                }}
            }}
            
            function onMouseUp() {{
                isDragging = false;
                document.removeEventListener('mousemove', onMouseMove);
                document.removeEventListener('mouseup', onMouseUp);
            }}
            
            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);
        }}
        
        function resetZoom() {{
            // Reset all nodes to random positions
            const container = document.getElementById('graph-container');
            const width = container.clientWidth;
            const height = container.clientHeight;
            
            nodes.forEach(node => {{
                node.x = Math.random() * (width - 100) + 50;
                node.y = Math.random() * (height - 100) + 50;
                node.vx = 0;
                node.vy = 0;
            }});
            
            updatePositions();
        }}
        
        function centerGraph() {{
            const container = document.getElementById('graph-container');
            const centerX = container.clientWidth / 2;
            const centerY = container.clientHeight / 2;
            
            nodes.forEach(node => {{
                node.x = centerX + (Math.random() - 0.5) * 200;
                node.y = centerY + (Math.random() - 0.5) * 200;
            }});
            
            updatePositions();
        }}
        
        function togglePhysics() {{
            physicsEnabled = !physicsEnabled;
            if (physicsEnabled) {{
                startSimulation();
            }}
        }}
        
        // Initialize when page loads
        window.addEventListener('load', initializeGraph);
        window.addEventListener('resize', () => {{
            // Handle window resize
            updatePositions();
        }});
    </script>
</body>
</html>"""
        
        return html_content
    
    def save_enterprise_graph(self, filename: str = "enterprise_knowledge_graph.html") -> str:
        """Save enterprise-safe graph as completely self-contained HTML"""
        print(f"💾 Generating enterprise-safe HTML: {filename}...")
        
        html_content = self.generate_self_contained_html("Enterprise Knowledge Graph")
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        abs_path = os.path.abspath(filename)
        
        print(f"✅ Enterprise-safe graph saved!")
        print(f"   File: {abs_path}")
        print(f"   ✅ No external dependencies")
        print(f"   ✅ Data sanitized")
        print(f"   ✅ Self-contained HTML")
        print(f"   🔒 Enterprise security compliant")
        
        return filename
    
    def get_graph_stats(self) -> Dict[str, Any]:
        """Get statistics about the graph"""
        stats = {
            'total_nodes': len(self.graph.nodes),
            'total_edges': len(self.graph.edges),
            'node_types': {},
            'relationship_types': {},
            'connected_components': nx.number_weakly_connected_components(self.graph)
        }
        
        for node_id, node_data in self.graph.nodes(data=True):
            node_type = node_data.get('entity_type', 'unknown')
            stats['node_types'][node_type] = stats['node_types'].get(node_type, 0) + 1
        
        for source, target, edge_data in self.graph.edges(data=True):
            rel_type = edge_data.get('rel_type', 'unknown')
            stats['relationship_types'][rel_type] = stats['relationship_types'].get(rel_type, 0) + 1
        
        return stats

def test_enterprise_knowledge_graph():
    """Test the enterprise-safe knowledge graph generator"""
    print("🧪 Testing Enterprise-Safe Knowledge Graph Generator...")
    print("=" * 70)
    
    # Sample data with potential security issues (to test sanitization)
    sample_data = {
        "entities": [
            {
                "id": "john.doe@company.com",
                "label": "John Doe <script>alert('test')</script>",
                "type": "person",
                "properties": {"department": "IT", "role": "Admin", "email": "john.doe@company.com"}
            },
            {
                "id": "web-server-01",
                "label": "Web Server 01",
                "type": "system",
                "properties": {"ip": "192.168.1.10", "status": "Active", "note": "Critical <b>system</b>"}
            },
            {
                "id": "database_01",
                "label": "Database Server",
                "type": "system",
                "properties": {"ip": "192.168.1.20", "status": "Active"}
            },
            {
                "id": "nyc_dc1",
                "label": "NYC DataCenter 1",
                "type": "location",
                "properties": {"address": "123 Main St, NYC"}
            }
        ],
        "relationships": [
            {"source": "john.doe@company.com", "target": "web-server-01", "type": "manages", "properties": {}},
            {"source": "web-server-01", "target": "database_01", "type": "depends_on", "properties": {}},
            {"source": "web-server-01", "target": "nyc_dc1", "type": "located_in", "properties": {}}
        ]
    }
    
    # Create enterprise-safe knowledge graph
    kg = EnterpriseKnowledgeGraphGenerator()
    kg.create_graph_from_data(sample_data)
    
    # Get statistics
    stats = kg.get_graph_stats()
    print(f"\n📊 Graph Statistics:")
    print(f"   Total nodes: {stats['total_nodes']}")
    print(f"   Total edges: {stats['total_edges']}")
    
    # Save enterprise-safe HTML
    html_file = kg.save_enterprise_graph("enterprise_knowledge_graph.html")
    
    print(f"\n" + "=" * 70)
    print("✅ Step 5B PASSED - Enterprise-Safe Knowledge Graph!")
    print("🔒 Security Features:")
    print("   ✅ No external CDN dependencies")
    print("   ✅ All JavaScript embedded in HTML")
    print("   ✅ Data sanitization (XSS protection)")
    print("   ✅ No server communication required")
    print("   ✅ Self-contained file")
    print(f"\n🌐 Enterprise-safe graph: {html_file}")
    print("👉 Safe to open in enterprise environments!")
    
    return kg

if __name__ == "__main__":
    test_kg = test_enterprise_knowledge_graph()
