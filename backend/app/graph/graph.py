from __future__ import annotations

from typing import Any

from langgraph.graph import END, StateGraph

from app.graph.nodes import (
    analyze_node,
    blocked_node,
    final_guardrail_node,
    findings_node,
    initial_guardrail_node,
    load_dataset_node,
    plan_node,
    profile_node,
    quality_node,
    report_node,
    route_after_input_guardrail,
    route_after_output_guardrail,
)
from app.graph.state import AnalysisState


def build_analysis_graph(
    checkpointer: Any = None,
):
    builder = StateGraph(AnalysisState)

    # ---------------------------------------------------------
    # Nodes
    # ---------------------------------------------------------

    builder.add_node(
        "initial_guardrail",
        initial_guardrail_node,
    )

    builder.add_node(
        "load_dataset",
        load_dataset_node,
    )

    builder.add_node(
        "plan",
        plan_node,
    )

    builder.add_node(
        "profile",
        profile_node,
    )

    builder.add_node(
        "quality",
        quality_node,
    )

    builder.add_node(
        "analyze",
        analyze_node,
    )

    builder.add_node(
        "findings",
        findings_node,
    )

    builder.add_node(
        "report",
        report_node,
    )

    builder.add_node(
        "final_guardrail",
        final_guardrail_node,
    )

    builder.add_node(
        "blocked",
        blocked_node,
    )

    # ---------------------------------------------------------
    # Entry
    # ---------------------------------------------------------

    builder.set_entry_point(
        "initial_guardrail"
    )

    # ---------------------------------------------------------
    # Input guardrail
    # ---------------------------------------------------------

    builder.add_conditional_edges(
        "initial_guardrail",
        route_after_input_guardrail,
        {
            "load_dataset": "load_dataset",
            "blocked": "blocked",
        },
    )

    # ---------------------------------------------------------
    # Dataset loading
    # ---------------------------------------------------------

    builder.add_edge(
        "load_dataset",
        "plan",
    )

    # ---------------------------------------------------------
    # Main analysis pipeline
    # ---------------------------------------------------------

    builder.add_edge(
        "plan",
        "profile",
    )

    builder.add_edge(
        "profile",
        "quality",
    )

    builder.add_edge(
        "quality",
        "analyze",
    )

    builder.add_edge(
        "analyze",
        "findings",
    )

    builder.add_edge(
        "findings",
        "report",
    )

    builder.add_edge(
        "report",
        "final_guardrail",
    )

    # ---------------------------------------------------------
    # Blocked path
    # ---------------------------------------------------------

    builder.add_edge(
        "blocked",
        END,
    )

    # ---------------------------------------------------------
    # Output guardrail
    # ---------------------------------------------------------

    builder.add_conditional_edges(
        "final_guardrail",
        route_after_output_guardrail,
        {
            "end": END,
            "blocked": "blocked",
        },
    )

    return builder.compile(
        checkpointer=checkpointer,
    )