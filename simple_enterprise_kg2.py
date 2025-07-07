import streamlit as st

st.set_page_config(page_title="📊 Direct Excel Knowledge Graph", layout="wide")

import pandas as pd
import networkx as nx
from pyvis.network import Network
import os
import uuid

class DirectExcelMapper:
    """Directly map Excel data to knowledge graph without LLM guessing"""
    
    def __init__(self):
        self.entities = {}
        self.relationships = []
    
    def process_excel(self, df):
        """Process Excel data directly - each row becomes entities with relationships"""
        
        st.write("### 📋 Excel Data Analysis")
        st.write(f"**Rows:** {len(df)} | **Columns:** {len(df.columns)}")
        
        # Show column mapping options
        st.write("**Your Columns:**")
        for i, col in enumerate(df.columns):
            st.write(f"{i+1}. `{col}`")
        
        st.write("---")
        
        # Let user see the data
        with st.expander("🔍 View Your Excel Data"):
            st.dataframe(df.head(10))
        
        # Process each row as a component
        components_created = 0
        relationships_created = 0
        
        for idx, row in df.iterrows():
            if idx >= 20:  # Limit to prevent overload
                break
                
            # Create main component from this row
            component_id = f"component_{idx}"
            component_name = self._extract_component_name(row, df.columns)
            component_type = self._determine_component_type(row, df.columns)
            
            # Extract all properties from this row
            properties = {}
            for col in df.columns:
                if pd.notna(row[col]) and str(row[col]).strip():
                    clean_key = col.replace(' ', '_').replace('-', '_').lower()
                    properties[clean_key] = str(row[col]).strip()
            
            # Add the main component
            self.entities[component_id] = {
                "id": component_id,
                "label": component_name,
                "type": component_type,
                "properties": properties,
                "excel_row": idx + 1
            }
            components_created += 1
            
            # Create relationships based on column content
            relationships_created += self._create_relationships_from_row(component_id, row, df.columns, idx)
        
        st.success(f"✅ **Direct Mapping Complete:** {components_created} components, {relationships_created} relationships")
        return self._prepare_graph_data()
    
    def _extract_component_name(self, row, columns):
        """Extract the best name for this component"""
        name_candidates = []
        
        # Look for common name columns
        name_columns = [col for col in columns if any(keyword in col.lower() 
                       for keyword in ['name', 'title', 'label', 'component', 'asset', 'system', 'application'])]
        
        for col in name_columns:
            if pd.notna(row[col]) and str(row[col]).strip():
                return str(row[col]).strip()
        
        # Fallback: use first non-empty column
        for col in columns:
            if pd.notna(row[col]) and str(row[col]).strip():
                value = str(row[col]).strip()
                if len(value) > 1:  # Avoid single character names
                    return value
        
        return f"Component {row.name + 1}"
    
    def _determine_component_type(self, row, columns):
        """Determine component type from row data"""
        row_text = " ".join([str(row[col]) for col in columns if pd.notna(row[col])]).lower()
        
        # Application patterns
        if any(keyword in row_text for keyword in ['application', 'app', 'software', 'program', 'tool']):
            return 'application'
        
        # Server patterns
        elif any(keyword in row_text for keyword in ['server', 'host', 'machine', 'vm', 'virtual']):
            return 'server'
        
        # Database patterns
        elif any(keyword in row_text for keyword in ['database', 'db', 'data', 'sql', 'oracle', 'mysql']):
            return 'database'
        
        # Network patterns
        elif any(keyword in row_text for keyword in ['network', 'router', 'switch', 'firewall', 'load balancer']):
            return 'network'
        
        # Service patterns
        elif any(keyword in row_text for keyword in ['service', 'api', 'interface', 'endpoint']):
            return 'service'
        
        # Person patterns
        elif any(keyword in row_text for keyword in ['admin', 'manager', 'user', 'owner', 'analyst', 'engineer']):
            return 'person'
        
        # Location patterns
        elif any(keyword in row_text for keyword in ['datacenter', 'office', 'location', 'site', 'building']):
            return 'location'
        
        # Default
        else:
            return 'component'
    
    def _create_relationships_from_row(self, component_id, row, columns, row_idx):
        """Create relationships based on column content"""
        relationships_count = 0
        
        # Look for relationship indicators in columns
        for col in columns:
            if pd.notna(row[col]) and str(row[col]).strip():
                col_lower = col.lower()
                value = str(row[col]).strip()
                
                # Skip if it's the component's own name
                if value == self.entities[component_id]['label']:
                    continue
                
                # Management relationships
                if any(keyword in col_lower for keyword in ['owner', 'manager', 'admin', 'responsible']):
                    person_id = f"person_{value.replace(' ', '_').lower()}"
                    if person_id not in self.entities:
                        self.entities[person_id] = {
                            "id": person_id,
                            "label": value,
                            "type": "person",
                            "properties": {"role": "Manager/Owner", "source": f"Row {row_idx + 1}"},
                            "excel_row": f"Derived from row {row_idx + 1}"
                        }
                    
                    self.relationships.append({
                        "source": person_id,
                        "target": component_id,
                        "type": "manages",
                        "properties": {"description": f"Manages {self.entities[component_id]['label']}", "source_column": col}
                    })
                    relationships_count += 1
                
                # Location relationships
                elif any(keyword in col_lower for keyword in ['location', 'site', 'datacenter', 'environment']):
                    location_id = f"location_{value.replace(' ', '_').lower()}"
                    if location_id not in self.entities:
                        self.entities[location_id] = {
                            "id": location_id,
                            "label": value,
                            "type": "location",
                            "properties": {"type": "Location", "source": f"Row {row_idx + 1}"},
                            "excel_row": f"Derived from row {row_idx + 1}"
                        }
                    
                    self.relationships.append({
                        "source": component_id,
                        "target": location_id,
                        "type": "located_in",
                        "properties": {"description": f"Located in {value}", "source_column": col}
                    })
                    relationships_count += 1
                
                # Department relationships
                elif any(keyword in col_lower for keyword in ['department', 'dept', 'team', 'group', 'division']):
                    dept_id = f"dept_{value.replace(' ', '_').lower()}"
                    if dept_id not in self.entities:
                        self.entities[dept_id] = {
                            "id": dept_id,
                            "label": value,
                            "type": "organization",
                            "properties": {"type": "Department", "source": f"Row {row_idx + 1}"},
                            "excel_row": f"Derived from row {row_idx + 1}"
                        }
                    
                    self.relationships.append({
                        "source": component_id,
                        "target": dept_id,
                        "type": "belongs_to",
                        "properties": {"description": f"Belongs to {value}", "source_column": col}
                    })
                    relationships_count += 1
                
                # Dependency relationships
                elif any(keyword in col_lower for keyword in ['depends', 'requires', 'uses', 'connects']):
                    dep_id = f"dependency_{value.replace(' ', '_').lower()}"
                    if dep_id not in self.entities:
                        self.entities[dep_id] = {
                            "id": dep_id,
                            "label": value,
                            "type": "system",
                            "properties": {"type": "Dependency", "source": f"Row {row_idx + 1}"},
                            "excel_row": f"Derived from row {row_idx + 1}"
                        }
                    
                    self.relationships.append({
                        "source": component_id,
                        "target": dep_id,
                        "type": "depends_on",
                        "properties": {"description": f"Depends on {value}", "source_column": col}
                    })
                    relationships_count += 1
        
        return relationships_count
    
    def _prepare_graph_data(self):
        """Prepare data for graph generation"""
        return {
            "entities": list(self.entities.values()),
            "relationships": self.relationships
        }

