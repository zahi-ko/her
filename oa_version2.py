import os
import tools
import logging

from model import llm
from typing import TypedDict

from langgraph.graph import END, START, StateGraph
from langchain_core.messages import SystemMessage, HumanMessage

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Get the desktop items
def init(*args, **kwargs):
    global step_mapping
    global desktop_items

    global JUDGE_INSTRUCTIONS, IMPROVE_INSTRUCTION

    logger.info("Initializing the system")

    desktop_items = tools.get_desktop_items("open")

    step_mapping = dict((
        (0, lambda *x, **y: desktop_items),
        (1, tools.get_by_everytools_search),
        (2, tools.get_by_windows_search),
    ))

    JUDGE_INSTRUCTIONS = """你是一个 AI 助手，负责判断用户请求的文件或文件夹是否在可疑列表中。任务如下：{task}。

    对于每个请求，请按照以下步骤操作：

    1. **检查是否可疑：**
    - 如果请求的文件或文件夹在可疑列表中，将变量 `satisfied` 设置为 `True`，并提供该文件或文件夹的 **确切路径**。
    - 如果请求的文件或文件夹 **不在** 可疑列表中，将 `satisfied` 设置为 `False`，并提供一个 **灵活的正则表达式**，该表达式可用于搜索该文件或文件夹。正则表达式应足够宽泛，以捕捉名称或路径中的变体，以匹配用户的请求，考虑到可能的措辞或命名规范的差异。
    - 请注意，用户提供的可能是目标文件或文件夹的常见变体，因此进行检查时要保持适当的灵活性，格外注意用户暗示的文件类型。

    2. **重要说明：**
    - 不要假设用户的意图总是精确的；正则表达式应允许文件或文件夹名称的常见变体（例如，通配符、不区分大小写、可能的拼写错误）。
    - 仅提供相关的输出（`satisfied` 和路径或正则表达式）。
    - 如果用户的请求不在可疑列表中，不要提供确切路径，只提供正则表达式。

    3. **输出格式：**
    - **确保 JudgeState 始终被正确初始化：**
        - 即使某些键值不必要，始终返回完全初始化的 JudgeState。这意味着你应该始终在响应中包含 `regex`、`satisfied` 和 `target_path` 键，即使它们的值为空或为默认值。这是为了避免 `KeyError`。

    4. **上下文策略：**
    - 理解用户请求的上下文，以生成合适的正则表达式：
        - 例如，如果用户请求的是 "文档"，正则表达式不应包含 "document" 这个词，而应专注于常见的文档文件类型（例如，.docx、.pdf、.txt 等）。
        - 如果用户请求的是带有常见扩展名或格式的文件，正则表达式应考虑该格式的变体（例如，.jpg 和 .jpeg 用于图像文件）。
        - 使用与请求文件类型相关的常见模式。例如：
        - 文档：`.*\.(docx|pdf|txt|odt|rtf).*`
        - 图像：`.*\.(jpg|jpeg|png|gif|bmp).*`
        - 可执行文件：`.*\.(exe|bat|msi|app).*`
        - 这有助于创建一个更灵活、更智能的正则表达式，适应不同的用户意图。
    """


    IMPROVE_INSTRUCTION = """
    你是一个 AI 助手，负责处理用户输入的连续任务文本，可能包含拼写错误，并将其转换为语义正确的文本。基于正确的文本生成一个能够被文件查找代理接受的请求。

    输入修正：修正用户输入中的拼写错误或语法不正确的部分。确保文本变得语义正确，并清晰地传达用户的意图。

    语义理解：理解修正后的文本的核心意图。如果用户请求的是某个程序（例如“打开微信”），识别文件查找代理应该搜索相应的应用程序或可执行文件。考虑上下文、同义词和常见用户请求。

    文件查找请求：将修正并理解后的文本转换为文件查找代理可理解的请求。确保请求简洁明了，聚焦于查找用户所提及的具体文件或文件夹（例如，程序、文档或安装文件夹）。

    输出格式：
    文件查找请求：一个简洁且明确的请求，文件查找代理可以理解并根据其执行。
    
    示例：
    用户输入： "你好我是小王我想亲你打开微信"
    文件查找请求： "请找到与微信相关的文件或文件夹，搜索系统中与微信相关的可执行文件或安装文件。"
    """

    return {"suspicious": desktop_items, "regex": "", "satisfied": False, "target_path": "", "current_step": 0}


class InputState(TypedDict):
    task: str

class OuputState(TypedDict):
    satisfied: bool

class OverallState(TypedDict):
    task: str
    regex: str
    satisfied: bool
    target_path: str
    current_step: int 
    suspicious: list[str]

class JudgeState(TypedDict):
    regex: str = ""
    satisfied: bool = False
    target_path: str = ""

def voice_to_text(state: OverallState) -> OverallState:
    logger.info("Converting voice to text")
    while text:= tools.recognize_speech_from_microphone():
        if text != None:
            break
    logger.debug(f"Recognized text: {text}")
    return {"task": text}

def text_improvement(state: OverallState) -> OverallState:
    logger.info("Improving text")
    improved = llm.invoke([SystemMessage(IMPROVE_INSTRUCTION)] + [HumanMessage(state["task"])])
    logger.debug(f"Improved text: {improved.content}")
    return {"task": improved}

def judge(state: OverallState) -> OverallState:
    logger.info("Judging the task")
    step = state["current_step"]
    results = step_mapping[step](state["regex"])
    state["current_step"] = step + 1
    state["suspicious"] = results

    system_messsage = JUDGE_INSTRUCTIONS.format(task=state['task'])
    prompt = f"The suspicious files are {state['suspicious']}."

    judger = llm.with_structured_output(JudgeState)
    judge = judger.invoke([SystemMessage(system_messsage)] + [HumanMessage(prompt)])
    
    info = "Judge result:\n"
    for key, value in judge.items():
        info += f"|{key}: {value}| "
    logger.debug(info)
    return {"satisfied": judge["satisfied"], "regex": judge["regex"], "target_path": judge["target_path"], "current_step": state["current_step"], "suspicious": state["suspicious"]}

def if_satisfied(state: OverallState) -> str:
    logger.info("Checking if satisfied")
    if state["satisfied"]:
        return "perform_task"
    if (state["current_step"] + 1) > 3:
        logger.warning("No more steps to perform")
        return END
    
    return "judge"

def perfomr_task(state: OverallState) -> OuputState:
    logger.info(f"Performing task: opening {state['target_path']}")
    os.startfile(state["target_path"])
    return {"satisfied": True}

graph = StateGraph(OverallState, input=InputState, output=OuputState)

graph.add_node("init", init)
graph.add_node("judge", judge)
graph.add_node("perform_task", perfomr_task)
graph.add_node("voice_to_text", voice_to_text)
graph.add_node("text_improvement", text_improvement)

graph.add_edge(START, "init")
graph.add_edge("init", "voice_to_text")
graph.add_edge("voice_to_text", "text_improvement")
graph.add_edge("text_improvement", "judge")
graph.add_conditional_edges("judge", if_satisfied)

graph = graph.compile()

states = graph.invoke({
    "task": "请帮我打开项目2报告",
})
