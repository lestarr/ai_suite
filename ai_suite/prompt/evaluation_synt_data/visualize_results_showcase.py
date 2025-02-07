import streamlit as st
import pandas as pd
import json
from pathlib import Path
from extraction.evaluation.eval_result_collection import EvalResultCollector

def load_data():
    """Load evaluation data from files"""
    # Load JSON evaluation files
    eval_files = {
        "bank_statement_jan_2024": "bank_statement_jan_2024_eval.json",
        "transaction_log_q1": "transaction_log_q1_eval.json"
    }
    
    raw_results = []
    for name, filename in eval_files.items():
        with open(Path("extraction/prompt/evaluation_synt_data") / filename) as f:
            raw_results.append(json.load(f))
    
    # Load statistics CSVs
    field_stats = pd.read_csv("extraction/prompt/evaluation_synt_data/financial_docs_field_stats.csv")
    doc_stats = pd.read_csv("extraction/prompt/evaluation_synt_data/financial_docs_document_stats.csv")
    
    return field_stats, doc_stats, raw_results

def show_summary_metrics(field_stats: pd.DataFrame, doc_stats: pd.DataFrame):
    """Display overall summary metrics"""
    st.header("Summary")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Documents", len(doc_stats))
    
    with col2:
        total_evals = field_stats["total"].sum()
        st.metric("Total Evaluations", f"{total_evals:,}")
    
    with col3:
        avg_accuracy = (field_stats["correct"].sum() / total_evals * 100)
        st.metric("Overall Accuracy", f"{avg_accuracy:.1f}%")
    
    with col4:
        missing_rate = (field_stats["missing"].sum() / total_evals * 100)
        st.metric("Missing Rate", f"{missing_rate:.1f}%")

def show_field_stats(field_stats: pd.DataFrame):
    """Display field-level statistics"""
    st.header("Field-level Statistics")
    
    # Sort by accuracy
    field_stats = field_stats.sort_values("accuracy", ascending=False)
    
    # Create bar chart using streamlit
    st.bar_chart(field_stats.set_index("field")["accuracy"])
    
    # Show detailed stats
    st.dataframe(field_stats.style.format({
        "accuracy": "{:.1f}%",
        "total": "{:,.0f}",
        "correct": "{:,.0f}",
        "missing": "{:,.0f}"
    }))

def show_document_stats(doc_stats: pd.DataFrame):
    """Display document-level statistics"""
    st.header("Document-level Statistics")
    
    # Sort by accuracy
    doc_stats = doc_stats.sort_values("accuracy", ascending=False)
    
    # Create bar chart using streamlit
    st.bar_chart(doc_stats.set_index("document")["accuracy"])
    
    # Show detailed stats
    st.dataframe(doc_stats.style.format({
        "accuracy": "{:.1f}%",
        "total": "{:,.0f}",
        "correct": "{:,.0f}",
        "missing": "{:,.0f}"
    }))

