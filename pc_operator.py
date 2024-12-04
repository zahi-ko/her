# -*- coding: utf-8 -*-

"""
File: pc_operator.py
Author: Zahi
Date: 2024-11-27
Description: 
    This module provides functionality to simulate various keyboard and mouse operations 
    using the pyautogui library. It defines an Operation class for specifying operation 
    details and a simulate_operation function to execute the operations. The module includes 
    support for clicking, scrolling, writing input, pressing keys, and moving the cursor, 
    along with comprehensive logging and validation to ensure reliable and controlled 
    automation tasks.
"""
import logging
from typing import Literal
import pyautogui as pg
from pydantic import BaseModel, Field, field_validator

SUPPORTED_OPERATIONS = ("nop", "click", "double_click", "scroll", "write_input", "press_keys", "move")

# Create a logger for this module
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

file_handler = logging.FileHandler("pc_operator.log")
file_handler.setFormatter(formatter)

stream_handler = logging.StreamHandler()
stream_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(stream_handler)

class Operation(BaseModel):
    """Simulate keyboard and mouse operations."""

    #! Be careful since JSON not support tuple, so we use list instead.
    coord: list[int, int] = Field([0, 0], description="The coordinate where the operation will be performed.")
    scroll_clicks: int = Field(0, description="The number of clicks to scroll with pyauotgui in Windows, positive for up and negative for down.")
    duration: float = Field(0., description="The duration of the operation in seconds.")
    operation: Literal[*SUPPORTED_OPERATIONS] = Field("nop", description="The operation to be performed.")
    content: str = Field("", description="The content to be written when the operation is 'write_input'.")
    keys: list[str] = Field("", description="The keys to be pressed", examples=[["ctrl", "alt", "shift", "esc"], ["c",]])

    @field_validator("operation")
    def check_operation(cls, value: str):
        if value not in SUPPORTED_OPERATIONS:
            logger.error(f"Unsupported operation: {value}, program terminated.")
            raise ValueError(f"Operation '{value}' not supported.")
        return value

    @field_validator("keys")
    def check_keys(cls, value: list[str]):
        for key in value:
            if key not in pg.KEYBOARD_KEYS:
                logger.error(f"Unsupported key: {key}, program terminated.")
                raise ValueError(f"Key '{key}' not supported.")
        return value


def simulate_operation(operation: Operation) -> None:
    """
    **Simulate the given operation.**  
    This function takes an Operation object and simulates the specified operation by performing actions such as clicks,
    scrolls, writing input, and key presses. It logs the execution details and returns True upon successful completion.
    Parameters:
        operation (Operation): The operation to simulate, containing details such as operation type, coordinates,
                               duration, scroll clicks, content, keys, etc.
    Raises:
        ValueError: If an unexpected operation type is encountered.
    """
    oper_type = operation.operation
    logger.info(f"Simulating operation: {oper_type}")

    #TODO Validate if the relevant fields are filled and legal.
    # Assign the operation to the corresponding function.
    match oper_type:
        case "nop":
            logger.debug("No operation performed.")
            pass
        case "click":
            logger.debug(f"Performing click at {operation.coord} with duration {operation.duration}.")
            pg.click(*operation.coord, duration=operation.duration)
        case "double_click":
            logger.debug(f"Performing double click at {operation.coord} with duration {operation.duration}.")
            pg.doubleClick(*operation.coord, duration=operation.duration)
        case "scroll":
            logger.debug(f"Scrolling {'up' if operation.scroll_clicks > 0 else 'down'} by {abs(operation.scroll_clicks)} clicks.")
            pg.scroll(operation.scroll_clicks)
        case "write_input":
            logger.debug(f"Writing input: {operation.content}.")
            pg.write(operation.content)
        case "press_keys":
            logger.debug(f"Pressing keys: {operation.keys}.")
            pg.press(operation.keys)
        case "move":
            logger.debug(f"Moving to {operation.coord} with duration {operation.duration}.")
            pg.moveTo(*operation.coord, duration=operation.duration)
        case _:
            #! This should not happen.
            logger.error("Unexpected execution, program terminated.")
            raise ValueError("Unexpected execution.")
        
    logger.info(f"Operation {oper_type} completed.")

def screenshot(filename: str = "screenshot.png") -> str:
    """
    **Take a screenshot of the current screen.**  
    This function uses the pyautogui library to take a screenshot of the current screen and save it to a file.
    Returns:
        str: The filename of the saved screenshot.
    """
    logger.info("Taking screenshot.")
    pg.screenshot(filename)
    logger.info(f"Screenshot saved as {filename}.")

    return filename

if __name__ == "__main__":
    simulate_operation(Operation(coord=[120, 340], operation="double_click", duration=0.5))
    # print("This module is not meant to be executed.")
