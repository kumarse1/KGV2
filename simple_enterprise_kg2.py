import streamlit as st
import pandas as pd
import networkx as nx
import json
from collections import defaultdict
import requests
import re

st.set_page_config(page_title="🔗 Knowledge Graph System", layout="wide")

# ========================================
# 🔧 LLM CONFIGURATION
# ========================================
LLM_API_URL = "https://api.openai.com/v1/chat/completions"
LLM_API_KEY = "your_api_key_here"  # Replace with your actual API key

class EnhancedKnowledgeGraph:
    """Enhanced knowledge graph with detailed entity extraction and relationships"""
    
    def __init__(self):
        self.entities = {}
        self.relationships = []
        self.entity_types = {
            'Application': '🔵',
            'Database': '🟢', 
            'Server': '🟡',
            'Service': '🟣',
            'Component': '🔴',
            'Security Function': '🟠',
            'Business Service': '🟤',
            'Environment': '⚫',
            'Data': '🔶',
            'Queue': '🔷',
            'Software': '🟦',
            'Flow': '⭕',
            'Person': '👤',
            'Location': '📍'
        }
        self.df = None
        self.use_llm = LLM_API_KEY != "your_api_key_here"
    
    def process_data(self, df):
        """Process data with enhanced entity extraction"""
        self.df = df
        
        # First pass: Create basic entities
        for idx, row in df.iterrows():
            if idx >= 50:  # Reasonable limit
                break
            
            # Extract main entity
            entity_name = self._get_entity_name(row)
            entity_type = self._get_enhanced_entity_type(row)
            
            self.entities[entity_name] = {
                'name': entity_name,
                'type': entity_type,
                'properties': self._extract_detailed_properties(row),
                'row_index': idx,
                'description': self._generate_description(row)
            }
        
        # Second pass: Create relationships with LLM enhancement
        for idx, row in df.iterrows():
            if idx >= 50:
                break
            
            entity_name = self._get_entity_name(row)
            
            # Create basic relationships
            self._create_basic_relationships(entity_name, row)
            
            # Enhance with LLM if available
            if self.use_llm:
                self._enhance_relationships_with_llm(entity_name, row)
    
    def _get_entity_name(self, row):
        """Extract entity name with priority for meaningful names"""
        # Priority columns for names
        priority_columns = ['name', 'title', 'system', 'application', 'component', 'service']
        
        for priority in priority_columns:
            matching_cols = [col for col in self.df.columns if priority in col.lower()]
            for col in matching_cols:
                if pd.notna(row[col]) and str(row[col]).strip():
                    return str(row[col]).strip()
        
        # Fallback to first meaningful column
        for col in self.df.columns:
            if pd.notna(row[col]) and str(row[col]).strip():
                value = str(row[col]).strip()
                if len(value) > 2 and not value.isdigit():
                    return value
        
        return f"Entity_{row.name}"
    
    def _get_enhanced_entity_type(self, row):
        """Enhanced entity type detection"""
        row_text = ' '.join([str(val) for val in row.values if pd.notna(val)]).lower()
        
        # Detailed type matching based on your image
        type_patterns = {
            'Application': ['application', 'app', 'system', 'portal', 'platform'],
            'Database': ['database', 'db', 'sql', 'oracle', 'mysql', 'postgres', 'data store'],
            'Server': ['server', 'host', 'machine', 'vm', 'instance'],
            'Service': ['service', 'api', 'endpoint', 'interface'],
            'Component': ['component', 'module', 'library', 'framework'],
            'Security Function': ['security', 'auth', 'firewall', 'encryption', 'ssl'],
            'Business Service': ['business', 'process', 'workflow', 'function'],
            'Environment': ['environment', 'env', 'staging', 'production', 'dev'],
            'Data': ['data', 'dataset', 'file', 'document', 'record'],
            'Queue': ['queue', 'message', 'topic', 'stream', 'event'],
            'Software': ['software', 'tool', 'utility', 'program'],
            'Flow': ['flow', 'pipeline', 'process flow', 'workflow'],
            'Person': ['person', 'user', 'admin', 'manager', 'owner', 'analyst'],
            'Location': ['location', 'datacenter', 'site', 'office', 'region']
        }
        
        for entity_type, patterns in type_patterns.items():
            if any(pattern in row_text for pattern in patterns):
                return entity_type
        
        return 'Component'  # Default
    
    def _extract_detailed_properties(self, row):
        """Extract detailed properties for entities"""
        properties = {}
        
        for col in self.df.columns:
            if pd.notna(row[col]):
                key = col.strip()
                value = str(row[col]).strip()
                
                # Categorize properties
                if any(word in key.lower() for word in ['tech', 'technology', 'stack']):
                    properties['technology'] = value
                elif any(word in key.lower() for word in ['owner', 'manager', 'responsible']):
                    properties['owner'] = value
                elif any(word in key.lower() for word in ['location', 'site', 'datacenter']):
                    properties['location'] = value
                elif any(word in key.lower() for word in ['env', 'environment']):
                    properties['environment'] = value
                elif any(word in key.lower() for word in ['critical', 'importance', 'priority']):
                    properties['criticality'] = value
                elif any(word in key.lower() for word in ['status', 'state']):
                    properties['status'] = value
                else:
                    properties[key.lower().replace(' ', '_')] = value
        
        return properties
    
    def _generate_description(self, row):
        """Generate entity description"""
        properties = self._extract_detailed_properties(row)
        
        desc_parts = []
        if 'technology' in properties:
            desc_parts.append(f"Uses: {properties['technology']}")
        if 'owner' in properties:
            desc_parts.append(f"Managed by: {properties['owner']}")
        if 'location' in properties:
            desc_parts.append(f"Located in: {properties['location']}")
        
        return " | ".join(desc_parts) if desc_parts else "System component"
    
    def _create_basic_relationships(self, entity_name, row):
        """Create basic relationships from data"""
        properties = self._extract_detailed_properties(row)
        
        # Management relationships
        if 'owner' in properties:
            owner = properties['owner']
            if owner not in self.entities:
                self.entities[owner] = {
                    'name': owner,
                    'type': 'Person',
                    'properties': {'role': 'Manager/Owner'},
                    'description': f"Manages {entity_name}"
                }
            
            self.relationships.append({
                'source': owner,
                'target': entity_name,
                'type': 'MANAGES',
                'description': f"{owner} manages {entity_name}",
                'strength': 'strong'
            })
        
        # Location relationships
        if 'location' in properties:
            location = properties['location']
            if location not in self.entities:
                self.entities[location] = {
                    'name': location,
                    'type': 'Location',
                    'properties': {'type': 'Physical Location'},
                    'description': f"Physical location: {location}"
                }
            
            self.relationships.append({
                'source': entity_name,
                'target': location,
                'type': 'LOCATED_IN',
                'description': f"{entity_name} is located in {location}",
                'strength': 'medium'
            })
        
        # Technology relationships
        if 'technology' in properties:
            techs = [tech.strip() for tech in properties['technology'].split(',')]
            for tech in techs:
                if tech and len(tech) > 2:
                    tech_clean = tech.strip()
                    if tech_clean not in self.entities:
                        self.entities[tech_clean] = {
                            'name': tech_clean,
                            'type': 'Software',
                            'properties': {'category': 'Technology'},
                            'description': f"Technology: {tech_clean}"
                        }
                    
                    self.relationships.append({
                        'source': entity_name,
                        'target': tech_clean,
                        'type': 'USES',
                        'description': f"{entity_name} uses {tech_clean}",
                        'strength': 'medium'
                    })
    
    def _enhance_relationships_with_llm(self, entity_name, row):
        """Use LLM to discover additional relationships"""
        if not self.use_llm:
            return
            
        try:
            # Prepare context for LLM
            entity_info = f"Entity: {entity_name}\nType: {self.entities[entity_name]['type']}\n"
            entity_info += f"Properties: {self.entities[entity_name]['properties']}\n"
            
            prompt = f"""
            Based on this entity information, identify potential relationships and components:
            
            {entity_info}
            
            Please identify:
            1. What components this entity might contain (SUB_COMPONENT)
            2. What it might depend on (DEPENDS_ON)
            3. What flows or data it processes (PROCESSES)
            4. What it supports or enables (SUPPORTS)
            
            Return only a JSON list of relationships in this format:
            [
                {{"source": "entity_name", "target": "related_entity", "type": "RELATIONSHIP_TYPE", "description": "brief description"}}
            ]
            
            Focus on technical architecture relationships. Be specific and realistic.
            """
            
            headers = {
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": "You are a technical architect analyzing system relationships. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 500,
                "temperature": 0.3
            }
            
            response = requests.post(LLM_API_URL, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                llm_response = response.json()['choices'][0]['message']['content']
                
                # Extract JSON from response
                json_match = re.search(r'\[.*\]', llm_response, re.DOTALL)
                if json_match:
                    relationships = json.loads(json_match.group())
                    
                    for rel in relationships:
                        # Create target entity if it doesn't exist
                        target_name = rel['target']
                        if target_name not in self.entities:
                            self.entities[target_name] = {
                                'name': target_name,
                                'type': self._infer_type_from_name(target_name),
                                'properties': {'source': 'LLM_generated'},
                                'description': f"Component related to {entity_name}"
                            }
                        
                        # Add relationship
                        self.relationships.append({
                            'source': rel['source'],
                            'target': rel['target'],
                            'type': rel['type'],
                            'description': rel['description'],
                            'strength': 'medium',
                            'source': 'LLM'
                        })
        
        except Exception as e:
            # Silently continue if LLM enhancement fails
            pass
    
    def _infer_type_from_name(self, name):
        """Infer entity type from name"""
        name_lower = name.lower()
        
        if any(word in name_lower for word in ['database', 'db', 'data']):
            return 'Database'
        elif any(word in name_lower for word in ['server', 'host']):
            return 'Server'
        elif any(word in name_lower for word in ['service', 'api']):
            return 'Service'
        elif any(word in name_lower for word in ['security', 'auth']):
            return 'Security Function'
        elif any(word in name_lower for word in ['queue', 'message']):
            return 'Queue'
        elif any(word in name_lower for word in ['flow', 'process']):
            return 'Flow'
        else:
            return 'Component'
    
    def get_strategic_insights(self):
        """Generate strategic insights with LLM enhancement"""
        insights = []
        
        # Network topology analysis
        connections = defaultdict(int)
        for rel in self.relationships:
            connections[rel['source']] += 1
            connections[rel['target']] += 1
        
        # Most connected entities (potential single points of failure)
        if connections:
            top_connected = sorted(connections.items(), key=lambda x: x[1], reverse=True)[:5]
            critical_components = [name for name, count in top_connected if count > 3]
            
            if critical_components:
                insights.append({
                    'title': '🔴 Critical Components (High Connectivity)',
                    'content': f"These components have many connections and could be single points of failure: {', '.join(critical_components[:3])}",
                    'type': 'risk'
                })
        
        # Technology diversity analysis
        tech_entities = [e for e in self.entities.values() if e['type'] == 'Software']
        if tech_entities:
            tech_count = len(tech_entities)
            insights.append({
                'title': '🛠️ Technology Stack Diversity',
                'content': f"Using {tech_count} different technologies. Review for standardization opportunities.",
                'type': 'optimization'
            })
        
        # Management coverage
        managed_entities = set(rel['target'] for rel in self.relationships if rel['type'] == 'MANAGES')
        unmanaged = [name for name in self.entities.keys() if name not in managed_entities and self.entities[name]['type'] not in ['Person', 'Location', 'Software']]
        
        if unmanaged:
            insights.append({
                'title': '⚠️ Management Gaps',
                'content': f"{len(unmanaged)} components lack clear ownership. Consider assigning responsible parties.",
                'type': 'governance'
            })
        
        # LLM-enhanced strategic analysis
        if self.use_llm and len(self.entities) > 0:
            llm_insights = self._get_llm_strategic_insights()
            if llm_insights:
                insights.extend(llm_insights)
        
        return insights
    
    def _get_llm_strategic_insights(self):
        """Get strategic insights from LLM analysis"""
        try:
            # Prepare architecture summary
            entity_summary = {}
            for entity_type in self.entity_types.keys():
                count = len([e for e in self.entities.values() if e['type'] == entity_type])
                if count > 0:
                    entity_summary[entity_type] = count
            
            relationship_summary = {}
            for rel in self.relationships:
                rel_type = rel['type']
                relationship_summary[rel_type] = relationship_summary.get(rel_type, 0) + 1
            
            prompt = f"""
            Analyze this IT architecture and provide strategic insights:
            
            ENTITIES: {entity_summary}
            RELATIONSHIPS: {relationship_summary}
            
            Provide 2-3 strategic insights focusing on:
            1. Architecture risks and recommendations
            2. Optimization opportunities
            3. Governance and compliance considerations
            
            Format as JSON array:
            [
                {{"title": "insight title", "content": "detailed insight", "type": "risk|optimization|governance"}}
            ]
            
            Be specific and actionable.
            """
            
            headers = {
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": "You are a senior IT architect providing strategic insights. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 600,
                "temperature": 0.3
            }
            
            response = requests.post(LLM_API_URL, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                llm_response = response.json()['choices'][0]['message']['content']
                json_match = re.search(r'\[.*\]', llm_response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
        
        except Exception as e:
            pass
        
        return []
    
    def get_network_view(self):
        """Get network view for display"""
        network_data = {
            'entities': [],
            'relationships': []
        }
        
        for entity in self.entities.values():
            network_data['entities'].append({
                'name': entity['name'],
                'type': entity['type'],
                'icon': self.entity_types.get(entity['type'], '🔵'),
                'description': entity['description'],
                'properties': entity['properties']
            })
        
        for rel in self.relationships:
            network_data['relationships'].append({
                'source': rel['source'],
                'target': rel['target'],
                'type': rel['type'],
                'description': rel['description'],
                'strength': rel.get('strength', 'medium')
            })
        
        return network_data

class EnhancedChatEngine:
    """Enhanced chat engine with deep knowledge graph integration"""
    
    def __init__(self, knowledge_graph):
        self.kg = knowledge_graph
        self.use_llm = knowledge_graph.use_llm
    
    def answer_question(self, question):
        """Answer questions with deep analysis"""
        
        # Get structured answer from knowledge graph
        structured_answer = self._analyze_with_kg(question)
        
        # Enhance with LLM for strategic insights
        if self.use_llm and structured_answer:
            try:
                enhanced_answer = self._enhance_with_strategic_llm(question, structured_answer)
                return enhanced_answer
            except:
                return structured_answer
        
        return structured_answer or self._provide_suggestions()
    
    def _analyze_with_kg(self, question):
        """Deep analysis using knowledge graph structure"""
        question_lower = question.lower()
        
        # Architecture analysis
        if any(word in question_lower for word in ['architecture', 'structure', 'design']):
            return self._analyze_architecture()
        
        # Dependency analysis
        elif any(word in question_lower for word in ['depend', 'connect', 'relation']):
            return self._analyze_dependencies()
        
        # Risk analysis
        elif any(word in question_lower for word in ['risk', 'critical', 'failure', 'problem']):
            return self._analyze_risks()
        
        # Technology analysis
        elif any(word in question_lower for word in ['technology', 'tech', 'software', 'stack']):
            return self._analyze_technology_stack()
        
        # Specific entity search
        elif any(word in question_lower for word in ['what is', 'tell me about', 'describe']):
            return self._describe_entity(question)
        
        # Management analysis
        elif any(word in question_lower for word in ['manage', 'owner', 'responsible']):
            return self._analyze_management()
        
        return None
    
    def _analyze_architecture(self):
        """Analyze overall architecture"""
        entity_types = defaultdict(int)
        for entity in self.kg.entities.values():
            entity_types[entity['type']] += 1
        
        result = "🏗️ **Architecture Analysis:**\n\n"
        
        # Entity distribution
        result += "**Component Distribution:**\n"
        for entity_type, count in sorted(entity_types.items(), key=lambda x: x[1], reverse=True):
            icon = self.kg.entity_types.get(entity_type, '🔵')
            result += f"{icon} {entity_type}: {count}\n"
        
        # Relationship patterns
        rel_types = defaultdict(int)
        for rel in self.kg.relationships:
            rel_types[rel['type']] += 1
        
        result += "\n**Relationship Patterns:**\n"
        for rel_type, count in sorted(rel_types.items(), key=lambda x: x[1], reverse=True):
            result += f"• {rel_type}: {count} connections\n"
        
        return result
    
    def _analyze_dependencies(self):
        """Analyze component dependencies"""
        # Build dependency graph
        dependencies = defaultdict(list)
        dependents = defaultdict(list)
        
        for rel in self.kg.relationships:
            if rel['type'] in ['DEPENDS_ON', 'USES', 'CONNECTS_TO']:
                dependencies[rel['source']].append(rel['target'])
                dependents[rel['target']].append(rel['source'])
        
        result = "🔗 **Dependency Analysis:**\n\n"
        
        # Most depended upon
        most_depended = sorted(dependents.items(), key=lambda x: len(x[1]), reverse=True)[:5]
        if most_depended:
            result += "**Most Depended Upon Components:**\n"
            for component, deps in most_depended:
                entity_type = self.kg.entities.get(component, {}).get('type', 'Unknown')
                icon = self.kg.entity_types.get(entity_type, '🔵')
                result += f"{icon} {component}: {len(deps)} dependencies\n"
        
        # Most dependent
        most_dependent = sorted(dependencies.items(), key=lambda x: len(x[1]), reverse=True)[:5]
        if most_dependent:
            result += "\n**Most Dependent Components:**\n"
            for component, deps in most_dependent:
                entity_type = self.kg.entities.get(component, {}).get('type', 'Unknown')
                icon = self.kg.entity_types.get(entity_type, '🔵')
                result += f"{icon} {component}: depends on {len(deps)} components\n"
        
        return result
    
    def _analyze_risks(self):
        """Comprehensive risk analysis"""
        risks = []
        
        # Single points of failure
        connections = defaultdict(int)
        for rel in self.kg.relationships:
            connections[rel['source']] += 1
            connections[rel['target']] += 1
        
        critical_components = [(name, count) for name, count in connections.items() if count > 4]
        if critical_components:
            risks.append({
                'level': 'HIGH',
                'type': 'Single Point of Failure',
                'components': [name for name, _ in critical_components[:3]],
                'description': 'Highly connected components that could cause cascading failures'
            })
        
        # Unmanaged components
        managed = set(rel['target'] for rel in self.kg.relationships if rel['type'] == 'MANAGES')
        unmanaged = [name for name, entity in self.kg.entities.items() 
                    if name not in managed and entity['type'] not in ['Person', 'Location']]
        
        if unmanaged:
            risks.append({
                'level': 'MEDIUM',
                'type': 'Governance Gap',
                'components': unmanaged[:3],
                'description': 'Components without clear ownership or management'
            })
        
        # Technology concentration
        tech_usage = defaultdict(list)
        for rel in self.kg.relationships:
            if rel['type'] == 'USES':
                tech_usage[rel['target']].append(rel['source'])
        
        concentrated_tech = [(tech, users) for tech, users in tech_usage.items() if len(users) > 3]
        if concentrated_tech:
            risks.append({
                'level': 'MEDIUM',
                'type': 'Technology Concentration',
                'components': [tech for tech, _ in concentrated_tech[:2]],
                'description': 'Heavy reliance on specific technologies'
            })
        
        result = "🛡️ **Risk Analysis:**\n\n"
        for risk in risks:
            level_icon = '🔴' if risk['level'] == 'HIGH' else '🟡'
            result += f"{level_icon} **{risk['level']} RISK - {risk['type']}**\n"
            result += f"Components: {', '.join(risk['components'])}\n"
            result += f"Impact: {risk['description']}\n\n"
        
        return result if risks else "✅ **No significant risks detected in current analysis**"
    
    def _analyze_technology_stack(self):
        """Analyze technology stack"""
        tech_entities = [e for e in self.kg.entities.values() if e['type'] == 'Software']
        
        if not tech_entities:
            return "❌ **No technology information found in the data**"
        
        result = "🛠️ **Technology Stack Analysis:**\n\n"
        
        # Technology usage
        tech_usage = defaultdict(list)
        for rel in self.kg.relationships:
            if rel['type'] == 'USES' and rel['target'] in [t['name'] for t in tech_entities]:
                tech_usage[rel['target']].append(rel['source'])
        
        result += "**Technology Usage:**\n"
        for tech, users in sorted(tech_usage.items(), key=lambda x: len(x[1]), reverse=True):
            result += f"• {tech}: used by {len(users)} component(s)\n"
            for user in users[:3]:  # Show first 3 users
                entity_type = self.kg.entities.get(user, {}).get('type', 'Unknown')
                icon = self.kg.entity_types.get(entity_type, '🔵')
                result += f"  {icon} {user}\n"
            if len(users) > 3:
                result += f"  ... and {len(users) - 3} more\n"
        
        return result
    
    def _describe_entity(self, question):
        """Describe specific entity"""
        # Extract entity name from question
        words = question.lower().split()
        
        # Find entity name in question
        entity_name = None
        for word in words:
            if word in self.kg.entities:
                entity_name = word
                break
        
        # If not found, try partial matching
        if not entity_name:
            for name in self.kg.entities.keys():
                if any(word in name.lower() for word in words):
                    entity_name = name
                    break
        
        if entity_name:
            entity = self.kg.entities[entity_name]
            icon = self.kg.entity_types.get(entity['type'], '🔵')
            
            result = f"{icon} **{entity_name}**\n\n"
            result += f"**Type:** {entity['type']}\n"
            result += f"**Description:** {entity['description']}\n\n"
            
            # Show relationships
            incoming = [rel for rel in self.kg.relationships if rel['target'] == entity_name]
            outgoing = [rel for rel in self.kg.relationships if rel['source'] == entity_name]
            
            if incoming:
                result += "**Incoming Relationships:**\n"
                for rel in incoming[:5]:
                    result += f"• {rel['source']} → {rel['type']} → {entity_name}\n"
            
            if outgoing:
                result += "**Outgoing Relationships:**\n"
                for rel in outgoing[:5]:
                    result += f"• {entity_name} → {rel['type']} → {rel['target']}\n"
            
            return result
        
        return "❌ **Entity not found. Try asking about specific components in your data.**"
    
    def _analyze_management(self):
        """Analyze management structure"""
        managers = defaultdict(list)
        for rel in self.kg.relationships:
            if rel['type'] == 'MANAGES':
                managers[rel['source']].append(rel['target'])
        
        result = "👤 **Management Analysis:**\n\n"
        
        if managers:
            result += "**Management Structure:**\n"
            for manager, managed in sorted(managers.items(), key=lambda x: len(x[1]), reverse=True):
                result += f"• {manager} manages {len(managed)} component(s):\n"
                for component in managed[:3]:
                    entity_type = self.kg.entities.get(component, {}).get('type', 'Unknown')
                    icon = self.kg.entity_types.get(entity_type, '🔵')
                    result += f"  {icon} {component}\n"
                if len(managed) > 3:
                    result += f"  ... and {len(managed) - 3} more\n"
        
        # Find unmanaged components
        managed_components = set()
        for managed_list in managers.values():
            managed_components.update(managed_list)
        
        unmanaged = [name for name, entity in self.kg.entities.items() 
                    if name not in managed_components and entity['type'] not in ['Person', 'Location']]
        
        if unmanaged:
            result += f"\n**⚠️ Unmanaged Components ({len(unmanaged)}):**\n"
            for component in unmanaged[:5]:
                entity_type = self.kg.entities.get(component, {}).get('type', 'Unknown')
                icon = self.kg.entity_types.get(entity_type, '🔵')
                result += f"• {icon} {component}\n"
            if len(unmanaged) > 5:
                result += f"... and {len(unmanaged) - 5} more\n"
        
        return result
    
    def _enhance_with_strategic_llm(self, question, structured_answer):
        """Enhance answer with strategic LLM insights"""
        try:
            prompt = f"""
            Question: {question}
            
            Data Analysis Results:
            {structured_answer}
            
            Based on this technical analysis, provide strategic insights and recommendations:
            
            1. Business impact and implications
            2. Risk mitigation strategies
            3. Optimization opportunities
            4. Action items for leadership
            
            Be specific, actionable, and focus on business value.
            """
            
            headers = {
                "Authorization": f"Bearer {LLM_API_KEY}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": "You are a strategic IT consultant providing executive-level insights from technical analysis."},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 400,
                "temperature": 0.3
            }
            
            response = requests.post(LLM_API_URL, headers=headers, json=payload, timeout=10)
            
            if response.status_code == 200:
                llm_response = response.json()['choices'][0]['message']['content']
                return f"📊 **Technical Analysis:**\n{structured_answer}\n\n🧠 **Strategic Insights:**\n{llm_response}"
            
        except Exception as e:
            pass
        
        return structured_answer
    
    def _provide_suggestions(self):
        """Provide helpful suggestions"""
        return """💡 **Try asking strategic questions like:**

🏗️ **Architecture Questions:**
• "Analyze the overall architecture"
• "What are the dependencies?"
• "Describe the [component name]"

🛡️ **Risk & Security:**
• "What are the risks in our system?"
• "Which components are most critical?"
• "Show me single points of failure"

🛠️ **Technology:**
• "Analyze our technology stack"
• "What technologies are we using?"
• "Show technology dependencies"

👤 **Management:**
• "Who manages what components?"
• "What are the management gaps?"
• "Show ownership structure"
"""

def create_sample_data():
    """Create sample data that demonstrates rich knowledge graph capabilities"""
    return pd.DataFrame({
        'Application Name': [
            'Customer Portal',
            'Payment Gateway', 
            'User Management Service',
            'Order Processing System',
            'Analytics Dashboard'
        ],
        'Type': [
            'Web Application',
            'Payment Service',
            'Identity Service', 
            'Business Application',
            'Analytics Platform'
        ],
        'Technology Stack': [
            'React, Node.js, PostgreSQL',
            'Java, Spring Boot, Redis',
            'Python, FastAPI, MongoDB',
            'Java, Kafka, Oracle',
            'Python, Elasticsearch, Kibana'
        ],
        'Owner': [
            'John Smith',
            'Jane Doe',
            'Bob Wilson',
            'Alice Brown',
            'John Smith'
        ],
        'Environment': [
            'Production',
            'Production',
            'Production',
            'Staging',
            'Production'
        ],
        'Location': [
            'AWS US-East',
            'AWS US-East',
            'Azure Central',
            'AWS US-West',
            'AWS US-East'
        ],
        'Criticality': [
            'High',
            'Critical',
            'Critical',
            'Medium',
            'Low'
        ],
        'Dependencies': [
            'User Management Service, Payment Gateway',
            'Order Processing System',
            'Analytics Dashboard',
            'Customer Portal',
            'Order Processing System, User Management Service'
        ]
    })

def main():
    st.title("🔗 Advanced Knowledge Graph System")
    st.write("Transform your enterprise data into intelligent, connected insights")
    
    # Initialize session state
    if 'kg' not in st.session_state:
        st.session_state.kg = None
    if 'chat_engine' not in st.session_state:
        st.session_state.chat_engine = None
    
    # Configuration sidebar
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # LLM Status
        llm_status = "🟢 Active" if LLM_API_KEY != "your_api_key_here" else "🔴 Configure API Key"
        st.write(f"**LLM Enhancement:** {llm_status}")
        
        if llm_status == "🔴 Configure API Key":
            st.info("💡 Configure LLM_API_KEY in the code for enhanced insights")
        
        st.divider()
        
        st.header("📊 Data Source")
        
        # Sample data button
        if st.button("🚀 Load Sample Architecture", type="primary"):
            with st.spinner("Creating knowledge graph..."):
                df = create_sample_data()
                kg = EnhancedKnowledgeGraph()
                kg.process_data(df)
                st.session_state.kg = kg
                st.session_state.chat_engine = EnhancedChatEngine(kg)
                st.success("✅ Sample architecture loaded!")
                st.rerun()
        
        # File upload
        uploaded_file = st.file_uploader(
            "📁 Upload Excel/CSV", 
            type=['xlsx', 'csv'],
            help="Upload your architecture or component data"
        )
        
        if uploaded_file:
            try:
                df = pd.read_csv(uploaded_file) if uploaded_file.name.endswith('.csv') else pd.read_excel(uploaded_file)
                st.success(f"📊 {len(df)} rows loaded")
                
                if st.button("🔄 Process Architecture Data"):
                    with st.spinner("Building knowledge graph..."):
                        kg = EnhancedKnowledgeGraph()
                        kg.process_data(df)
                        st.session_state.kg = kg
                        st.session_state.chat_engine = EnhancedChatEngine(kg)
                        st.success("✅ Knowledge graph created!")
                        st.rerun()
                        
            except Exception as e:
                st.error(f"❌ Error: {str(e)}")
    
    # Main content area
    if st.session_state.kg is None:
        # Welcome screen with value proposition
        st.markdown("""
        ### 🎯 Why Advanced Knowledge Graphs?
        
        **Transform your spreadsheets into intelligent, connected insights:**
        """)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **🔍 Discover Hidden Patterns:**
            - Find critical dependencies others miss
            - Identify single points of failure
            - Uncover management gaps
            - Analyze technology concentration risks
            
            **🧠 AI-Powered Insights:**
            - Strategic recommendations from LLM
            - Risk analysis and mitigation strategies
            - Architecture optimization opportunities
            """)
        
        with col2:
            st.markdown("""
            **📊 Rich Visualizations:**
            - Interactive network diagrams
            - Component relationship mapping
            - Technology stack analysis
            - Management structure overview
            
            **💬 Intelligent Chat:**
            - Ask complex architecture questions
            - Get strategic business insights
            - Receive actionable recommendations
            """)
        
        st.info("👆 **Get started:** Load sample data or upload your architecture file")
        return
    
    # Main tabs
    tab1, tab2 = st.tabs(["💡 Strategic Dashboard", "💬 Ask Architecture Questions"])
    
    with tab1:
        st.header("📊 Strategic Architecture Insights")
        
        # Key metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("🏗️ Components", len(st.session_state.kg.entities))
        with col2:
            st.metric("🔗 Relationships", len(st.session_state.kg.relationships))
        with col3:
            entity_types = len(set(e['type'] for e in st.session_state.kg.entities.values()))
            st.metric("📋 Entity Types", entity_types)
        with col4:
            avg_connections = len(st.session_state.kg.relationships) / len(st.session_state.kg.entities) if st.session_state.kg.entities else 0
            st.metric("🔄 Avg Connections", f"{avg_connections:.1f}")
        
        # Strategic insights
        st.subheader("🧠 Strategic Insights")
        insights = st.session_state.kg.get_strategic_insights()
        
        for insight in insights:
            if insight.get('type') == 'risk':
                st.error(f"**{insight['title']}**\n\n{insight['content']}")
            elif insight.get('type') == 'optimization':
                st.info(f"**{insight['title']}**\n\n{insight['content']}")
            else:
                st.warning(f"**{insight['title']}**\n\n{insight['content']}")
            
            st.divider()
        
        # Network overview
        st.subheader("🌐 Architecture Overview")
        
        # Entity type distribution
        entity_type_counts = defaultdict(int)
        for entity in st.session_state.kg.entities.values():
            entity_type_counts[entity['type']] += 1
        
        st.write("**Component Distribution:**")
        for entity_type, count in sorted(entity_type_counts.items(), key=lambda x: x[1], reverse=True):
            icon = st.session_state.kg.entity_types.get(entity_type, '🔵')
            percentage = (count / len(st.session_state.kg.entities)) * 100
            st.write(f"{icon} **{entity_type}**: {count} ({percentage:.1f}%)")
        
        # Key relationships
        if st.checkbox("🔍 Show Key Relationships"):
            st.write("**🔗 Important Connections:**")
            
            # Group relationships by type
            rel_groups = defaultdict(list)
            for rel in st.session_state.kg.relationships:
                rel_groups[rel['type']].append(rel)
            
            for rel_type, rels in rel_groups.items():
                st.write(f"\n**{rel_type} Relationships:**")
                for rel in rels[:5]:  # Show first 5
                    source_type = st.session_state.kg.entities.get(rel['source'], {}).get('type', 'Unknown')
                    target_type = st.session_state.kg.entities.get(rel['target'], {}).get('type', 'Unknown')
                    source_icon = st.session_state.kg.entity_types.get(source_type, '🔵')
                    target_icon = st.session_state.kg.entity_types.get(target_type, '🔵')
                    
                    st.write(f"  {source_icon} {rel['source']} → {target_icon} {rel['target']}")
                
                if len(rels) > 5:
                    st.write(f"  ... and {len(rels) - 5} more {rel_type} relationships")
        
        # Export options
        st.subheader("💾 Export Options")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📥 Download Graph Data"):
                network_data = st.session_state.kg.get_network_view()
                st.download_button(
                    "📄 Download as JSON",
                    json.dumps(network_data, indent=2),
                    "knowledge_graph.json",
                    "application/json"
                )
        
        with col2:
            if st.button("📊 Generate Report"):
                st.info("📋 Report generation coming soon...")
    
    with tab2:
        st.header("💬 Architecture Intelligence Chat")
        
        # Show LLM enhancement status
        if st.session_state.kg.use_llm:
            st.success("🧠 **AI Enhancement Active** - Get strategic insights with your technical analysis")
        else:
            st.info("⚙️ **Configure LLM API Key** for enhanced strategic insights")
        
        # Sample question
        if st.button("💡 What are the risks in our architecture?"):
            st.session_state.sample_question = "What are the risks in our architecture?"
        
        # Chat interface
        question = st.text_input(
            "Ask about your architecture:",
            value=st.session_state.get('sample_question', ''),
            placeholder="e.g., 'Analyze the overall architecture', 'What are the dependencies?', 'Show me critical components'"
        )
        
        if question:
            with st.spinner("🔍 Analyzing architecture..."):
                try:
                    answer = st.session_state.chat_engine.answer_question(question)
                    st.markdown(answer)
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.info("💡 Try rephrasing your question or check your LLM configuration")
        
        # Quick action buttons
        st.subheader("⚡ Quick Analysis")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🏗️ Architecture Overview"):
                with st.spinner("Analyzing..."):
                    answer = st.session_state.chat_engine.answer_question("Analyze the overall architecture")
                    st.markdown(answer)
        
        with col2:
            if st.button("🔗 Dependencies"):
                with st.spinner("Analyzing..."):
                    answer = st.session_state.chat_engine.answer_question("What are the dependencies?")
                    st.markdown(answer)
        
        with col3:
            if st.button("🛡️ Risk Analysis"):
                with st.spinner("Analyzing..."):
                    answer = st.session_state.chat_engine.answer_question("What are the risks?")
                    st.markdown(answer)
        
        # Help section
        with st.expander("💡 Question Examples"):
            st.markdown("""
            **🏗️ Architecture Questions:**
            - "Analyze the overall architecture"
            - "What are the main components?"
            - "Describe the [component name]"
            
            **🔗 Relationship Questions:**
            - "What are the dependencies?"
            - "Which components are most connected?"
            - "Show me the data flow"
            
            **🛡️ Risk & Security:**
            - "What are the risks in our system?"
            - "Which components are critical?"
            - "Show me single points of failure"
            
            **🛠️ Technology:**
            - "Analyze our technology stack"
            - "What technologies are we using?"
            - "Show technology concentration"
            
            **👤 Management:**
            - "Who manages what components?"
            - "What are the management gaps?"
            - "Show ownership structure"
            """)

if __name__ == "__main__":
    main()
