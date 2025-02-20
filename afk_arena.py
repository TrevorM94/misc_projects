import pyautogui
import pygetwindow as gw
import pytesseract
from PIL import Image, ImageEnhance
import os
import time
import re
from difflib import get_close_matches
from pprint import pprint

def bluestacks_screenshot():
    pyautogui.hotkey('ctrl', 'shift', 's')


def find_bluestacks_window():
    window_titles = gw.getAllTitles()

    for title in window_titles:
        if 'BlueStacks App Player' in title:
            return gw.getWindowsWithTitle(title)[0]

    return None


def interact_with_bluestacks():
    bluestacks_window = find_bluestacks_window()

    if bluestacks_window:
        bluestacks_window.activate()
        time.sleep(0.5)
        print("Active Window Title:", gw.getActiveWindow().title)
        
        summon_again_x = bluestacks_window.left + 625
        summon_again_y = bluestacks_window.top + 785
        pyautogui.click(summon_again_x, summon_again_y)

        time.sleep(2.5)

        quick_flip_x = bluestacks_window.left + 625
        quick_flip_y = bluestacks_window.top + 785
        pyautogui.click(quick_flip_x, quick_flip_y)

        time.sleep(1)

        flip_all_x = bluestacks_window.left + 625
        flip_all_y = bluestacks_window.top + 785
        pyautogui.click(flip_all_x, flip_all_y)

        time.sleep(6)

        bluestacks_screenshot()

    else:
        print("Bluestacks window was not found.")


def get_most_recent_screenshot_path():
    directory = 'C:\\Users\\trevo\\OneDrive\\Pictures\\BlueStacks'
    files = os.listdir(directory)

    image_files = [f for f in files if f.lower().endswith('.png')]

    image_files.sort(key = lambda x: os.path.getmtime(os.path.join(directory, x)), reverse=True)

    if image_files:
        return os.path.join(directory, image_files[0])
    else:
        return None
    
def delete_most_recent_screenshot():
    directory = 'C:\\Users\\trevo\\OneDrive\\Pictures\\BlueStacks'
    files = os.listdir(directory)

    files = [f for f in files if os.path.isfile(os.path.join(directory, f))]

    if not files:
        print('No files are present in the directory')

    most_recent = max(files, key=lambda f: os.path.getmtime(os.path.join(directory, f)))
    most_recent_file_path = os.path.join(directory, most_recent)

    try:
        os.remove(most_recent_file_path)
        print(f'Deleted the most recent screenshot named {most_recent}.')
    except Exception as e:
        print(f'Failed to delete the most recent file named: {most_recent}.\t{e}')
    

def preprocess_image(image):
    enhanced_image = ImageEnhance.Sharpness(image).enhance(3.0)
    return enhanced_image

def get_card_coordinates(card_num):

    return {
        1: [110, 500, 255, 520],
        2: [110, 855, 255, 875],
        3: [110, 1210, 255, 1230],
        4: [375, 315, 520, 335],
        5: [375, 675, 520, 695],
        6: [375, 1025, 520, 1045],
        7: [375, 1385, 520, 1405],
        8: [640, 505, 785, 525],
        9: [640, 865, 785, 885],
        10: [640, 1215, 785, 1235]
    }.get(card_num)


def wanted_heroes():
    hero_titles = [
        'Maiden of Dusk'
        , 'Duskfeather'
        , 'Abyssal Rocker'
        , 'The Insidious'
        , 'Voidbinder'
        , 'Scion of Dawn'
        , 'Lady of Summer'
        , 'Harbinger of Truth'
        , 'The Shining Sword'
        , 'The Crafter'
        , 'The Frozen Mother'
        , 'The Bonesmith'
        , 'The Astral Oracle'
        , 'The Sacrifice'
        , 'Spark of Hope'
        , 'Heart of Moltenflow'
        , 'Luminous Archbishop'
        , 'Fool of Chaos'
        , 'Keeper of Order'
        , 'Commander of the Waves'
        , 'The Soulreaver'
    ]
    return hero_titles


def check_for_awakened_heroes():

    screenshot_path = get_most_recent_screenshot_path()
    matched = []

    if screenshot_path:
        screenshot = Image.open(screenshot_path)
        processed_image = preprocess_image(screenshot)

    for i in range(1, 11):
        test = find_matches_from_screenshot(processed_image, get_card_coordinates(i))
        if test is not None:
            matched.append(test)

    # delete_most_recent_screenshot()
            
    if len(matched) >= 3:
        pprint(matched)
        return True

    return False

def find_matches_from_screenshot(processed_image, card_coords):
    
    test_hero_titles = wanted_heroes()
    card_cropped = processed_image.crop((card_coords[0], card_coords[1], card_coords[2], card_coords[3]))
    card_cropped_enhanced = ImageEnhance.Sharpness(card_cropped).enhance(3.5)
    card_extracted_text = pytesseract.image_to_string(card_cropped_enhanced, lang='eng', config='--psm 6')

    match = get_close_matches(card_extracted_text, test_hero_titles, n=1, cutoff=0.9)

    if match:
        return match[0]
    else:
        return None

while True:
    interact_with_bluestacks()
    time.sleep(2)
    if check_for_awakened_heroes():
        break