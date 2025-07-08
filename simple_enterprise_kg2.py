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
import tempfile

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
    
    def _find_technology_stack(self):
        """Find technology stack overview"""
        tech_keywords = {
            'Database': ['oracle', 'mysql', 'sql server', 'postgres', 'mongodb', 'redis'],
            'Programming': ['java', 'python', '.net', 'c#', 'javascript', 'php'],
            'Web Server': ['apache', 'nginx', 'iis', 'tomcat'],
            'Operating System': ['linux', 'windows', 'unix', 'solaris'],
            'Cloud/Container': ['docker', 'kubernetes', 'aws', 'azure', 'gcp']
        }
        
        tech_usage = {}
        
        for category, keywords in tech_keywords.items():
            tech_usage[category] = {}
            for idx, row in self.df.iterrows():
                row_text = " ".join([str(val) for val in row.values if pd.notna(val)]).lower()
                component_name = self._get_component_name_from_row(row)
                
                for tech in keywords:
                    if tech in row_text:
                        if tech not in tech_usage[category]:
                            tech_usage[category][tech] = []
                        tech_usage[category][tech].append(component_name)
        
        result = "🛠️ **Technology Stack Overview:**\n\n"
        
        for category, techs in tech_usage.items():
            if techs:
                result += f"**{category}:**\n"
                for tech, components in techs.items():
                    result += f"  • {tech.title()}: {len(components)} component(s)\n"
                result += "\n"
        
        return result if any(tech_usage.values()) else "❌ **No technology stack patterns found** in your data"
    
    def _provide_suggestions(self):
        """Provide helpful suggestions for questions"""
        return """❓ **I didn't understand that question. Try asking:**

🔍 **Technology Questions:**
• "What applications use Oracle?"
• "What software is common in applications?"
• "What uses MySQL?"
• "Search for Java"
• "Show technology stack"

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
            result = f"📍 **Components in {location_name}:**\n\n"
            for comp in components:
                result += f"• {comp}\n"
            return result
        else:
            return f"❌ **No components found in {location_name}**"

class KnowledgeGraphVisualizer:
    """Generate interactive knowledge graph visualizations"""
    
    def __init__(self):
        self.colors = {
            'application': '#FF6B6B',
            'server': '#4ECDC4', 
            'database': '#45B7D1',
            'network': '#96CEB4',
            'service': '#FFEAA7',
            'person': '#DDA0DD',
            'location': '#98D8C8',
            'organization': '#F7DC6F',
            'component': '#AED6F1',
            'default': '#BDC3C7'
        }
    
    def create_graph(self, entities, relationships, height=600):
        """Create interactive network graph using pyvis"""
        
        # Create network
        net = Network(height=f"{height}px", width="100%", bgcolor="#ffffff", font_color="black")
        net.set_options("""
        var options = {
          "physics": {
            "enabled": true,
            "stabilization": {"iterations": 100}
          }
        }
        """)
        
        # Add nodes
        for entity in entities:
            color = self.colors.get(entity.get('type', 'default'), self.colors['default'])
            size = self._calculate_node_size(entity, relationships)
            
            title = self._create_node_tooltip(entity)
            
            net.add_node(
                entity['id'],
                label=entity['label'],
                color=color,
                size=size,
                title=title,
                font={'size': 12}
            )
        
        # Add edges
        for rel in relationships:
            edge_color = self._get_edge_color(rel['type'])
            net.add_edge(
                rel['source'], 
                rel['target'],
                label=rel['type'].replace('_', ' ').title(),
                color=edge_color,
                width=2,
                title=rel.get('properties', {}).get('description', rel['type'])
            )
        
        return net
    
    def _calculate_node_size(self, entity, relationships):
        """Calculate node size based on connections"""
        connections = 0
        entity_id = entity['id']
        
        for rel in relationships:
            if rel['source'] == entity_id or rel['target'] == entity_id:
                connections += 1
        
        # Base size 20, +5 for each connection, max 50
        return min(20 + (connections * 5), 50)
    
    def _create_node_tooltip(self, entity):
        """Create detailed tooltip for node"""
        tooltip = f"<b>{entity['label']}</b><br>"
        tooltip += f"Type: {entity.get('type', 'Unknown').title()}<br>"
        
        if 'excel_row' in entity:
            tooltip += f"Excel Row: {entity['excel_row']}<br>"
        
        properties = entity.get('properties', {})
        if properties:
            tooltip += "<br><b>Properties:</b><br>"
            for key, value in list(properties.items())[:5]:  # Show first 5 properties
                clean_key = key.replace('_', ' ').title()
                tooltip += f"{clean_key}: {value}<br>"
        
        return tooltip
    
    def _get_edge_color(self, relationship_type):
        """Get color for relationship type"""
        edge_colors = {
            'manages': '#E74C3C',
            'located_in': '#3498DB',
            'belongs_to': '#9B59B6',
            'uses': '#F39C12',
            'connects_to': '#27AE60',
            'depends_on': '#E67E22',
            'default': '#95A5A6'
        }
        return edge_colors.get(relationship_type, edge_colors['default'])

def create_sample_data():
    """Create sample data for testing"""
    sample_data = {
        'Component Name': ['Web Server 1', 'Database Server', 'Email System', 'File Server', 'Backup System'],
        'Type': ['Application', 'Database', 'Application', 'Server', 'Service'],
        'Owner': ['John Smith', 'Jane Doe', 'Bob Wilson', 'Alice Brown', 'John Smith'],
        'Location': ['DataCenter-A', 'DataCenter-A', 'DataCenter-B', 'DataCenter-A', 'DataCenter-B'],
        'Department': ['IT', 'IT', 'Operations', 'IT', 'Operations'],
        'Technology': ['Apache, Linux', 'Oracle, Linux', 'Exchange, Windows', 'Windows Server', 'Veeam, Windows'],
        'Status': ['Active', 'Active', 'Active', 'Maintenance', 'Active']
    }
    return pd.DataFrame(sample_data)

def main():
    """Main Streamlit application"""
    
    st.title("📊 Complete Knowledge Graph System")
    st.write("Transform your Excel data into an interactive knowledge graph and chat with your data!")
    
    # Initialize session state
    if 'graph_data' not in st.session_state:
        st.session_state.graph_data = None
    if 'chat_engine' not in st.session_state:
        st.session_state.chat_engine = None
    if 'original_df' not in st.session_state:
        st.session_state.original_df = None
    
    # Sidebar
    with st.sidebar:
        st.header("📋 Data Source")
        
        data_source = st.radio(
            "Choose your data source:",
            ["📁 Upload Excel File", "🔧 Use Sample Data"]
        )
        
        if data_source == "📁 Upload Excel File":
            uploaded_file = st.file_uploader(
                "Choose Excel file", 
                type=['xlsx', 'xls', 'csv'],
                help="Upload your Excel or CSV file containing component data"
            )
            
            if uploaded_file is not None:
                try:
                    if uploaded_file.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file)
                    else:
                        df = pd.read_excel(uploaded_file)
                    
                    st.success(f"✅ File loaded: {len(df)} rows, {len(df.columns)} columns")
                    
                    if st.button("🔄 Process Data"):
                        with st.spinner("Processing Excel data..."):
                            mapper = DirectExcelMapper()
                            st.session_state.graph_data = mapper.process_excel(df)
                            st.session_state.chat_engine = ExcelChatEngine(
                                st.session_state.graph_data['entities'],
                                st.session_state.graph_data['relationships'],
                                df
                            )
                            st.session_state.original_df = df
                            st.success("🎉 Knowledge graph created!")
                            st.rerun()
                            
                except Exception as e:
                    st.error(f"❌ Error reading file: {str(e)}")
        
        else:  # Sample data
            st.info("📖 Using sample IT infrastructure data")
            if st.button("🔄 Load Sample Data"):
                with st.spinner("Creating sample knowledge graph..."):
                    df = create_sample_data()
                    mapper = DirectExcelMapper()
                    st.session_state.graph_data = mapper.process_excel(df)
                    st.session_state.chat_engine = ExcelChatEngine(
                        st.session_state.graph_data['entities'],
                        st.session_state.graph_data['relationships'],
                        df
                    )
                    st.session_state.original_df = df
                    st.success("🎉 Sample knowledge graph created!")
                    st.rerun()
    
    # Main content
    if st.session_state.graph_data is None:
        st.info("👆 Please upload an Excel file or use sample data to get started!")
        
        # Show preview of what the system can do
        st.write("### 🚀 What this system can do:")
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**📈 Knowledge Graph Features:**")
            st.write("• Automatic component detection")
            st.write("• Relationship mapping")
            st.write("• Interactive visualization")
            st.write("• Type-based categorization")
            
        with col2:
            st.write("**💬 Chat Capabilities:**")
            st.write("• Technology usage analysis")
            st.write("• Management relationships")
            st.write("• Location-based queries")
            st.write("• Search and discovery")
        
        return
    
    # Tabs for different views
    tab1, tab2, tab3, tab4 = st.tabs(["🌐 Knowledge Graph", "💬 Chat with Data", "📊 Analytics", "📋 Raw Data"])
    
    with tab1:
        st.header("🌐 Interactive Knowledge Graph")
        
        # Graph controls
        col1, col2, col3 = st.columns(3)
        with col1:
            height = st.slider("Graph Height", 400, 800, 600, 50)
        with col2:
            show_stats = st.checkbox("Show Statistics", True)
        with col3:
            download_graph = st.button("💾 Download Graph Data")
        
        if download_graph:
            graph_json = json.dumps(st.session_state.graph_data, indent=2)
            st.download_button(
                label="📥 Download as JSON",
                data=graph_json,
                file_name="knowledge_graph.json",
                mime="application/json"
            )
        
        # Create and display graph
        try:
            visualizer = KnowledgeGraphVisualizer()
            net = visualizer.create_graph(
                st.session_state.graph_data['entities'],
                st.session_state.graph_data['relationships'],
                height
            )
            
            # Save to temporary file and display
            with tempfile.NamedTemporaryFile(delete=False, suffix='.html') as tmp_file:
                net.save_graph(tmp_file.name)
                with open(tmp_file.name, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                st.components.v1.html(html_content, height=height+50)
                os.unlink(tmp_file.name)
            
        except Exception as e:
            st.error(f"❌ Error creating graph: {str(e)}")
            st.info("💡 Try installing required packages: pip install pyvis networkx")
        
        # Statistics
        if show_stats:
            st.write("### 📊 Graph Statistics")
            entities = st.session_state.graph_data['entities']
            relationships = st.session_state.graph_data['relationships']
            
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Entities", len(entities))
            with col2:
                st.metric("Total Relationships", len(relationships))
            with col3:
                entity_types = {}
                for entity in entities:
                    entity_type = entity.get('type', 'unknown')
                    entity_types[entity_type] = entity_types.get(entity_type, 0) + 1
                st.metric("Entity Types", len(entity_types))
            with col4:
                rel_types = set(rel['type'] for rel in relationships)
                st.metric("Relationship Types", len(rel_types))
            
            # Entity type breakdown
            st.write("**Entity Types:**")
            for entity_type, count in sorted(entity_types.items()):
                st.write(f"• {entity_type.title()}: {count}")
    
    with tab2:
        st.header("💬 Chat with Your Data")
        
        if st.session_state.chat_engine is None:
            st.warning("⚠️ Please process your data first!")
            return
        
        # Chat interface
        st.write("Ask questions about your data! Try these examples:")
        
        # Example questions
        examples = [
            "What applications use Oracle?",
            "Show all servers",
            "What software is common?",
            "Who manages the database?",
            "Search for Linux"
        ]
        
        cols = st.columns(len(examples))
        for i, example in enumerate(examples):
            with cols[i]:
                if st.button(f"💡 {example}", key=f"example_{i}"):
                    st.session_state.current_question = example
        
        # Question input
        question = st.text_input(
            "Your Question:", 
            value=st.session_state.get('current_question', ''),
            placeholder="Type your question here..."
        )
        
        if question:
            with st.spinner("🔍 Analyzing your data..."):
                try:
                    answer = st.session_state.chat_engine.answer_question(question)
                    st.markdown(answer)
                except Exception as e:
                    st.error(f"❌ Error processing question: {str(e)}")
        
        # Chat history could be added here
        with st.expander("💡 Question Ideas"):
            st.write("""
            **Technology Questions:**
            • "What applications use [technology]?"
            • "What software is common?"
            • "Show technology stack"
            
            **Management:**
            • "Who manages [component]?"
            • "What does [person] manage?"
            
            **Location:**
            • "What is in [location]?"
            • "Show all locations"
            
            **Search:**
            • "Search for [term]"
            • "Find [keyword]"
            
            **Listing:**
            • "Show all applications"
            • "List all servers"
            """)
    
    with tab3:
        st.header("📊 Data Analytics")
        
        if st.session_state.original_df is None:
            st.warning("⚠️ No data available for analysis!")
            return
        
        df = st.session_state.original_df
        
        # Basic statistics
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("### 📈 Data Overview")
            st.write(f"**Total Records:** {len(df)}")
            st.write(f"**Columns:** {len(df.columns)}")
            st.write(f"**Data Types:**")
            for dtype in df.dtypes.value_counts().items():
                st.write(f"• {dtype[0]}: {dtype[1]} columns")
        
        with col2:
            st.write("### 🔍 Missing Data")
            missing_data = df.isnull().sum()
            if missing_data.sum() > 0:
                for col, missing in missing_data.items():
                    if missing > 0:
                        percentage = (missing / len(df)) * 100
                        st.write(f"• {col}: {missing} ({percentage:.1f}%)")
            else:
                st.write("✅ No missing data found!")
        
        # Column analysis
        st.write("### 📋 Column Analysis")
        selected_column = st.selectbox("Select column to analyze:", df.columns)
        
        if selected_column:
            col_data = df[selected_column].dropna()
            
            if col_data.dtype == 'object':
                # Text analysis
                value_counts = col_data.value_counts().head(10)
                st.write(f"**Top values in {selected_column}:**")
                st.bar_chart(value_counts)
                
                st.write("**Value distribution:**")
                for value, count in value_counts.items():
                    percentage = (count / len(col_data)) * 100
                    st.write(f"• {value}: {count} ({percentage:.1f}%)")
            else:
                # Numeric analysis
                st.write(f"**Statistics for {selected_column}:**")
                st.write(col_data.describe())
    
    with tab4:
        st.header("📋 Raw Data")
        
        if st.session_state.original_df is None:
            st.warning("⚠️ No data available!")
            return
        
        df = st.session_state.original_df
        
        # Data preview
        st.write("### 👀 Data Preview")
        
        # Filters
        col1, col2 = st.columns(2)
        with col1:
            show_rows = st.number_input("Rows to show:", 1, len(df), min(50, len(df)))
        with col2:
            search_term = st.text_input("Search in data:", placeholder="Enter search term...")
        
        # Apply search filter
        display_df = df.copy()
        if search_term:
            # Search across all columns
            mask = display_df.astype(str).apply(lambda x: x.str.contains(search_term, case=False, na=False)).any(axis=1)
            display_df = display_df[mask]
            st.write(f"📍 Found {len(display_df)} rows containing '{search_term}'")
        
        # Display data
        st.dataframe(display_df.head(show_rows), use_container_width=True)
        
        # Download options
        st.write("### 💾 Download Options")
        col1, col2 = st.columns(2)
        
        with col1:
            csv_data = df.to_csv(index=False)
            st.download_button(
                "📥 Download as CSV",
                csv_data,
                "knowledge_graph_data.csv",
                "text/csv"
            )
        
        with col2:
            if st.session_state.graph_data:
                graph_json = json.dumps(st.session_state.graph_data, indent=2)
                st.download_button(
                    "📥 Download Graph JSON",
                    graph_json,
                    "knowledge_graph.json",
                    "application/json"
                )

if __name__ == "__main__":
    main()
