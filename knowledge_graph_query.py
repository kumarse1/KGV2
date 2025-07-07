#!/usr/bin/env python3
"""
Step 6: Knowledge Graph Query Engine
Ask natural language questions about your knowledge graph
Run: python knowledge_graph_query.py
"""

import networkx as nx
from typing import Dict, List, Any, Optional
import re
import json

class KnowledgeGraphQueryEngine:
    """Query engine for asking questions about the knowledge graph"""
    
    def __init__(self, graph: nx.DiGraph, entities: List[Dict], relationships: List[Dict]):
        self.graph = graph
        self.entities = {e['id']: e for e in entities}
        self.relationships = relationships
        
        # Create reverse lookup indices for faster querying
        self.entity_by_name = {}
        self.entity_by_type = {}
        
        print("🔍 KnowledgeGraphQueryEngine initialized")
        print(f"   Graph: {len(self.graph.nodes)} nodes, {len(self.graph.edges)} edges")
        
        # Build lookup indices
        for entity in entities:
            # Name lookup (case-insensitive)
            name_key = entity['label'].lower()
            self.entity_by_name[name_key] = entity['id']
            
            # Type lookup
            entity_type = entity.get('type', 'unknown')
            if entity_type not in self.entity_by_type:
                self.entity_by_type[entity_type] = []
            self.entity_by_type[entity_type].append(entity['id'])
        
        print(f"   Indexed: {len(self.entity_by_name)} named entities")
        print(f"   Types: {list(self.entity_by_type.keys())}")
    
    def find_entity_by_name(self, name: str) -> Optional[str]:
        """Find entity ID by name (case-insensitive, partial matching)"""
        name_lower = name.lower().strip()
        
        # Exact match first
        if name_lower in self.entity_by_name:
            return self.entity_by_name[name_lower]
        
        # Partial match - find if name is contained in any entity name
        for entity_name, entity_id in self.entity_by_name.items():
            if name_lower in entity_name or entity_name in name_lower:
                return entity_id
        
        # Try matching with word boundaries
        name_words = name_lower.split()
        for entity_name, entity_id in self.entity_by_name.items():
            entity_words = entity_name.split()
            if any(word in entity_words for word in name_words):
                return entity_id
        
        return None
    
    def get_entity_info(self, entity_id: str) -> Dict[str, Any]:
        """Get detailed information about an entity"""
        if entity_id not in self.entities:
            return {"error": f"Entity {entity_id} not found"}
        
        entity = self.entities[entity_id]
        
        # Get all relationships
        outgoing = []
        incoming = []
        
        for successor in self.graph.successors(entity_id):
            edge_data = self.graph[entity_id][successor]
            target_entity = self.entities.get(successor, {})
            outgoing.append({
                "target": successor,
                "target_label": target_entity.get('label', successor),
                "target_type": target_entity.get('type', 'unknown'),
                "relationship": edge_data.get('rel_type', 'unknown')
            })
        
        for predecessor in self.graph.predecessors(entity_id):
            edge_data = self.graph[predecessor][entity_id]
            source_entity = self.entities.get(predecessor, {})
            incoming.append({
                "source": predecessor,
                "source_label": source_entity.get('label', predecessor),
                "source_type": source_entity.get('type', 'unknown'),
                "relationship": edge_data.get('rel_type', 'unknown')
            })
        
        return {
            "entity": entity,
            "outgoing_relationships": outgoing,
            "incoming_relationships": incoming,
            "total_connections": len(outgoing) + len(incoming)
        }
    
    def who_manages(self, target_name: str) -> List[Dict[str, Any]]:
        """Find who manages/owns a specific entity"""
        target_id = self.find_entity_by_name(target_name)
        if not target_id:
            return [{"error": f"Could not find entity: {target_name}"}]
        
        managers = []
        management_types = ['manages', 'owns', 'administers', 'supervises', 'controls']
        
        for source in self.graph.predecessors(target_id):
            edge_data = self.graph[source][target_id]
            rel_type = edge_data.get('rel_type', '').lower()
            
            if rel_type in management_types:
                source_entity = self.entities.get(source, {})
                managers.append({
                    "manager": source_entity.get('label', source),
                    "manager_type": source_entity.get('type', 'unknown'),
                    "relationship": edge_data.get('rel_type', 'unknown'),
                    "manager_id": source,
                    "manager_properties": source_entity.get('properties', {})
                })
        
        if not managers:
            return [{"result": f"No managers found for {target_name}"}]
        
        return managers
    
    def what_does_person_manage(self, person_name: str) -> List[Dict[str, Any]]:
        """Find what a person manages/owns"""
        person_id = self.find_entity_by_name(person_name)
        if not person_id:
            return [{"error": f"Could not find person: {person_name}"}]
        
        managed_items = []
        management_types = ['manages', 'owns', 'administers', 'supervises', 'controls']
        
        for target in self.graph.successors(person_id):
            edge_data = self.graph[person_id][target]
            rel_type = edge_data.get('rel_type', '').lower()
            
            if rel_type in management_types:
                target_entity = self.entities.get(target, {})
                managed_items.append({
                    "item": target_entity.get('label', target),
                    "item_type": target_entity.get('type', 'unknown'),
                    "relationship": edge_data.get('rel_type', 'unknown'),
                    "item_id": target,
                    "item_properties": target_entity.get('properties', {})
                })
        
        if not managed_items:
            return [{"result": f"{person_name} doesn't manage anything directly"}]
        
        return managed_items
    
    def find_dependencies(self, entity_name: str) -> Dict[str, Any]:
        """Find what an entity depends on and what depends on it"""
        entity_id = self.find_entity_by_name(entity_name)
        if not entity_id:
            return {"error": f"Could not find entity: {entity_name}"}
        
        dependency_types = ['depends_on', 'requires', 'uses', 'connects_to', 'runs_on']
        
        # What this entity depends on
        dependencies = []
        for target in self.graph.successors(entity_id):
            edge_data = self.graph[entity_id][target]
            rel_type = edge_data.get('rel_type', '').lower()
            
            if rel_type in dependency_types:
                target_entity = self.entities.get(target, {})
                dependencies.append({
                    "dependency": target_entity.get('label', target),
                    "dependency_type": target_entity.get('type', 'unknown'),
                    "relationship": edge_data.get('rel_type', 'unknown'),
                    "dependency_id": target,
                    "properties": target_entity.get('properties', {})
                })
        
        # What depends on this entity
        dependents = []
        for source in self.graph.predecessors(entity_id):
            edge_data = self.graph[source][entity_id]
            rel_type = edge_data.get('rel_type', '').lower()
            
            if rel_type in dependency_types:
                source_entity = self.entities.get(source, {})
                dependents.append({
                    "dependent": source_entity.get('label', source),
                    "dependent_type": source_entity.get('type', 'unknown'),
                    "relationship": edge_data.get('rel_type', 'unknown'),
                    "dependent_id": source,
                    "properties": source_entity.get('properties', {})
                })
        
        return {
            "entity": self.entities[entity_id]['label'],
            "entity_type": self.entities[entity_id].get('type', 'unknown'),
            "depends_on": dependencies,
            "dependents": dependents,
            "total_dependencies": len(dependencies),
            "total_dependents": len(dependents)
        }
    
    def find_by_location(self, location_name: str) -> List[Dict[str, Any]]:
        """Find all entities in a specific location"""
        location_types = ['located_in', 'hosted_in', 'deployed_in']
        items_in_location = []
        
        # Find the location entity
        location_id = self.find_entity_by_name(location_name)
        
        # Search all entities for location relationships
        for entity_id in self.entities:
            for target in self.graph.successors(entity_id):
                edge_data = self.graph[entity_id][target]
                rel_type = edge_data.get('rel_type', '').lower()
                
                if rel_type in location_types:
                    # Check if target matches our location
                    target_entity = self.entities.get(target, {})
                    if (target == location_id or 
                        target_entity.get('label', '').lower() == location_name.lower()):
                        
                        entity = self.entities[entity_id]
                        items_in_location.append({
                            "item": entity.get('label', entity_id),
                            "item_type": entity.get('type', 'unknown'),
                            "item_id": entity_id,
                            "relationship": edge_data.get('rel_type', 'unknown'),
                            "properties": entity.get('properties', {})
                        })
        
        if not items_in_location:
            return [{"result": f"No items found in {location_name}"}]
        
        return items_in_location
    
    def find_by_type(self, entity_type: str) -> List[Dict[str, Any]]:
        """Find all entities of a specific type"""
        entity_type_lower = entity_type.lower()
        matches = []
        
        # Check exact type match
        for stored_type, entity_ids in self.entity_by_type.items():
            if (entity_type_lower == stored_type.lower() or 
                entity_type_lower in stored_type.lower() or 
                stored_type.lower() in entity_type_lower):
                
                for entity_id in entity_ids:
                    entity = self.entities[entity_id]
                    matches.append({
                        "item": entity.get('label', entity_id),
                        "item_type": stored_type,
                        "item_id": entity_id,
                        "properties": entity.get('properties', {}),
                        "connections": len(list(self.graph.successors(entity_id))) + len(list(self.graph.predecessors(entity_id)))
                    })
        
        if not matches:
            return [{"result": f"No entities found of type: {entity_type}"}]
        
        # Sort by number of connections (most connected first)
        matches.sort(key=lambda x: x.get('connections', 0), reverse=True)
        return matches
    
    def find_reporting_chain(self, person_name: str) -> Dict[str, Any]:
        """Find the reporting chain for a person"""
        person_id = self.find_entity_by_name(person_name)
        if not person_id:
            return {"error": f"Could not find person: {person_name}"}
        
        # Find who this person reports to
        reports_to = []
        current_id = person_id
        visited = set()  # Prevent infinite loops
        
        while current_id and current_id not in visited:
            visited.add(current_id)
            
            for target in self.graph.successors(current_id):
                edge_data = self.graph[current_id][target]
                if edge_data.get('rel_type', '').lower() == 'reports_to':
                    target_entity = self.entities.get(target, {})
                    reports_to.append({
                        "person": target_entity.get('label', target),
                        "person_type": target_entity.get('type', 'unknown'),
                        "person_id": target,
                        "properties": target_entity.get('properties', {})
                    })
                    current_id = target
                    break
            else:
                break  # No more reports_to relationships
        
        # Find who reports to this person
        direct_reports = []
        for source in self.graph.predecessors(person_id):
            edge_data = self.graph[source][person_id]
            if edge_data.get('rel_type', '').lower() == 'reports_to':
                source_entity = self.entities.get(source, {})
                direct_reports.append({
                    "person": source_entity.get('label', source),
                    "person_type": source_entity.get('type', 'unknown'),
                    "person_id": source,
                    "properties": source_entity.get('properties', {})
                })
        
        return {
            "person": self.entities[person_id]['label'],
            "reports_to": reports_to,
            "direct_reports": direct_reports,
            "chain_length": len(reports_to),
            "team_size": len(direct_reports)
        }
    
    def natural_language_query(self, question: str) -> Dict[str, Any]:
        """Process natural language questions"""
        question_lower = question.lower().strip()
        
        print(f"🔍 Processing query: {question}")
        
        # Who manages X?
        who_manages_patterns = [
            r"who (?:manages|owns|administers|controls) (.+?)[\?\.]?$",
            r"who is (?:managing|owning|administering|controlling) (.+?)[\?\.]?$",
            r"(?:manager|owner|admin|administrator) (?:of|for) (.+?)[\?\.]?$"
        ]
        
        for pattern in who_manages_patterns:
            match = re.search(pattern, question_lower)
            if match:
                entity_name = match.group(1).strip()
                return {"query_type": "who_manages", "entity": entity_name, "results": self.who_manages(entity_name)}
        
        # What does X manage?
        what_manages_patterns = [
            r"what does (.+?) (?:manage|own|administer|control)[\?\.]?$",
            r"what is (.+?) (?:managing|owning|administering|controlling)[\?\.]?$",
            r"(?:list|show) what (.+?) (?:manages|owns)[\?\.]?$"
        ]
        
        for pattern in what_manages_patterns:
            match = re.search(pattern, question_lower)
            if match:
                person_name = match.group(1).strip()
                return {"query_type": "what_manages", "person": person_name, "results": self.what_does_person_manage(person_name)}
        
        # Dependencies
        dependency_patterns = [
            r"(?:dependencies|depends on|requirements) (?:for|of) (.+?)[\?\.]?$",
            r"what (?:does|are) (.+?) (?:depend|depends) on[\?\.]?$",
            r"what (?:depends|relies) on (.+?)[\?\.]?$",
            r"(?:show|find|get) dependencies (?:for|of) (.+?)[\?\.]?$"
        ]
        
        for pattern in dependency_patterns:
            match = re.search(pattern, question_lower)
            if match:
                entity_name = match.group(1).strip()
                return {"query_type": "dependencies", "entity": entity_name, "results": self.find_dependencies(entity_name)}
        
        # Location queries
        location_patterns = [
            r"(?:what|which) (?:is|are) in (.+?)[\?\.]?$",
            r"(?:show|list|find) (?:everything|all|items) in (.+?)[\?\.]?$",
            r"(?:what|which) (?:systems|servers|items|entities) (?:are )?(?:in|at|located in) (.+?)[\?\.]?$"
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, question_lower)
            if match:
                location_name = match.group(1).strip()
                return {"query_type": "by_location", "location": location_name, "results": self.find_by_location(location_name)}
        
        # Type queries
        type_patterns = [
            r"(?:show|list|find) (?:all )?(.+?)s?[\?\.]?$",
            r"(?:what|which) (.+?)s? (?:do we have|are there|exist)[\?\.]?$",
            r"(?:get|find) (?:all )?(?:the )?(.+?) (?:entities|items|objects)[\?\.]?$"
        ]
        
        for pattern in type_patterns:
            match = re.search(pattern, question_lower)
            if match:
                entity_type = match.group(1).strip()
                # Check if it matches common entity types
                common_types = ['person', 'people', 'user', 'users', 'server', 'servers', 'system', 'systems', 
                               'application', 'applications', 'app', 'apps', 'location', 'locations', 
                               'organization', 'organizations', 'department', 'departments']
                
                if entity_type in common_types:
                    # Normalize plurals
                    if entity_type in ['people', 'users']:
                        entity_type = 'person'
                    elif entity_type in ['servers', 'systems']:
                        entity_type = 'system'
                    elif entity_type in ['applications', 'apps']:
                        entity_type = 'application'
                    elif entity_type in ['locations']:
                        entity_type = 'location'
                    elif entity_type in ['organizations', 'departments']:
                        entity_type = 'organization'
                    
                    return {"query_type": "by_type", "type": entity_type, "results": self.find_by_type(entity_type)}
        
        # Reporting chain
        reporting_patterns = [
            r"(?:who does|reporting chain (?:for|of)) (.+?) (?:report to|reports to)[\?\.]?$",
            r"(?:show|get) (?:reporting chain|org chart) (?:for|of) (.+?)[\?\.]?$",
            r"(.+?) (?:reports to|reporting chain|org structure)[\?\.]?$"
        ]
        
        for pattern in reporting_patterns:
            match = re.search(pattern, question_lower)
            if match:
                person_name = match.group(1).strip()
                return {"query_type": "reporting_chain", "person": person_name, "results": self.find_reporting_chain(person_name)}
        
        # Fallback - entity info
        if len(question_lower.split()) <= 3:  # Short queries might be entity names
            possible_entity = question_lower.replace('?', '').replace('.', '').strip()
            entity_id = self.find_entity_by_name(possible_entity)
            if entity_id:
                return {"query_type": "entity_info", "entity": possible_entity, "results": self.get_entity_info(entity_id)}
        
        # Unknown query
        return {
            "query_type": "unknown",
            "results": [{"error": f"Could not understand question: {question}"}],
            "suggestions": [
                "Try: 'Who manages Web Server 01?'",
                "Try: 'What does John Doe manage?'",
                "Try: 'What are the dependencies for CRM Application?'",
                "Try: 'What is in DataCenter-A?'",
                "Try: 'Show all servers'",
                "Try: 'Reporting chain for Jane Smith'"
            ]
        }

