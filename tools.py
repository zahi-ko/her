import math
import os
import struct
import winreg
import everytools
import pyautogui
import time
import speech_recognition as sr

from typing import TypedDict


def recognize_speech_from_microphone():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        print("请开始说话...")
        audio = r.listen(source)
    try:
        text = r.recognize_google(audio, language='zh-CN')
        print("识别结果：" + text)
        return text
    except sr.UnknownValueError:
        print("无法识别")
        return None
    except sr.RequestError as e:
        print("请求错误：" + str(e))
        return None

class DesktopItem(TypedDict):
    entry_name: str
    index: int
    position: list[int, int]

class Item(TypedDict):
    """
    A dictionary representing an item with a name and a path.

    Attributes:
        name (str): The name of the item.
        path (str): The file path of the item.
    """
    name: str
    path: str

ICON_SIZE = (93, 89)

def _get_reg_value(sub_key=r"Software\Microsoft\Windows\Shell\Bags\1\Desktop"):
    with winreg.ConnectRegistry(None, winreg.HKEY_CURRENT_USER) as aReg:
        with winreg.OpenKey(aReg, sub_key) as aKey:
            _, value, _ = winreg.EnumValue(aKey, 9)

    return value

def _read_reg_value(value, mode):
    offset = 0x10
    number_of_items = struct.unpack_from("<I", value[offset:],8)[0]

    offset += 12
    desktop_items = []
    for x in range(number_of_items):
        uint32_filesize = struct.unpack_from("<I", value[offset:],4)[0]
        offset += 12
        entry_name = value[offset:(offset + (2 * uint32_filesize - 8))].decode('utf-16-le')
        offset += (2 * uint32_filesize - 4)

        if mode == "click":
            item = DesktopItem(entry_name=entry_name, index=x, position=[0, 0])
        else:
            item = Item(name=entry_name, path=os.path.join(os.path.expanduser(r"~\Desktop"), entry_name))

        desktop_items.append(item)
    if mode != "click": return desktop_items

    mapping = generate_mapping(number_of_items)
    offs = len(value)
    for x in range(number_of_items):
        offs -= 10
        item_tuple = (
            struct.unpack_from("<H", value[offs:],6)[0],  # row 
            struct.unpack_from("<H", value[offs:],2)[0],  # column
            struct.unpack_from("<H", value[offs:],8)[0]  # index to desktop_items
        )
        # item_positions.append(item_tuple[:2])
        position = [mapping.get(i, 0) for i in item_tuple[:2]]
        desktop_items[item_tuple[2]]['position'] = list(position)

    # # 处理行列
    # row_set = set((x[0] for x in item_positions))
    # column_set = set((x[1] for x in item_positions))

    # row_set = sorted(row_set)
    # column_set = sorted(column_set)

    # mapping = lambda x: {row: idx + 1 for idx, row in enumerate(x)}

    # row_mapping = mapping(row_set)
    # column_mapping = mapping(column_set)

    # for _, item in enumerate(desktop_items):
    #     item['position'] = (row_mapping[item['position'][0]], column_mapping[item['position'][1]])

    return desktop_items

def get_desktop_items(mode="click"):
    value = _get_reg_value()
    desktop_items = _read_reg_value(value, mode=mode)

    # for i in desktop_items:
        # i['position'] = get_coordinate(*i['position'])
    return desktop_items

def get_by_windows_search(app_name):
    pyautogui.press('win')
    time.sleep(0.5)  # Wait for the start menu to open
    pyautogui.write(app_name)
    pyautogui.press('enter')

def get_by_everytools_search(keywords, max_results=10, search_type='regex', ext=None):
    et = everytools.EveryTools()
    match search_type:
        case 'regex':
            et.search(keywords, regex=True)
        case 'audio':
            et.search_audio(keywords)
        case 'video':
            et.search_video(keywords)
        case 'pic':
            et.search_pic(keywords)
        case 'doc':
            et.search_doc(keywords)
        case 'exe':
            et.search_exe(keywords)
        case 'folder':
            et.search_folder(keywords)
        case 'zip':
            et.search_zip(keywords)
        case 'ext':
            et.search_ext(ext=keywords) if ext else et.search(keywords)
        case _:
            et.search(keywords)
        
    results = et.results(max_results)
    names = results.name
    paths = results.path

    return [Item(name=name, path=os.path.join(path, name)) for name, path in zip(names, paths)]

def _get_nth_row_column_value(n: int) -> int:
    if n == 1:
        res = 0
    elif n == 2:
        res = 16256
    else:
        res = _get_nth_row_column_value(n - 1) + math.pow(2, 7 - math.floor(math.log2(n - 2)))
    print(res)
    return res
    
def _get_nth_row_column_value_withloop(n: int) -> int:
    res = 0
    for i in range(2, n + 1):
        res = res +  (1 << (7 - (i - 2).bit_length() + 1)) if i > 2 else 16256
        print(res)
    return res

def generate_mapping(n: int) -> dict:
    mapping = {0: 1, 16256: 2}
    tmp = 16256

    for i in range(3, n + 1):
        tmp += (1 << (7 - (i - 2).bit_length() + 1))
        mapping[tmp] = i
    return mapping    

def get_coordinate(row: int, column: int) -> tuple:
    x = (column - 1) * ICON_SIZE[0] + ICON_SIZE[0] // 2
    y = (row - 1) * (ICON_SIZE[1] + 45) + ICON_SIZE[1] // 2

    return (x, y)

def open_object(path: str):
    os.startfile(path)