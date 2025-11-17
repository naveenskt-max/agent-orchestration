import streamlit as st
import httpx
import json
import time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# Configure page
st.set_page_config(
    page_title="AI Agent Orchestration Platform",
    page_icon="🤖",
    layout="wide"
)

# Initialize session state
if "plan" not in st.session_state:
    st.session_state.plan = None
if "execution_result" not in st.session_state:
    st.session_state.execution_result = None
if "agents" not in st.session_state:
    st.session_state.agents = []
if "current_tab" not in st.session_state:
    st.session_state.current_tab = "Planning"

# Header
st.title("🤖 AI Agent Orchestration Platform")
st.markdown("Intelligent workflow planning with gap analysis and guided agent development")

# Service URLs from environment variables
REGISTRY_URL = os.getenv("REGISTRY_URL", "http://localhost:8000")
PLANNER_URL = os.getenv("PLANNER_URL", "http://localhost:8100")
EXECUTOR_URL = os.getenv("EXECUTOR_URL", "http://localhost:8200")
OBSERVABILITY_URL = os.getenv("OBSERVABILITY_URL", "http://localhost:8300")

# Service Health Check
def check_service_health():
    services = {
        "Registry": REGISTRY_URL,
        "Planner": PLANNER_URL,
        "Executor": EXECUTOR_URL,
        "Observability": OBSERVABILITY_URL
    }
    
    status = {}
    for name, url in services.items():
        try:
            response = httpx.get(f"{url}/health", timeout=2.0)
            status[name] = "🟢 Online" if response.status_code == 200 else "🔴 Error"
        except:
            status[name] = "🔴 Offline"
    
    return status

# Load agents from registry
def load_agents():
    try:
        response = httpx.get(f"{REGISTRY_URL}/list_agents", timeout=5.0)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []

# Load observability metrics
def load_observability_metrics():
    try:
        response = httpx.get(f"{OBSERVABILITY_URL}/metrics", timeout=5.0)
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return None

# Load traces
def load_traces(limit=50):
    try:
        response = httpx.get(f"{OBSERVABILITY_URL}/traces?limit={limit}", timeout=5.0)
        if response.status_code == 200:
            return response.json()["traces"]
    except:
        pass
    return []

# Load events
def load_events(limit=100):
    try:
        response = httpx.get(f"{OBSERVABILITY_URL}/events?limit={limit}", timeout=5.0)
        if response.status_code == 200:
            return response.json()["events"]
    except:
        pass
    return []

# Sidebar for agent management
with st.sidebar:
    st.header("🔧 System Status")
    
    # Display service status
    health_status = check_service_health()
    for service, status in health_status.items():
        st.metric(service, status)
    
    st.divider()
    
    # Load and display agents
    if st.button("🔄 Refresh Agents"):
        st.session_state.agents = load_agents()
        if st.session_state.agents:
            st.success(f"Loaded {len(st.session_state.agents)} agents")
        else:
            st.error("Failed to load agents")
    
    if st.session_state.agents:
        st.subheader("📋 Available Agents")
        for agent in st.session_state.agents:
            with st.expander(f"🔹 {agent['name']}"):
                st.markdown(f"**Description:** {agent['description']}")
                st.markdown(f"**Endpoint:** `{agent['endpoint']}`")

# Main content with tabs
tab1, tab2, tab3 = st.tabs(["🎯 Planning", "📊 Observability", "🔍 Trace Viewer"])

