import streamlit as st

st.set_page_config(page_title="📊 Complete Knowledge Graph System", layout="wide")

import pandas as pd
import requests
import base64
import json
import networkx as nx
from pyvis.network import Network
import os
import uuid

# ========================================
# 🔧 CONFIGURE YOUR LLM CREDENTIALS HERE
# ========================================
LLM_API_URL = "https://your-api-endpoint.com/v1/chat/completions"
LLM_USERNAME = "your_username_here"
LLM_PASSWORD = "your_password_here"
# ========================================

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
            if idx >= 50:  # Reasonable limit
                st.warning(f"⚠️ Processing limited to first 50 rows to maintain performance")
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
        """Answer questions about the Excel data using in-memory search"""
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
        
        # Search questions
        elif any(phrase in question_lower for phrase in ['search', 'find', 'contains']):
            search_term = self._extract_search_term(question_lower)
            if search_term:
                return self._search_excel_data(search_term)
        
        # Fallback with suggestions
        else:
            return self._provide_suggestions()
    
    def _find_oracle_usage(self):
        """Find applications that use Oracle - IN-MEMORY SEARCH"""
        oracle_users = []
        
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
        """Find common software/technologies - IN-MEMORY ANALYSIS"""
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
        """Find database usage - IN-MEMORY SEARCH"""
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
        """Find what uses specific technology - IN-MEMORY SEARCH"""
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
    
    def _search_excel_data(self, search_term):
        """Search through Excel data - IN-MEMORY SEARCH"""
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
    
    def _show_all_by_type(self, component_type):
        """Show all components of specific type - IN-MEMORY FILTER"""
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

🔎 **Search:**
• "Search for [any term]"
• "Find components with [keyword]"

💡 **Tip:** Use the exact names from your Excel data for best results!"""
    
    # Helper methods
    def _get_component_name_from_row(self, row):
        """Extract component name from Excel row"""
        name_columns = [col for col in self.df.columns if any(keyword in col.lower() 
                       for keyword in ['name', 'title', 'component', 'asset', 'system', 'application'])]
        
        for col in name_columns:
            if pd.notna(row[col]) and str(row[col]).strip():
                return str(row[col]).strip()
        
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
    
    def _extract_search_term(self, question):
        """Extract search term from question"""
        search_indicators = ['search for', 'find', 'search', 'contains']
        for indicator in search_indicators:
            if indicator in question:
                parts = question.split(indicator)
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
    
    def _find_who_manages(self, entity_name):
        """Find who manages entity - RELATIONSHIP LOOKUP"""
        managers = []
        for rel in self.relationships:
            if rel['type'] == 'manages':
                target_entity = self.entities.get(rel['target'])
                if target_entity and entity_name.lower() in target_entity['label'].lower():
                    manager_entity = self.entities.get(rel['source'])
                    if manager_entity:
                        managers.append({
                            'manager': manager_entity['label'],
                            'entity': target_entity['label']
                        })
        
        if managers:
            result = f"👤 **Management for '{entity_name}':**\n\n"
            for mgr in managers:
                result += f"• **{mgr['manager']}** manages **{mgr['entity']}**\n"
            return result
        else:
            return f"❌ **No management information found for '{entity_name}'**"
    
    def _extract_person_name_from_question(self, question):
        """Extract person name from 'what does X manage' questions"""
        if 'what does' in question and 'manage' in question:
            start = question.find('what does') + 9
            end = question.find('manage')
            return question[start:end].strip()
        return None
    
    def _find_what_person_manages(self, person_name):
        """Find what person manages - RELATIONSHIP LOOKUP"""
        managed = []
        for rel in self.relationships:
            if rel['type'] == 'manages':
                manager_entity = self.entities.get(rel['source'])
                if manager_entity and person_name.lower() in manager_entity['label'].lower():
                    target_entity = self.entities.get(rel['target'])
                    if target_entity:
                        managed.append(target_entity['label'])
        
        if managed:
            result = f"👤 **{person_name} manages:**\n\n"
            for item in managed:
                result += f"• {item}\n"
            return result
        else:
            return f"❌ **No management info found for {person_name}**"
    
    def _extract_location_name(self, question):
        """Extract location name from question"""
        location_indicators = ['what is in', 'in', 'location', 'datacenter', 'site']
        for indicator in location_indicators:
            if indicator in question:
                parts = question.split(indicator)
                if len(parts) > 1:
                    return parts[1].strip(' ?.,')
        return None
    
    def _find_in_location(self, location_name):
        """Find components in location - RELATIONSHIP LOOKUP"""
        components = []
        for rel in self.relationships:
            if rel['type'] == 'located_in':
                location_entity = self.entities.get(rel['target'])
                if location_entity and location_name.lower() in location_entity['label'].lower():
                    component_entity = self.entities.get(rel['source'])
                    if component_entity:
                        components.append(component_entity['label'])
        
        if components:
            result = f"📍 **Components in {location_name}:**
