import base64
from typing import Literal
from pydantic import BaseModel, Field, FilePath
from pc_operator import Operation, simulate_operation

from langgraph.graph import START, StateGraph, END
# from langgraph.prebuilt import ToolNode, tools_condition

from langchain_core.messages import SystemMessage, HumanMessage

import pc_operator as po
import pyautogui as pg
from model import llm

GRAPH_VERSION = "1.0.0"
WINDOW_RESOLUTION = pg.size()

analyze_instructions = """You are an AI tasked with analyzing a screenshot taken in Windows with the resolution of {resolution} to determine if a given task has been completed. Your responsibilities are:

1. Analyze the screenshot to determine whether the task can be completed.
2. Analyze the screenshot to determine whether the task has already been completed.
3. If the task is not completed, provide actionable sets of instructions to propel the task toward completion based on what is visible in the screenshot. The instructions should only include actions that can be performed directly from the screenshot.
4. Do not assume any steps beyond what is visible in the screenshot.
5. If the task requires multiple steps and not all of them are visible in the screenshot, only provide the sets of actionable steps that can be taken immediately.
Remeber, you should be very careful about the coordinates of the operations, as they are based on the resolution of the screenshot.
"""

def encode_image(image_path: str) -> str:
    with open(image_path, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode("utf-8")
    return encoded_image


"""Define the state classes"""
class OverallState(BaseModel):
    operations: list[Operation] = Field([], description="The list of operations to be performed.")
    screenshot: FilePath = Field("", description="The path to the screenshot.")
    task: str = Field("", description="The task to be performed.")
    completed: bool = Field(False, description="The status of the task.")
    completable: bool = Field(True, description="Whether the task can be completed.")

class AnalyzeState(BaseModel):
    operations: list[Operation] = Field([], description="The list of operations to be performed.")
    completed: bool = Field(False, description="The status of the task.")
    completable: bool = Field(True, description="Whether the task can be completed.")

class InputState(BaseModel):
    task: str = Field("", description="The task to be performed.")

class OutputState(BaseModel):
    completed: bool = Field(False, description="The status of the task.")


"""Define the relevant nodes"""
def capture_screen(state: InputState) -> OverallState:
    shotname = po.screenshot()
    return {"screenshot": shotname, }

def analyze_screenshot(state: OverallState) -> OverallState:
    prompt = f"Please analyze this screenshot to determine if the task '{state.task}' has been completed."
    img = encode_image(state.screenshot)
    human_message = HumanMessage(content=[
        {"type": "text", "text": prompt},
        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img}"}},
    ])

    system_messages = analyze_instructions.format(resolution=WINDOW_RESOLUTION)
    structured_llm = llm.with_structured_output(AnalyzeState)

    analysis = structured_llm.invoke([SystemMessage(system_messages)] + [human_message])

    return {"operations": analysis.operations, "completed": analysis.completed, "completable": analysis.completable}

def judge_if_completed(state: OverallState) -> Literal["operate", END]: # type: ignore
    if state.completed or not state.completable:
        return END
    return "operate"

def operate(state: OverallState) -> OverallState:
    if state.operations:
        for operation in state.operations:
            simulate_operation(operation)
    
    # clear the operations after execution
    return {"operations": ()}


"""Build the graph"""
workflow = StateGraph(OverallState, input=InputState, output=OutputState)

workflow.add_node("capture_screen", capture_screen)
workflow.add_node("analyze_screenshot", analyze_screenshot)
workflow.add_node("operate", operate)

workflow.add_edge(START, "capture_screen")
workflow.add_edge("capture_screen", "analyze_screenshot")
workflow.add_conditional_edges("analyze_screenshot", judge_if_completed)
workflow.add_edge("operate", "capture_screen")

graph = workflow.compile()

states = graph.invoke({
    "task": "打开微信",
})