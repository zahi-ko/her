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
import pyautogui as pg
from pydantic import BaseModel, Field, field_validator

SUPPORTED_OPERATIONS = ("nop", "click", "right_click", "left_click", "scroll", "write_input", "press_keys", "move")

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("pc_operator.log"),
        logging.StreamHandler()
    ]
)

class Operation(BaseModel):
    """Simulate keyboard and mouse operations."""
    coord: tuple[int, int] = Field((0, 0), description="The coordinate where the operation will be performed.")
    scroll_clicks: int = Field(0, description="The number of clicks to scroll with pyauotgui in Windows, positive for up and negative for down.")
    duration: int = Field(0, description="The duration of the operation in seconds.")
    operation: str = Field("nop", description="The operation to be performed.")
    content: str = Field("", description="The content to be written when the operation is 'write_input'.")
    keys: list[str] = Field("", description="The keys to be pressed", examples=[["ctrl", "alt", "shift", "esc"], ["c",]])

    @field_validator("operation")
    def check_operation(cls, value: str):
        if value not in SUPPORTED_OPERATIONS:
            logging.error(f"Unsupported operation: {value}, program terminated.")
            raise ValueError(f"Operation '{value}' not supported.")
        return value

    @field_validator("keys")
    def check_keys(cls, value: list[str]):
        for key in value:
            if key not in pg.KEYBOARD_KEYS:
                logging.error(f"Unsupported key: {key}, program terminated.")
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
    logging.info(f"Simulating operation: {oper_type}")

    #TODO Validate if the relevant fields are filled and legal.
    # Assign the operation to the corresponding function.
    match oper_type:
        case "nop":
            logging.debug("No operation performed.")
            pass
        case "click":
            logging.debug(f"Performing click at {operation.coord} with duration {operation.duration}.")
            pg.click(*operation.coord, duration=operation.duration)
        case "right_click":
            logging.debug(f"Performing right click at {operation.coord} with duration {operation.duration}.")
            pg.rightClick(*operation.coord, duration=operation.duration)
        case "left_click":
            logging.debug(f"Performing left click at {operation.coord} with duration {operation.duration}.")
            pg.leftClick(*operation.coord, duration=operation.duration)
        case "scroll":
            logging.debug(f"Scrolling {'up' if operation.scroll_clicks > 0 else 'down'} by {abs(operation.scroll_clicks)} clicks.")
            pg.scroll(operation.scroll_clicks)
        case "write_input":
            logging.debug(f"Writing input: {operation.content}.")
            pg.write(operation.content)
        case "press_keys":
            logging.debug(f"Pressing keys: {operation.keys}.")
            pg.press(operation.keys)
        case "move":
            logging.debug(f"Moving to {operation.coord} with duration {operation.duration}.")
            pg.moveTo(*operation.coord, duration=operation.duration)
        case _:
            #! This should not happen.
            logging.error("Unexpeted execution, program terminated.")
            raise ValueError("Unexpected execution.")
        
    logging.info(f"Operation {oper_type} completed.")

if __name__ == "__main__":
    print("This module is not meant to be executed.")