from pydantic import BaseModel, Field, field_validator
from pc_operator import Operation, simulate_operation

from langgraph.graph import START, END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

class OperationState(BaseModel):
    operations: list[Operation] = Field([], description="The list of operations to be performed.")


workflow = StateGraph(OperationState)

workflow.add_node("screenshot", lambda: 0)
workflow.add_node("assistant", lambda: 0)
workflow.add_node("operate", lambda: 0)

workflow.add_edge(START, "screenshot")
workflow.add_edge("screenshot", "assistant")
workflow.add_conditional_edges("assistant", tools_condition)
workflow.add_edge("operate", "screenshot")

graph = workflow.compile()