def show_raw_results(raw_results: list):
    """Display raw evaluation results"""
    st.header("Raw Evaluation Results")
    
    # Allow selecting a document
    selected_doc = st.selectbox(
        "Select Document",
        ["bank_statement_jan_2024", "transaction_log_q1"]
    )
    
    # Show results for selected document
    result = next(r for r in raw_results 
                 if selected_doc in r["metadata"]["test_file"])
    
    # Show metadata
    st.subheader("Metadata")
    st.json(result["metadata"])
    
    # Show evaluations
    st.subheader("Field Evaluations")
    for eval_item in result["results"]["ground_truth_evaluations"]:
        with st.expander(f"Field: {eval_item['field_name_ground_truth']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write("Ground Truth Value:")
                st.code(eval_item["ground_truth_entity_core_value"])
            with col2:
                st.write("Test Value:")
                st.code(eval_item["test_entity_core_value"])
            
            for eval_result in eval_item["evaluations"]:
                st.write("---")
                status = "✅" if eval_result["entity_info_correct"] else "❌"
                st.write(f"Status: {status}")
                if eval_result["entity_info_missing"]:
                    st.warning("Missing Information")
                st.write("Details:", eval_result["examples_for_wrong_or_correct"])

def show_comparison_metrics(runs: dict[str, tuple[pd.DataFrame, pd.DataFrame, list]]):
    """Display comparison of summary metrics between runs"""
    st.header("Summary Comparison")
    
    metrics = []
    for run_name, (field_stats, doc_stats, _) in runs.items():
        total_evals = field_stats["total"].sum()
        avg_accuracy = (field_stats["correct"].sum() / total_evals * 100)
        missing_rate = (field_stats["missing"].sum() / total_evals * 100)
        
        metrics.append({
            "run": run_name,
            "documents": len(doc_stats),
            "evaluations": total_evals,
            "accuracy": avg_accuracy,
            "missing_rate": missing_rate
        })
    
    metrics_df = pd.DataFrame(metrics)
    
    # Show metrics side by side
    cols = st.columns(len(runs))
    for i, (run_name, metrics) in enumerate(zip(runs.keys(), metrics)):
        with cols[i]:
            st.subheader(run_name)
            st.metric("Documents", f"{metrics_df.loc[i, 'documents']:,}")
            st.metric("Evaluations", f"{metrics_df.loc[i, 'evaluations']:,}")
            st.metric("Accuracy", f"{metrics_df.loc[i, 'accuracy']:.1f}%")
            st.metric("Missing Rate", f"{metrics_df.loc[i, 'missing_rate']:.1f}%")

def show_field_comparison(runs: dict[str, tuple[pd.DataFrame, pd.DataFrame, list]]):
    """Compare field-level statistics between runs"""
    st.header("Field-level Comparison")
    
    # Show accuracy comparison charts
    st.subheader("Accuracy by Field")
    cols = st.columns(len(runs))
    for i, (run_name, (field_stats, _, _)) in enumerate(runs.items()):
        with cols[i]:
            st.write(f"**{run_name}**")
            chart_df = field_stats.sort_values("accuracy", ascending=False)
            st.bar_chart(chart_df.set_index("field")["accuracy"])
    
    # Show accuracy comparison table
    st.subheader("Field Accuracy Comparison")
    accuracy_df = pd.concat([
        field_stats[["field", "accuracy"]].assign(run=run_name)
        for run_name, (field_stats, _, _) in runs.items()
    ])
    pivot_accuracy = accuracy_df.pivot(index="field", columns="run", values="accuracy")
    st.dataframe(pivot_accuracy.style.format("{:.1f}%"))
    
    # Show detailed metrics table
    st.subheader("Detailed Field Metrics")
    metrics_df = pd.concat([
        field_stats[["field", "total", "correct", "missing"]].assign(run=run_name)
        for run_name, (field_stats, _, _) in runs.items()
    ])
    pivot_metrics = metrics_df.pivot(index="field", columns="run", 
                                   values=["total", "correct", "missing"])
    st.dataframe(pivot_metrics.style.format("{:,.0f}"))

def show_document_comparison(runs: dict[str, tuple[pd.DataFrame, pd.DataFrame, list]]):
    """Compare document-level statistics between runs"""
    st.header("Document-level Comparison")
    
    # Show accuracy comparison charts
    st.subheader("Accuracy by Document")
    cols = st.columns(len(runs))
    for i, (run_name, (_, doc_stats, _)) in enumerate(runs.items()):
        with cols[i]:
            st.write(f"**{run_name}**")
            chart_df = doc_stats.sort_values("accuracy", ascending=False)
            st.bar_chart(chart_df.set_index("document")["accuracy"])
    
    # Show accuracy comparison table
    st.subheader("Document Accuracy Comparison")
    accuracy_df = pd.concat([
        doc_stats[["document", "accuracy"]].assign(run=run_name)
        for run_name, (_, doc_stats, _) in runs.items()
    ])
    pivot_accuracy = accuracy_df.pivot(index="document", columns="run", values="accuracy")
    st.dataframe(pivot_accuracy.style.format("{:.1f}%"))
    
    # Show detailed metrics table
    st.subheader("Detailed Document Metrics")
    metrics_df = pd.concat([
        doc_stats[["document", "total", "correct", "missing"]].assign(run=run_name)
        for run_name, (_, doc_stats, _) in runs.items()
    ])
    pivot_metrics = metrics_df.pivot(index="document", columns="run", 
                                   values=["total", "correct", "missing"])
    st.dataframe(pivot_metrics.style.format("{:,.0f}"))

def main():
    st.set_page_config(page_title="Financial Document Evaluation Results")
    st.title("Financial Document Evaluation Results")
    
    try:
        field_stats, doc_stats, raw_results = load_data()
    except Exception as e:
        st.error(f"Failed to load data: {str(e)}")
        return
    
    # Show different views
    tab1, tab2, tab3, tab4 = st.tabs(["Summary", "Field Stats", "Document Stats", "Raw Results"])
    
    with tab1:
        show_summary_metrics(field_stats, doc_stats)
    with tab2:
        show_field_stats(field_stats)
    with tab3:
        show_document_stats(doc_stats)
    with tab4:
        show_raw_results(raw_results)

if __name__ == "__main__":
    main()

# Run with: streamlit run extraction/prompt/evaluation_synt_data/visualize_results_showcase.py 