with tab1:
    st.header("🎯 Plan Your Workflow")

    # Example goals
    example_goals = [
        "Create a weekly sales intelligence report with competitor analysis",
        "Generate a market analysis dashboard with trend visualization", 
        "Analyze customer feedback and create improvement recommendations",
        "Produce a competitive landscape report with data visualizations"
    ]

    # Goal input
    goal = st.text_area(
        "Enter your business goal:",
        value=example_goals[0],
        height=100,
        help="Describe what you want to accomplish using the available agents"
    )

    # Show examples
    with st.expander("💡 More Example Goals"):
        for i, example in enumerate(example_goals[1:], 2):
            st.write(f"{i}. {example}")

    # Generate Plan button
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("🚀 Generate Plan", type="primary", disabled=not goal.strip()):
            with st.spinner("🤔 Analyzing goal and generating strategies..."):
                try:
                    start_time = time.time()
                    response = httpx.post(f"{PLANNER_URL}/plan", json={"goal": goal}, timeout=30.0)
                    response.raise_for_status()
                    st.session_state.plan = response.json()
                    st.session_state.execution_result = None
                    
                    planning_time = round((time.time() - start_time) * 1000)
                    st.success(f"✅ Plan generated in {planning_time}ms!")
                    
                except httpx.RequestError as e:
                    st.error("🔌 Connection error: Unable to reach planner service")
                    st.code(str(e))
                except httpx.HTTPStatusError as e:
                    st.error(f"📋 Planner error: {e.response.status_code}")
                    st.code(e.response.text)
                except Exception as e:
                    st.error(f"❌ Unexpected error: {str(e)}")

    with col2:
        if st.button("🗑️ Clear All"):
            st.session_state.plan = None
            st.session_state.execution_result = None
            st.session_state.agents = []
            st.rerun()

    # Display plan details (existing code continues...)
    if st.session_state.plan:
        st.divider()
        plan = st.session_state.plan
        
        # Plan summary
        col_coverage, col_status, col_strategies = st.columns(3)
        
        coverage = plan.get("coverage", 0)
        status = plan.get("status", "unknown")
        strategies = plan.get("alternative_approaches_tried", 0)
        
        with col_coverage:
            st.metric("Coverage", f"{coverage * 100:.0f}%")
        with col_status:
            status_icon = "🟢" if status == "complete" else "🟡"
            st.metric("Status", f"{status_icon} {status.title()}")
        with col_strategies:
            st.metric("Strategies Tried", strategies)
        
        # Status message
        if status == "complete":
            st.success("🎉 Complete plan generated! All required capabilities are available.")
            plan_steps = plan.get("plan", [])
        else:
            st.warning("🔍 Partial plan generated. Some capabilities are missing.")
            plan_steps = plan.get("achievable_plan", [])
        
        # Display plan steps
        if plan_steps:
            st.subheader("📋 Execution Plan")
            
            for step in plan_steps:
                with st.container():
                    st.markdown("---")
                    col_step, col_details = st.columns([1, 3])
                    
                    with col_step:
                        st.markdown(f"### Step {step['step']}")
                    
                    with col_details:
                        agent_name = step.get('agent_name', 'Unknown')
                        task = step.get('task', 'No task description')
                        confidence = step.get('confidence', 'unknown')
                        
                        # Confidence indicator
                        confidence_colors = {
                            'high': '🟢',
                            'medium': '🟡',
                            'low': '🔴'
                        }
                        confidence_icon = confidence_colors.get(confidence, '⚪')
                        
                        st.markdown(f"**🤖 {agent_name}** {confidence_icon}")
                        st.markdown(f"*{task}*")
                        st.markdown(f"**Confidence:** {confidence.title()}")
        
        # Display gaps
        if plan.get("gaps"):
            st.subheader("🚧 Capability Gaps")
            
            for i, gap in enumerate(plan["gaps"], 1):
                with st.expander(f"Gap {i}: {gap.get('required_capability', 'Unknown Capability')}", expanded=True):
                    st.markdown(f"**📍 At Step:** {gap.get('at_step', 'Unknown')}")
                    st.markdown(f"**📝 Description:** {gap.get('description', 'No description')}")
                    
                    # Suggested agent card
                    if 'suggested_agent_card' in gap:
                        agent_card = gap['suggested_agent_card']
                        st.markdown("**💡 Suggested Agent Implementation:**")
                        
                        col_name, col_complexity = st.columns(2)
                        with col_name:
                            st.code(f"Name: {agent_card.get('name', 'unnamed_agent')}")
                        with col_complexity:
                            hints = agent_card.get('implementation_hints', {})
                            complexity = hints.get('complexity', 'unknown')
                            st.code(f"Complexity: {complexity.title()}")
                        
                        st.markdown("**Description:**")
                        st.markdown(agent_card.get('description', 'No description'))
                        
                        # Implementation hints
                        if hints:
                            st.markdown("**🛠️ Implementation Details:**")
                            if 'suggested_libraries' in hints:
                                st.code(f"Libraries: {', '.join(hints['suggested_libraries'])}")
                            if 'estimated_effort' in hints:
                                st.code(f"Estimated Effort: {hints['estimated_effort']}")
            
            # Recommendation
            if plan.get("recommendation"):
                st.info(f"💡 **Recommendation:** {plan['recommendation']}")
        
        # Execution section
        st.divider()
        st.subheader("⚡ Execute Plan")
        
        col_exec, col_retry = st.columns([2, 1])
        
        with col_exec:
            if st.button("🚀 Execute Plan", type="primary"):
                plan_to_execute = plan_steps
                
                with st.spinner("🔄 Executing workflow steps..."):
                    try:
                        start_time = time.time()
                        response = httpx.post(
                            f"{EXECUTOR_URL}/execute_workflow",
                            json={"plan": plan_to_execute},
                            timeout=60.0
                        )
                        response.raise_for_status()
                        st.session_state.execution_result = response.json()
                        
                        execution_time = round((time.time() - start_time) * 1000)
                        st.success(f"✅ Execution completed in {execution_time}ms!")
                        
                    except httpx.RequestError as e:
                        st.error("🔌 Connection error: Unable to reach executor service")
                        st.code(str(e))
                    except httpx.HTTPStatusError as e:
                        st.error(f"⚡ Executor error: {e.response.status_code}")
                        st.code(e.response.text)
                    except Exception as e:
                        st.error(f"❌ Unexpected error: {str(e)}")
        
        with col_retry:
            max_retries = st.number_input("Max Retries", min_value=0, max_value=10, value=3)
            if st.button("🔄 Execute with Retries"):
                plan_to_execute = plan_steps
                
                with st.spinner(f"🔄 Executing with up to {max_retries} retries..."):
                    try:
                        response = httpx.post(
                            f"{EXECUTOR_URL}/execute_workflow",
                            json={"plan": plan_to_execute, "max_retries": max_retries},
                            timeout=120.0
                        )
                        response.raise_for_status()
                        st.session_state.execution_result = response.json()
                        st.success("✅ Execution completed!")
                        
                    except Exception as e:
                        st.error(f"❌ Execution failed: {str(e)}")

    # Display execution results
    if st.session_state.execution_result:
        st.divider()
        result = st.session_state.execution_result
        
        if result.get("status") == "success":
            st.success("🎉 Workflow executed successfully!")
            
            # Execution summary
            col_status, col_steps = st.columns(2)
            with col_status:
                st.metric("Final Status", "✅ Success")
            with col_steps:
                trace = result.get("execution_trace", [])
                st.metric("Steps Completed", len(trace))
            
            # Execution trace
            if trace:
                st.subheader("📊 Execution Trace")
                
                for step in trace:
                    with st.expander(f"Step {step['step']}: {step['agent']}", expanded=True):
                        col_info, col_timing = st.columns([3, 1])
                        
                        with col_info:
                            st.markdown(f"**Agent:** {step['agent']}")
                            st.markdown(f"**Status:** {step.get('status', 'unknown')}")
                            if 'error' in step:
                                st.error(f"**Error:** {step['error']}")
                        
                        with col_timing:
                            if 'duration_ms' in step:
                                st.metric("Duration", f"{step['duration_ms']}ms")
                        
                        # Show output
                        if 'output' in step and step['output']:
                            with st.expander("View Output", expanded=False):
                                st.json(step['output'])
            
            # Final output
            if result.get("final_output"):
                st.subheader("📋 Final Output")
                with st.expander("View Complete Context", expanded=False):
                    st.json(result["final_output"])
        
        else:
            st.error("❌ Workflow execution failed")
            
            # Failure details
            if "failed_step" in result:
                st.markdown(f"**Failed at Step:** {result['failed_step']}")
                st.markdown(f"**Failed Agent:** {result['failed_agent']}")
            
            if "error" in result:
                st.markdown("**Error Details:**")
                st.code(result["error"])
            
            # Partial trace
            if "execution_trace" in result:
                st.subheader("📊 Partial Execution Trace")
                for step in result["execution_trace"]:
                    with st.expander(f"Step {step['step']}: {step['agent']}"):
                        st.json(step)