class ExcelChatEngine:
    """Chat engine to answer questions about the Excel-based knowledge graph"""
    
    def __init__(self, entities, relationships, original_df):
        self.entities = {e['id']: e for e in entities}
        self.relationships = relationships
        self.df = original_df
        
        # Create lookup indices for fast searching
        self.entity_by_name = {}
        self.entity_by_type = {}
        
        for entity in entities:
            # Name lookup (case-insensitive)
            name_key = entity['label'].lower()
            self.entity_by_name[name_key] = entity['id']
            
            # Type lookup
            entity_type = entity.get('type', 'unknown')
            if entity_type not in self.entity_by_type:
                self.entity_by_type[entity_type] = []
            self.entity_by_type[entity_type].append(entity['id'])
    
    def answer_question(self, question):
        """Answer questions about the Excel data and knowledge graph"""
        question_lower = question.lower().strip()
        
        # Oracle usage questions
        if 'oracle' in question_lower and any(word in question_lower for word in ['used', 'application', 'app', 'software']):
            return self._find_oracle_usage()
        
        # Common software questions
        elif any(phrase in question_lower for phrase in ['common software', 'what software', 'software common']):
            return self._find_common_software()
        
        # Database usage questions
        elif any(word in question_lower for word in ['database', 'db']) and any(word in question_lower for word in ['used', 'application', 'app']):
            return self._find_database_usage()
        
        # What uses X questions
        elif 'what uses' in question_lower or 'what applications use' in question_lower:
            # Extract the technology name
            tech_name = self._extract_technology_name(question_lower)
            if tech_name:
                return self._find_what_uses_technology(tech_name)
        
        # Who manages X questions
        elif 'who manages' in question_lower or 'who owns' in question_lower:
            entity_name = self._extract_entity_name_from_question(question_lower, ['who manages', 'who owns'])
            if entity_name:
                return self._find_who_manages(entity_name)
        
        # What does X manage questions
        elif 'what does' in question_lower and 'manage' in question_lower:
            person_name = self._extract_person_name_from_question(question_lower)
            if person_name:
                return self._find_what_person_manages(person_name)
        
        # Location questions
        elif any(phrase in question_lower for phrase in ['what is in', 'what\'s in', 'location', 'datacenter', 'site']):
            location_name = self._extract_location_name(question_lower)
            if location_name:
                return self._find_in_location(location_name)
        
        # Show all X questions
        elif 'show all' in question_lower or 'list all' in question_lower:
            return self._handle_show_all_question(question_lower)
        
        # Technology stack questions
        elif any(phrase in question_lower for phrase in ['technology stack', 'tech stack', 'technologies used']):
            return self._find_technology_stack()
        
        # Dependencies questions
        elif any(word in question_lower for word in ['depends', 'dependencies', 'requires']):
            entity_name = self._extract_entity_name_from_question(question_lower, ['depends', 'dependencies', 'requires'])
            if entity_name:
                return self._find_dependencies(entity_name)
        
        # Department questions
        elif any(word in question_lower for word in ['department', 'team', 'group']):
            if 'what' in question_lower:
                return self._find_department_breakdown()
        
        # Excel data search
        elif any(phrase in question_lower for phrase in ['search', 'find', 'contains']):
            search_term = self._extract_search_term(question_lower)
            if search_term:
                return self._search_excel_data(search_term)
        
        # Fallback with suggestions
        else:
            return self._provide_suggestions()
    
    def _find_oracle_usage(self):
        """Find applications that use Oracle"""
        oracle_users = []
        
        # Search through Excel data for Oracle mentions
        for idx, row in self.df.iterrows():
            row_text = " ".join([str(val) for val in row.values if pd.notna(val)]).lower()
            if 'oracle' in row_text:
                component_name = self._get_component_name_from_row(row)
                oracle_users.append({
                    'component': component_name,
                    'row': idx + 1,
                    'context': self._get_oracle_context(row)
                })
        
        if oracle_users:
            result = "🔍 **Oracle Usage Found:**\n\n"
            for user in oracle_users:
                result += f"• **{user['component']}** (Row {user['row']})\n"
                if user['context']:
                    result += f"  📋 Context: {user['context']}\n"
                result += "\n"
            
            result += f"📊 **Summary:** {len(oracle_users)} component(s) use Oracle"
            return result
        else:
            return "❌ **No Oracle usage found** in your Excel data.\n\n💡 Try searching for other databases like 'MySQL', 'SQL Server', or 'PostgreSQL'"
    
    def _find_common_software(self):
        """Find common software/technologies across applications"""
        software_count = {}
        
        # Look for software mentions in Excel data
        software_keywords = ['oracle', 'mysql', 'sql server', 'postgres', 'mongodb', 'java', 'python', '.net', 
                           'apache', 'nginx', 'tomcat', 'iis', 'linux', 'windows', 'unix', 'docker', 'kubernetes']
        
        for idx, row in self.df.iterrows():
            row_text = " ".join([str(val) for val in row.values if pd.notna(val)]).lower()
            component_name = self._get_component_name_from_row(row)
            
            for software in software_keywords:
                if software in row_text:
                    if software not in software_count:
                        software_count[software] = []
                    software_count[software].append({
                        'component': component_name,
                        'row': idx + 1
                    })
        
        if software_count:
            # Sort by frequency
            sorted_software = sorted(software_count.items(), key=lambda x: len(x[1]), reverse=True)
            
            result = "📊 **Common Software/Technologies:**\n\n"
            
            for software, usage_list in sorted_software[:10]:  # Top 10
                result += f"🔹 **{software.title()}** - Used by {len(usage_list)} component(s)\n"
                for usage in usage_list[:3]:  # Show first 3 examples
                    result += f"   • {usage['component']} (Row {usage['row']})\n"
                if len(usage_list) > 3:
                    result += f"   • ... and {len(usage_list) - 3} more\n"
                result += "\n"
            
            return result
        else:
            return "❌ **No common software patterns found** in your Excel data.\n\n💡 The system looks for technologies like Oracle, MySQL, Java, Python, etc."
    
    def _find_database_usage(self):
        """Find database usage across applications"""
        database_keywords = ['oracle', 'mysql', 'sql server', 'postgres', 'postgresql', 'mongodb', 'redis', 'cassandra', 'db2']
        database_usage = {}
        
        for idx, row in self.df.iterrows():
            row_text = " ".join([str(val) for val in row.values if pd.notna(val)]).lower()
            component_name = self._get_component_name_from_row(row)
            
            for db in database_keywords:
                if db in row_text:
                    if db not in database_usage:
                        database_usage[db] = []
                    database_usage[db].append({
                        'component': component_name,
                        'row': idx + 1
                    })
        
        if database_usage:
            result = "🗄️ **Database Usage Analysis:**\n\n"
            
            for db, usage_list in sorted(database_usage.items(), key=lambda x: len(x[1]), reverse=True):
                result += f"**{db.upper()}** - {len(usage_list)} component(s)\n"
                for usage in usage_list:
                    result += f"  • {usage['component']} (Row {usage['row']})\n"
                result += "\n"
            
            return result
        else:
            return "❌ **No database usage found** in your Excel data.\n\n💡 Searched for: Oracle, MySQL, SQL Server, PostgreSQL, MongoDB, etc."
    
    def _find_what_uses_technology(self, tech_name):
        """Find what components use a specific technology"""
        users = []
        
        for idx, row in self.df.iterrows():
            row_text = " ".join([str(val) for val in row.values if pd.notna(val)]).lower()
            if tech_name.lower() in row_text:
                component_name = self._get_component_name_from_row(row)
                users.append({
                    'component': component_name,
                    'row': idx + 1,
                    'type': self._determine_component_type_from_row(row)
                })
        
        if users:
            result = f"🔍 **Components using {tech_name.title()}:**\n\n"
            
            # Group by type
            by_type = {}
            for user in users:
                user_type = user['type']
                if user_type not in by_type:
                    by_type[user_type] = []
                by_type[user_type].append(user)
            
            for comp_type, type_users in by_type.items():
                result += f"**{comp_type.title()}s:**\n"
                for user in type_users:
                    result += f"  • {user['component']} (Row {user['row']})\n"
                result += "\n"
            
            result += f"📊 **Total:** {len(users)} component(s) use {tech_name.title()}"
            return result
        else:
            return f"❌ **No components found using {tech_name.title()}**\n\n💡 Try searching for other technologies or check spelling"
    
    def _find_who_manages(self, entity_name):
        """Find who manages a specific entity"""
        # Search through relationships
        managers = []
        for rel in self.relationships:
            if rel['type'] == 'manages':
                target_entity = self.entities.get(rel['target'])
                if target_entity and entity_name.lower() in target_entity['label'].lower():
                    manager_entity = self.entities.get(rel['source'])
                    if manager_entity:
                        managers.append({
                            'manager': manager_entity['label'],
                            'entity': target_entity['label'],
                            'relationship': rel['type']
                        })
        
        if managers:
            result = f"👤 **Management for '{entity_name}':**\n\n"
            for mgr in managers:
                result += f"• **{mgr['manager']}** manages **{mgr['entity']}**\n"
            return result
        else:
            return f"❌ **No management information found for '{entity_name}'**\n\n💡 Try checking the exact component name or look for ownership data"
    
    def _search_excel_data(self, search_term):
        """Search through Excel data for a term"""
        matches = []
        
        for idx, row in self.df.iterrows():
            row_text = " ".join([str(val) for val in row.values if pd.notna(val)]).lower()
            if search_term.lower() in row_text:
                component_name = self._get_component_name_from_row(row)
                # Find which columns contain the search term
                matching_columns = []
                for col in self.df.columns:
                    if pd.notna(row[col]) and search_term.lower() in str(row[col]).lower():
                        matching_columns.append(f"{col}: {row[col]}")
                
                matches.append({
                    'component': component_name,
                    'row': idx + 1,
                    'matches': matching_columns[:3]  # Show first 3 matches
                })
        
        if matches:
            result = f"🔍 **Search results for '{search_term}':**\n\n"
            for match in matches[:10]:  # Show first 10 results
                result += f"• **{match['component']}** (Row {match['row']})\n"
                for col_match in match['matches']:
                    result += f"  📋 {col_match}\n"
                result += "\n"
            
            if len(matches) > 10:
                result += f"... and {len(matches) - 10} more results\n"
            
            result += f"📊 **Total:** {len(matches)} match(es) found"
            return result
        else:
            return f"❌ **No matches found for '{search_term}'**\n\n💡 Try different search terms or check spelling"
    
    def _handle_show_all_question(self, question):
        """Handle 'show all' type questions"""
        if any(word in question for word in ['application', 'app']):
            return self._show_all_by_type('application')
        elif any(word in question for word in ['server', 'servers']):
            return self._show_all_by_type('server')
        elif any(word in question for word in ['database', 'databases', 'db']):
            return self._show_all_by_type('database')
        elif any(word in question for word in ['person', 'people', 'manager', 'admin']):
            return self._show_all_by_type('person')
        elif any(word in question for word in ['location', 'locations', 'site']):
            return self._show_all_by_type('location')
        else:
            return self._show_all_components()
    
    def _show_all_by_type(self, component_type):
        """Show all components of a specific type"""
        components = self.entity_by_type.get(component_type, [])
        
        if components:
            result = f"📋 **All {component_type.title()}s ({len(components)}):**\n\n"
            for comp_id in components:
                entity = self.entities[comp_id]
                result += f"• **{entity['label']}**"
                if 'excel_row' in entity:
                    result += f" (Excel Row {entity['excel_row']})"
                
                # Add key properties
                props = entity.get('properties', {})
                key_props = []
                for key, value in props.items():
                    if key in ['department', 'location', 'status', 'type', 'role'] and value:
                        key_props.append(f"{key}: {value}")
                
                if key_props:
                    result += f"\n  📋 {' | '.join(key_props[:2])}"
                
                result += "\n\n"
            
            return result
        else:
            return f"❌ **No {component_type}s found** in your data"
    
    def _show_all_components(self):
        """Show all components grouped by type"""
        result = "📊 **All Components by Type:**\n\n"
        
        for comp_type, comp_list in self.entity_by_type.items():
            result += f"**{comp_type.title()}s ({len(comp_list)}):**\n"
            for comp_id in comp_list[:5]:  # Show first 5 of each type
                entity = self.entities[comp_id]
                result += f"  • {entity['label']}\n"
            if len(comp_list) > 5:
                result += f"  • ... and {len(comp_list) - 5} more\n"
            result += "\n"
        
        return result
    
    def _provide_suggestions(self):
        """Provide helpful suggestions for questions"""
        return """❓ **I didn't understand that question. Try asking:**

🔍 **Technology Questions:**
• "What applications use Oracle?"
• "What software is common in applications?"
• "What uses MySQL?"
• "Search for Java"

👤 **Management Questions:**
• "Who manages [component name]?"
• "What does [person name] manage?"

📍 **Location Questions:**
• "What is in DataCenter-A?"
• "Show all locations"

📋 **General Questions:**
• "Show all applications"
• "Show all servers"
• "List all databases"
• "What are the dependencies for [component]?"

🔎 **Search:**
• "Search for [any term]"
• "Find components with [keyword]"

💡 **Tip:** Use the exact names from your Excel data for best results!"""
    
    # Helper methods
    def _get_component_name_from_row(self, row):
        """Extract component name from Excel row"""
        # Look for name columns first
        name_columns = [col for col in self.df.columns if any(keyword in col.lower() 
                       for keyword in ['name', 'title', 'component', 'asset', 'system', 'application'])]
        
        for col in name_columns:
            if pd.notna(row[col]) and str(row[col]).strip():
                return str(row[col]).strip()
        
        # Fallback to first non-empty column
        for col in self.df.columns:
            if pd.notna(row[col]) and str(row[col]).strip():
                return str(row[col]).strip()
        
        return f"Component {row.name + 1}"
    
    def _determine_component_type_from_row(self, row):
        """Determine component type from Excel row"""
        row_text = " ".join([str(val) for val in row.values if pd.notna(val)]).lower()
        
        if any(keyword in row_text for keyword in ['application', 'app', 'software']):
            return 'application'
        elif any(keyword in row_text for keyword in ['server', 'host', 'machine']):
            return 'server'
        elif any(keyword in row_text for keyword in ['database', 'db', 'data']):
            return 'database'
        else:
            return 'component'
    
    def _extract_technology_name(self, question):
        """Extract technology name from question"""
        # Simple extraction - look for common patterns
        words = question.split()
        tech_indicators = ['uses', 'use', 'using', 'with']
        
        for i, word in enumerate(words):
            if word in tech_indicators and i + 1 < len(words):
                return words[i + 1].strip('?.,')
        
        return None
    
    def _extract_entity_name_from_question(self, question, keywords):
        """Extract entity name from question"""
        for keyword in keywords:
            if keyword in question:
                parts = question.split(keyword)
                if len(parts) > 1:
                    return parts[1].strip(' ?.,')
        return None
    
    def _get_oracle_context(self, row):
        """Get context about Oracle usage from row"""
        oracle_context = []
        for col in self.df.columns:
            if pd.notna(row[col]) and 'oracle' in str(row[col]).lower():
                oracle_context.append(f"{col}: {row[col]}")
        return ' | '.join(oracle_context[:2]) if oracle_context else None
    """Generate graph directly from Excel mapping"""
    
    def __init__(self):
        self.graph = nx.DiGraph()
        self.entities = {}
    
    def build_from_excel_data(self, data):
        """Build graph from direct Excel mapping"""
        entities = data.get('entities', [])
        relationships = data.get('relationships', [])
        
        st.write(f"### 🔨 Building Knowledge Graph")
        st.write(f"**Components:** {len(entities)} | **Relationships:** {len(relationships)}")
        
        # Add entities
        for entity in entities:
            self.entities[entity['id']] = entity
            self.graph.add_node(entity['id'], **entity)
        
        # Add relationships
        valid_rels = 0
        for rel in relationships:
            if rel['source'] in self.entities and rel['target'] in self.entities:
                self.graph.add_edge(rel['source'], rel['target'], **rel)
                valid_rels += 1
        
        # Show statistics
        node_types = {}
        for entity in entities:
            etype = entity.get('type', 'unknown')
            node_types[etype] = node_types.get(etype, 0) + 1
        
        st.write("**Component Types:**")
        for etype, count in node_types.items():
            st.write(f"• {etype.title()}: {count}")
        
        st.success(f"✅ Graph built: {len(self.entities)} nodes, {valid_rels} relationships")
    
    def generate_rich_visualization(self):
        """Generate rich visualization showing Excel data"""
        
        # Enhanced colors
        colors = {
            'application': '#FF6B6B',    # Red
            'server': '#4ECDC4',         # Teal  
            'database': '#45B7D1',       # Blue
            'network': '#96CEB4',        # Green
            'service': '#FFEAA7',        # Yellow
            'person': '#DDA0DD',         # Purple
            'location': '#FFA07A',       # Orange
            'organization': '#98D8C8',   # Mint
            'component': '#BDC3C7'       # Gray
        }
        
        net = Network(
            height="700px", 
            width="100%", 
            bgcolor="#f8f9fa", 
            font_color="black",
            directed=True
        )
        
        # Configure physics
        net.set_options("""
        {
          "physics": {
            "enabled": true,
            "stabilization": {"iterations": 200},
            "barnesHut": {
              "gravitationalConstant": -2000,
              "centralGravity": 0.1,
              "springLength": 150,
              "springConstant": 0.05,
              "damping": 0.09
            }
          }
        }
        """)
        
        # Add nodes with rich information
        for node_id, node_data in self.graph.nodes(data=True):
            entity_type = node_data.get('type', 'component')
            color = colors.get(entity_type, '#BDC3C7')
            label = node_data.get('label', node_id)
            
            # Create detailed hover info from Excel data
            properties = node_data.get('properties', {})
            hover_text = f"<div style='max-width: 300px; font-family: Arial;'>"
            hover_text += f"<h3 style='color: {color}; margin: 0;'>{label}</h3>"
            hover_text += f"<p><strong>Type:</strong> {entity_type.title()}</p>"
            
            if 'excel_row' in node_data:
                hover_text += f"<p><strong>Excel Row:</strong> {node_data['excel_row']}</p>"
            
            if properties:
                hover_text += "<p><strong>Details from Excel:</strong></p><ul>"
                for key, value in list(properties.items())[:5]:  # Show first 5 properties
                    clean_key = key.replace('_', ' ').title()
                    hover_text += f"<li><strong>{clean_key}:</strong> {value}</li>"
                hover_text += "</ul>"
            
            hover_text += "</div>"
            
            # Size based on connections
            connections = len(list(self.graph.neighbors(node_id)))
            size = max(30, min(60, 30 + connections * 5))
            
            net.add_node(
                node_id,
                label=label,
                color=color,
                title=hover_text,
                size=size,
                font={'size': 14, 'color': 'black'},
                borderWidth=2
            )
        
        # Add edges with relationship details
        edge_colors = {
            'manages': '#E74C3C',
            'located_in': '#2ECC71', 
            'belongs_to': '#3498DB',
            'depends_on': '#9B59B6',
            'supports': '#F39C12'
        }
        
        for source, target, edge_data in self.graph.edges(data=True):
            rel_type = edge_data.get('type', 'connected')
            edge_color = edge_colors.get(rel_type, '#7F8C8D')
            
            # Create edge hover info
            edge_props = edge_data.get('properties', {})
            edge_title = f"<strong>{rel_type.replace('_', ' ').title()}</strong><br>"
            if 'description' in edge_props:
                edge_title += edge_props['description']
            if 'source_column' in edge_props:
                edge_title += f"<br><small>From Excel column: {edge_props['source_column']}</small>"
            
            net.add_edge(
                source,
                target,
                label=rel_type.replace('_', ' '),
                color={'color': edge_color, 'opacity': 0.8},
                title=edge_title,
                arrows={'to': {'enabled': True, 'scaleFactor': 1.2}},
                width=3,
                font={'size': 12}
            )
        
        # Generate HTML with legend
        try:
            temp_filename = f"excel_graph_{uuid.uuid4().hex[:8]}.html"
            net.save_graph(temp_filename)
            
            with open(temp_filename, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # Add comprehensive legend
            legend_html = self._create_excel_legend(colors, edge_colors)
            html_content = html_content.replace('</body>', f'{legend_html}</body>')
            
            os.remove(temp_filename)
            return html_content
            
        except Exception as e:
            return f"<div style='padding: 20px; color: red;'>Visualization Error: {str(e)}</div>"
    
    def _create_excel_legend(self, colors, edge_colors):
        """Create comprehensive legend for Excel-based graph"""
        legend = """
        <div style="position: fixed; top: 10px; right: 10px; background: rgba(255,255,255,0.95); 
                    padding: 15px; border: 2px solid #333; border-radius: 10px; 
                    font-family: Arial; font-size: 12px; max-width: 250px; box-shadow: 0 4px 8px rgba(0,0,0,0.2);">
            <h3 style="margin: 0 0 10px 0; color: #333;">📊 Excel Knowledge Graph</h3>
            
            <div style="margin-bottom: 10px;">
                <strong>Component Types:</strong><br>
        """
        
        # Add component types
        for comp_type, color in colors.items():
            legend += f"""
                <div style="margin: 2px 0; display: flex; align-items: center;">
                    <div style="width: 12px; height: 12px; background: {color}; 
                               border-radius: 50%; margin-right: 6px; border: 1px solid #666;"></div>
                    <span>{comp_type.title()}</span>
                </div>
            """
        
        legend += """
            </div>
            
            <div style="margin-bottom: 10px;">
                <strong>Relationships:</strong><br>
        """
        
        # Add relationship types
        for rel_type, color in edge_colors.items():
            legend += f"""
                <div style="margin: 2px 0; display: flex; align-items: center;">
                    <div style="width: 16px; height: 2px; background: {color}; margin-right: 6px;"></div>
                    <span>{rel_type.replace('_', ' ').title()}</span>
                </div>
            """
        
        legend += f"""
            </div>
            
            <div style="border-top: 1px solid #ccc; padding-top: 8px; font-size: 11px; color: #666;">
                <strong>Graph Stats:</strong><br>
                • Nodes: {len(self.graph.nodes)}<br>
                • Edges: {len(self.graph.edges)}<br>
                • Source: Direct Excel mapping
            </div>
            
            <div style="margin-top: 8px; font-size: 10px; color: #888;">
                💡 Hover over nodes for Excel details<br>
                🖱️ Drag nodes to rearrange
            </div>
        </div>
        """
        
        return legend

def main():
    st.title("📊 Direct Excel Knowledge Graph")
    st.markdown("**Map your Excel data directly to knowledge graph - no LLM guessing!**")
    
    st.info("🎯 **How it works:** Each Excel row becomes a component. Columns like 'Owner', 'Location', 'Department' create automatic relationships.")
    
    # File upload
    st.header("📁 Upload Your Excel/CSV File")
    uploaded_file = st.file_uploader(
        "Choose your CMDB Excel file", 
        type=['csv', 'xlsx', 'xls'],
        help="Your Excel data will be mapped directly - each row becomes a component"
    )
    
    if uploaded_file:
        st.success(f"📄 **File loaded:** {uploaded_file.name}")
        
        try:
            # Read the file
            if uploaded_file.name.endswith('.csv'):
                df = pd.read_csv(uploaded_file)
            else:
                df = pd.read_excel(uploaded_file)
            
            st.write(f"**📋 Excel contains:** {len(df)} rows × {len(df.columns)} columns")
            
            # Process directly
            if st.button("🚀 Map Excel to Knowledge Graph", type="primary"):
                with st.spinner("Mapping your Excel data directly..."):
                    
                    # Direct mapping without LLM
                    mapper = DirectExcelMapper()
                    graph_data = mapper.process_excel(df)
                    
                    # Build and visualize
                    kg = DirectKnowledgeGraph()
                    kg.build_from_excel_data(graph_data)
                    
                    # Generate rich visualization
                    html_content = kg.generate_rich_visualization()
                    
                    # Create chat engine
                    chat_engine = ExcelChatEngine(graph_data['entities'], graph_data['relationships'], df)
                    
                    st.header("🕸️ Your Excel Knowledge Graph")
                    st.markdown("**🎯 This graph shows your actual Excel data with real business relationships**")
                    
                    # Display the graph
                    st.components.v1.html(html_content, height=750)
                    
                    # Chat Interface
                    st.header("💬 Ask Questions About Your Data")
                    st.markdown("**🤖 Ask natural language questions about your Excel components and relationships**")
                    
                    # Example questions
                    with st.expander("💡 Example Questions You Can Ask"):
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.markdown("""
                            **🔍 Technology Questions:**
                            - "What applications use Oracle?"
                            - "What software is common in applications?"
                            - "What uses MySQL?"
                            - "Search for Java"
                            
                            **👤 Management Questions:**
                            - "Who manages Web Server?"
                            - "What does John Smith manage?"
                            """)
                        
                        with col2:
                            st.markdown("""
                            **📍 Location & General:**
                            - "What is in DataCenter-A?"
                            - "Show all applications"
                            - "List all databases"
                            - "Show all servers"
                            
                            **🔎 Search Anything:**
                            - "Search for Linux"
                            - "Find components with Production"
                            """)
                    
                    # Chat input and response
                    question = st.text_input(
                        "🗣️ Ask your question:",
                        placeholder="e.g., What applications use Oracle?",
                        help="Ask about technologies, management, locations, or search for any term"
                    )
                    
                    if question:
                        with st.spinner("🔍 Analyzing your Excel data..."):
                            answer = chat_engine.answer_question(question)
                            
                            st.markdown("### 💬 Answer:")
                            st.markdown(answer)
                    
                    # Quick action buttons
                    st.markdown("### 🚀 Quick Questions")
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        if st.button("📊 Common Software"):
                            answer = chat_engine._find_common_software()
                            st.markdown("**Answer:**")
                            st.markdown(answer)
                    
                    with col2:
                        if st.button("🗄️ Database Usage"):
                            answer = chat_engine._find_database_usage()
                            st.markdown("**Answer:**")
                            st.markdown(answer)
                    
                    with col3:
                        if st.button("📋 All Applications"):
                            answer = chat_engine._show_all_by_type('application')
                            st.markdown("**Answer:**")
                            st.markdown(answer)
                    
                    with col4:
                        if st.button("💻 All Servers"):
                            answer = chat_engine._show_all_by_type('server')
                            st.markdown("**Answer:**")
                            st.markdown(answer)
                    
                    # Show extracted data summary
                    with st.expander("📋 View Extracted Components & Relationships"):
                        entities = graph_data.get('entities', [])
                        relationships = graph_data.get('relationships', [])
                        
                        col1, col2 = st.columns(2)
                        
                        with col1:
                            st.write("**🏷️ Components:**")
                            for entity in entities[:10]:
                                st.write(f"• **{entity['label']}** ({entity['type']}) - Row {entity.get('excel_row', '?')}")
                        
                        with col2:
                            st.write("**🔗 Relationships:**")
                            for rel in relationships[:10]:
                                source_name = next((e['label'] for e in entities if e['id'] == rel['source']), rel['source'])
                                target_name = next((e['label'] for e in entities if e['id'] == rel['target']), rel['target'])
                                st.write(f"• {source_name} **{rel['type']}** {target_name}")
                    
        except Exception as e:
            st.error(f"❌ **Error reading file:** {str(e)}")
            st.write("Please ensure your file is a valid Excel (.xlsx) or CSV (.csv) file.")

if __name__ == "__main__":
    main()