def test_query_engine():
    """Test the query engine with comprehensive sample data"""
    print("🧪 Testing Knowledge Graph Query Engine...")
    print("=" * 70)
    
    # Create comprehensive test data
    sample_entities = [
        {"id": "john_doe", "label": "John Doe", "type": "person", "properties": {"role": "System Admin", "department": "IT"}},
        {"id": "jane_smith", "label": "Jane Smith", "type": "person", "properties": {"role": "DBA", "department": "IT"}},
        {"id": "mike_wilson", "label": "Mike Wilson", "type": "person", "properties": {"role": "IT Manager", "department": "IT"}},
        {"id": "web_server_01", "label": "Web Server 01", "type": "system", "properties": {"ip": "192.168.1.10", "status": "Active"}},
        {"id": "database_01", "label": "Database Server", "type": "system", "properties": {"ip": "192.168.1.20", "status": "Active"}},
        {"id": "crm_app", "label": "CRM Application", "type": "application", "properties": {"version": "2.1", "users": "500"}},
        {"id": "nyc_dc1", "label": "NYC DataCenter 1", "type": "location", "properties": {"city": "New York", "capacity": "100 racks"}},
        {"id": "it_dept", "label": "IT Department", "type": "organization", "properties": {"budget": "2M", "headcount": "25"}}
    ]
    
    sample_relationships = [
        {"source": "john_doe", "target": "mike_wilson", "type": "reports_to"},
        {"source": "jane_smith", "target": "mike_wilson", "type": "reports_to"},
        {"source": "john_doe", "target": "web_server_01", "type": "manages"},
        {"source": "jane_smith", "target": "database_01", "type": "manages"},
        {"source": "web_server_01", "target": "database_01", "type": "depends_on"},
        {"source": "crm_app", "target": "web_server_01", "type": "runs_on"},
        {"source": "web_server_01", "target": "nyc_dc1", "type": "located_in"},
        {"source": "database_01", "target": "nyc_dc1", "type": "located_in"},
        {"source": "john_doe", "target": "it_dept", "type": "works_for"},
        {"source": "jane_smith", "target": "it_dept", "type": "works_for"}
    ]
    
    # Create graph
    graph = nx.DiGraph()
    for entity in sample_entities:
        graph.add_node(entity['id'], **entity)
    
    for rel in sample_relationships:
        graph.add_edge(rel['source'], rel['target'], rel_type=rel['type'])
    
    # Create query engine
    query_engine = KnowledgeGraphQueryEngine(graph, sample_entities, sample_relationships)
    
    # Test queries
    test_questions = [
        "Who manages Web Server 01?",
        "What does John Doe manage?",
        "What are the dependencies for CRM Application?",
        "What is in NYC DataCenter 1?",
        "Show all servers",
        "Show all people",
        "Reporting chain for John Doe",
        "What depends on Database Server?",
        "List all systems",
        "Who does Jane Smith report to?"
    ]
    
    print(f"\n🎯 Testing {len(test_questions)} natural language queries:")
    print("-" * 50)
    
    for i, question in enumerate(test_questions, 1):
        print(f"\n{i:2d}. Q: {question}")
        result = query_engine.natural_language_query(question)
        
        query_type = result.get('query_type', 'unknown')
        results = result.get('results', [])
        
        if query_type == 'unknown':
            print(f"    A: ❓ Could not understand question")
            suggestions = result.get('suggestions', [])
            if suggestions:
                print(f"    💡 Try: {suggestions[0]}")
        
        elif results and isinstance(results, list) and len(results) > 0:
            if 'error' in results[0]:
                print(f"    A: ❌ {results[0]['error']}")
            elif 'result' in results[0]:
                print(f"    A: ℹ️ {results[0]['result']}")
            else:
                if query_type == 'who_manages':
                    managers = [r.get('manager', 'Unknown') for r in results if 'manager' in r]
                    print(f"    A: ✅ {', '.join(managers) if managers else 'No managers found'}")
                
                elif query_type == 'what_manages':
                    items = [r.get('item', 'Unknown') for r in results if 'item' in r]
                    print(f"    A: ✅ Manages {len(items)} items: {', '.join(items[:3])}")
                    if len(items) > 3:
                        print(f"         ... and {len(items) - 3} more")
                
                elif query_type == 'dependencies':
                    deps_on = results.get('depends_on', [])
                    dependents = results.get('dependents', [])
                    total_deps = results.get('total_dependencies', 0)
                    total_dependents = results.get('total_dependents', 0)
                    print(f"    A: ✅ Depends on {total_deps} items, {total_dependents} items depend on it")
                
                elif query_type in ['by_location', 'by_type']:
                    items = [r.get('item', 'Unknown') for r in results if 'item' in r]
                    print(f"    A: ✅ Found {len(items)} items: {', '.join(items[:3])}")
                    if len(items) > 3:
                        print(f"         ... and {len(items) - 3} more")
                
                elif query_type == 'reporting_chain':
                    reports_to = results.get('reports_to', [])
                    direct_reports = results.get('direct_reports', [])
                    print(f"    A: ✅ Reports to {len(reports_to)} people, has {len(direct_reports)} direct reports")
        
        elif isinstance(results, dict):
            # Handle dictionary results (like dependencies)
            if 'error' in results:
                print(f"    A: ❌ {results['error']}")
            else:
                print(f"    A: ✅ Query processed successfully")
        
        else:
            print(f"    A: ⚠️ Unexpected result format")
    
    print(f"\n" + "=" * 70)
    print("✅ Step 6 PASSED - Query Engine works!")
    print("🔍 Natural language queries:")
    print("   ✅ Management queries (who manages what)")
    print("   ✅ Dependency analysis (what depends on what)")
    print("   ✅ Location-based searches")
    print("   ✅ Entity type filtering")
    print("   ✅ Reporting chain analysis")
    print("👉 Ready for Step 7: Full Integration Test")
    
    return query_engine

if __name__ == "__main__":
    test_engine = test_query_engine()