with tab2:
    st.header("📊 Observability Dashboard")
    
    # Auto-refresh option
    auto_refresh = st.checkbox("🔄 Auto-refresh (10s)", value=False)
    if auto_refresh:
        st.rerun()
    
    # Load metrics
    metrics = load_observability_metrics()
    
    if metrics:
        # System Metrics
        st.subheader("🖥️ System Metrics")
        sys_metrics = metrics.get("system_metrics", {})
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Requests", sys_metrics.get("requests_total", 0))
        with col2:
            st.metric("Success Rate", f"{sys_metrics.get('success_rate', 0):.1f}%")
        with col3:
            st.metric("Avg Latency", f"{sys_metrics.get('avg_latency_ms', 0):.0f}ms")
        with col4:
            st.metric("Active Agents", sys_metrics.get("active_agents", 0))
        
        # Planning Metrics
        st.subheader("🧠 Planning Quality")
        plan_metrics = metrics.get("planning_metrics", {})
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Avg Coverage", f"{plan_metrics.get('avg_coverage', 0):.1%}")
        with col2:
            st.metric("Gap Detection Rate", f"{plan_metrics.get('gap_detection_rate', 0):.1f}%")
        with col3:
            st.metric("Total Planning Attempts", plan_metrics.get('total_planning_attempts', 0))
        
        # Agent Performance
        st.subheader("🤖 Agent Performance")
        agent_metrics = metrics.get("agent_metrics", [])
        
        if agent_metrics:
            # Create DataFrame for visualization
            df = pd.DataFrame(agent_metrics)
            
            # Performance table
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Agent Performance Table:**")
                st.dataframe(df[["name", "invocations", "success_rate", "avg_latency_ms"]], 
                           use_container_width=True)
            
            with col2:
                # Invocations bar chart
                st.markdown("**Agent Invocations:**")
                fig = px.bar(df, x="name", y="invocations", title="Invocations per Agent")
                st.plotly_chart(fig, use_container_width=True)
                
                # Latency chart
                st.markdown("**Agent Latency:**")
                fig2 = px.bar(df, x="name", y="avg_latency_ms", title="Avg Latency per Agent")
                st.plotly_chart(fig2, use_container_width=True)
        
        # Recent Events
        st.subheader("📜 Recent Events")
        events = metrics.get("recent_events", [])
        
        if events:
            # Create DataFrame for events
            events_df = pd.DataFrame(events)
            if not events_df.empty:
                events_df['timestamp'] = pd.to_datetime(events_df['timestamp'])
                events_df = events_df.sort_values('timestamp', ascending=False)
                
                # Event type filter
                event_types = events_df['event_type'].unique().tolist()
                selected_event_type = st.selectbox("Filter by Event Type", ["All"] + event_types)
                
                if selected_event_type != "All":
                    filtered_events = events_df[events_df['event_type'] == selected_event_type]
                else:
                    filtered_events = events_df
                
                # Display events
                for _, event in filtered_events.head(10).iterrows():
                    with st.expander(f"{event['event_type']} - {event['timestamp']}", expanded=False):
                        st.json(event['data'])
    else:
        st.warning("⚠️ Observability service not available. Make sure it's running on port 8300.")

