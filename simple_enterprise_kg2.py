# langgraph_poc.py

import streamlit as st
import pandas as pd
from docx import Document
import json
import base64
import re
import requests
from langgraph.graph import StateGraph
from pyvis.network import Network
import tempfile
import os
import streamlit.components.v1 as components

# =======================
# 🔧 LLM CONFIG
# =======================
LLM_API_URL = "https://your-llm-endpoint.com/v1/chat/completions"
LLM_USERNAME = "your_username_here"
LLM_PASSWORD = "your_password_here"

def get_basic_auth():
    creds = f"{LLM_USERNAME}:{LLM_PASSWORD}"
    return base64.b64encode(creds.encode()).decode()

# =======================
# 📄 TEXT EXTRACTORS
# =======================
def extract_text_from_file(file):
    if file.name.endswith(".xlsx"):
        df = pd.read_excel(file)
        return df.to_csv(index=False)
    elif file.name.endswith(".docx"):
        doc = Document(file)
        return "\n".join([p.text for p in doc.paragraphs if p.text.strip()])
    return ""

# =======================
# 🤖 LLM Nodes
# =======================
def llm_extract_graph(text):
    prompt = f"""
From the following document, extract entities and architecture relationships:

ENTITY TYPES:
- Application, Database, Component, Business Service, Environment, Application Server, Software, Data Lifecycle Function, Queue Manager, Security Function, Flow, Market Segment, Application Group, APQC, Sub Component

RELATIONSHIP TYPES:
- USES, RUNS_ON, SUPPORTS, PART_OF, STORES_DATA_IN, DEPLOYED_IN, ALIGNS_WITH, PROVIDES, CONTAINS, RELATED_TO

Document Text:
{text[:2000]}

Return only JSON in the format:
{{
  "nodes": [{{"id": "App1", "type": "Application"}}],
  "edges": [{{"source": "App1", "target": "DB1", "type": "USES"}}]
}}
"""
    headers = {
        "Authorization": f"Basic {get_basic_auth()}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You extract structured knowledge graph data. Return valid JSON only."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,
        "max_tokens": 600
    }
    response = requests.post(LLM_API_URL, headers=headers, json=payload)
    content = response.json()["choices"][0]["message"]["content"]
    match = re.search(r'{.*}', content, re.DOTALL)
    return json.loads(match.group()) if match else {"nodes": [], "edges": []}

def llm_arch_summary(text):
    prompt = f"""
Summarize this architecture:
- Identify key components
- Mention key risks or opportunities
- Keep it executive friendly

Architecture:
{text[:2000]}
"""
    headers = {
        "Authorization": f"Basic {get_basic_auth()}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "You provide strategic IT architecture summaries."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.4,
        "max_tokens": 400
    }
    response = requests.post(LLM_API_URL, headers=headers, json=payload)
    return response.json()["choices"][0]["message"]["content"]

# =======================
# 🔍 LangGraph Setup
# =======================
def build_graph_pipeline():
    g = StateGraph()

    def extract_step(state):
        text = extract_text_from_file(state["file"])
        return {"text": text}

    def extract_kg_step(state):
        return {"graph": llm_extract_graph(state["text"])}

    g.add_node("extract_text", extract_step)
    g.add_node("extract_kg", extract_kg_step)

    g.set_entry_point("extract_text")
    g.add_edge("extract_text", "extract_kg")
    g.set_finish_point("extract_kg")

    return g.compile()

# =======================
# 🌐 Visualization
# =======================
def show_graph(graph_data):
    net = Network(height="600px", width="100%", directed=True)
    net.toggle_physics(True)
    net.show_buttons(filter_=['nodes'])

    color_map = {
        "Application": "#6C5CE7",
        "Database": "#00B894",
        "Component": "#FAB1A0",
        "Business Service": "#E17055",
        "Environment": "#74B9FF",
        "Software": "#FF7675",
        "Flow": "#55EFC4",
        "Queue Manager": "#81ECEC",
        "Security Function": "#FD79A8",
        "Application Server": "#636E72",
        "Market Segment": "#D63031",
        "APQC": "#FDCB6E",
        "Sub Component": "#A29BFE",
        "Application Group": "#00CEC9",
        "Data Lifecycle Function": "#E84393"
    }

    for node in graph_data.get("nodes", []):
        color = color_map.get(node.get("type", ""), "#BDC3C7")
        net.add_node(node["id"], label=node["id"], title=node.get("type", ""), color=color)

    for edge in graph_data.get("edges", []):
        net.add_edge(edge["source"], edge["target"], label=edge["type"])

    with tempfile.NamedTemporaryFile(delete=False, suffix=".html") as f:
        net.save_graph(f.name)
        html = open(f.name, "r", encoding="utf-8").read()
        components.html(html, height=650)
        os.unlink(f.name)

# =======================
# 🖼️ Streamlit UI
# =======================
def main():
    st.title("🔗 Knowledge Graph POC (with LangGraph)")
    uploaded = st.file_uploader("📁 Upload Excel or Word Document", type=["xlsx", "docx"], key="doc_upload")

    if uploaded:
        with st.spinner("🔍 Processing through LangGraph pipeline..."):
            graph_pipeline = build_graph_pipeline()
            output = graph_pipeline.invoke({"file": uploaded})
            kg = output["graph"]
            text = extract_text_from_file(uploaded)

        st.success("✅ Knowledge graph generated!")
        show_graph(kg)

        node_ids = [n['id'] for n in kg.get("nodes", [])]
        selected_node = st.selectbox("🔍 Select a node to view details", node_ids)

        if selected_node:
            node_info = next((n for n in kg["nodes"] if n["id"] == selected_node), None)
            related_edges = [e for e in kg["edges"] if e["source"] == selected_node or e["target"] == selected_node]

            st.subheader(f"📌 Details for: {selected_node}")
            if node_info:
                st.write(f"**Type:** {node_info.get('type', 'Unknown')}")
            st.write("**Connections:**")
            for rel in related_edges:
                direction = "→" if rel["source"] == selected_node else "←"
                other = rel["target"] if rel["source"] == selected_node else rel["source"]
                st.write(f"{selected_node} {direction} {rel['type']} {direction} {other}")

        if st.button("🧠 Generate Strategic Summary"):
            with st.spinner("Calling LLM for summary..."):
                summary = llm_arch_summary(text)
                st.subheader("🧠 Strategic Architecture Summary")
                st.markdown(summary)

        st.download_button("📥 Download Graph as JSON", json.dumps(kg, indent=2), file_name="knowledge_graph.json")

        # Chat interface
        st.markdown("---")
        st.subheader("💬 Ask Questions about the Architecture")
        user_question = st.text_input("Type your question:", placeholder="e.g., What are the critical components?")

        if user_question:
            prompt = f"""
Answer the following question based on this architecture document:

Document Text:
{text[:2000]}

Question: {user_question}

Respond concisely and insightfully.
"""
            headers = {
                "Authorization": f"Basic {get_basic_auth()}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {"role": "system", "content": "You are an architecture expert assistant."},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.4,
                "max_tokens": 400
            }
            with st.spinner("Thinking..."):
                response = requests.post(LLM_API_URL, headers=headers, json=payload)
                answer = response.json()["choices"][0]["message"]["content"]
                st.markdown(f"**Answer:**\n\n{answer}")

if __name__ == "__main__":
    main()