with tab3:
    st.header("🔍 Trace Viewer")
    
    # Load traces
    traces = load_traces()
    
    if traces:
        # Trace selection
        trace_options = [f"{trace.get('goal', 'Unknown Goal')} - {trace.get('status', 'unknown')}" 
                      for trace in traces]
        selected_trace_idx = st.selectbox("Select Trace", range(len(trace_options)), 
                                       format_func=lambda x: trace_options[x])
        
        if selected_trace_idx is not None:
            selected_trace = traces[selected_trace_idx]
            
            # Trace details
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Trace ID", selected_trace.get('trace_id', 'Unknown')[:8] + "...")
            with col2:
                st.metric("Duration", f"{selected_trace.get('duration_ms', 0):.0f}ms")
            with col3:
                status = selected_trace.get('status', 'unknown')
                status_icon = "🟢" if status == "success" else "🔴"
                st.metric("Status", f"{status_icon} {status.title()}")
            
            # Goal
            st.subheader("🎯 Goal")
            st.markdown(f"**{selected_trace.get('goal', 'No goal specified')}**")
            
            # Timeline visualization
            st.subheader("📈 Execution Timeline")
            spans = selected_trace.get('spans', [])
            
            if spans:
                # Create timeline data
                timeline_data = []
                for i, span in enumerate(spans):
                    timeline_data.append({
                        'start': i,
                        'duration': span.get('duration_ms', 0) / 1000,  # Convert to seconds for better visualization
                        'operation': span.get('operation', 'Unknown'),
                        'service': span.get('service', 'Unknown')
                    })
                
                timeline_df = pd.DataFrame(timeline_data)
                
                # Create Gantt chart
                fig = px.timeline(
                    timeline_df, 
                    x_start="start", 
                    x_end="start + duration", 
                    y="operation",
                    color="service",
                    title="Trace Timeline"
                )
                st.plotly_chart(fig, use_container_width=True)
                
                # Span details
                st.subheader("📋 Span Details")
                for span in spans:
                    with st.expander(f"{span.get('operation', 'Unknown')} ({span.get('service', 'Unknown')})", expanded=False):
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown(f"**Operation:** {span.get('operation', 'Unknown')}")
                            st.markdown(f"**Service:** {span.get('service', 'Unknown')}")
                            st.markdown(f"**Duration:** {span.get('duration_ms', 0):.0f}ms")
                        with col2:
                            st.markdown(f"**Status:** {span.get('status', 'Unknown')}")
                            
                            # Attributes
                            attributes = span.get('attributes', {})
                            if attributes:
                                st.markdown("**Attributes:**")
                                st.json(attributes)
    else:
        st.warning("⚠️ No traces available. Execute some workflows to see traces here.")

# Footer
st.divider()
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666;'>"
    "🤖 AI Agent Orchestration Platform | Built with FastAPI, Google ADK, and Streamlit"
    "</div>", 
    unsafe_allow_html=True
)