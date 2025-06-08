import requests
from bs4 import BeautifulSoup
import re
import json
import time
from pathlib import Path


def clean_text(text):
    while '[' in text and ']' in text:
        start = text.index('[')
        end = text.index(']') + 1
        text = text[:start] + text[end:]
    return text.strip()


def names(html):
    soup = BeautifulSoup(html, 'html.parser')
    characters = set()
    for el in soup.find_all('li'):
        text = clean_text(el.get_text(strip=True))
        if re.match(r'^[А-ЯЁ][а-яё]+\s[А-ЯЁ][а-яё]+$', text):
            characters.add(text)
    return characters


def determine_side(loyalty_text):
    if not loyalty_text or loyalty_text == 'Не указана':
        return "Нейтральный"

    normalized = loyalty_text.lower().replace('ё', 'е').strip()
    groups = [g.strip() for g in re.split(r'[,;]\s*|\n', normalized) if g.strip()]

    positive_keywords = {'орден феникса', 'отряд дамблдора'}
    negative_keywords = {'пожиратели смерти', 'инспекционная дружина'}

    has_positive = any(any(kw in group for kw in positive_keywords) for group in groups)
    has_negative = any(any(kw in group for kw in negative_keywords) for group in groups)

    if has_positive and has_negative:
        return "Неопределённый"
    elif has_positive:
        return "Положительный"
    elif has_negative:
        return "Отрицательный"
    return "Нейтральный"


def get_character_info(name):
    try:
        url = f"https://harrypotter.fandom.com/ru/wiki/{name.replace(' ', '_')}"
        response = requests.get(url, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')

        infobox = soup.find('aside', {'class': 'portable-infobox'})
        if not infobox:
            return None

        info = {
            'faculty': 'Не указан',
            'side': 'Нейтральный',
            'blood_status': 'Неизвестно',
            'species': 'Человек',
            'loyalty': 'Не указана'
        }

        for row in infobox.find_all('div', {'class': 'pi-item'}):
            if not row.find('h3'):
                continue

            key = clean_text(row.find('h3').get_text(strip=True))
            value = clean_text(row.find('div').get_text(' ', strip=True)) if row.find('div') else ''

            if 'факультет' in key.lower():
                info['faculty'] = value.split(',')[0].strip()
            elif 'лояльность' in key.lower():
                info['loyalty'] = value
            elif 'чистота крови' in key.lower() or 'чистотакрови' in key.lower():
                info['blood_status'] = value.split('(')[0].strip()
            elif 'вид' in key.lower():
                info['species'] = value.split(',')[0].strip()

        if info['loyalty'] != 'Не указана':
            info['side'] = determine_side(info['loyalty'])

        if not 'человек' in info['species'].lower():
            info['faculty'] = 'Отсутствует'
            info['blood_status'] = 'Нельзя определить'
        elif info['blood_status'].lower() == 'магл':
            info['faculty'] = 'Отсутствует'

        return info

    except Exception as e:
        print(f"Ошибка при обработке {name}: {str(e)}")
        return None


def main():
    urls = [
        "https://harrypotter.fandom.com/ru/wiki/Гарри_Поттер_и_Философский_камень_(персонажи)",
        "https://harrypotter.fandom.com/ru/wiki/Гарри_Поттер_и_Тайная_комната_(персонажи)",
        "https://harrypotter.fandom.com/ru/wiki/Гарри_Поттер_и_Узник_Азкабана_(персонажи)",
        "https://harrypotter.fandom.com/ru/wiki/Гарри_Поттер_и_Кубок_огня_(персонажи)",
        "https://harrypotter.fandom.com/ru/wiki/Гарри_Поттер_и_Орден_Феникса_(персонажи)",
        "https://harrypotter.fandom.com/ru/wiki/Гарри_Поттер_и_Принц-полукровка_(персонажи)",
        "https://harrypotter.fandom.com/ru/wiki/Гарри_Поттер_и_Дары_Смерти_(персонажи)"
    ]

    Path("data").mkdir(exist_ok=True)
    
    name_corrections = {
        'Мардж Дурсль': 'Марджори Дурсль',
        'Мистер Олливандер': 'Гаррик Олливандер',
        'Дедушка Невилла': 'Отец Фрэнка Долгопупса',
        'Отец Хагрида': 'Мистер Хагрид'
    }

    all_characters = set()

    for url in urls:
        print(f"Обрабатывается {url}...")

        try:
            response = requests.get(url, timeout=20)
            response.raise_for_status()
            if response.url != url:
                print(f"Произошёл редирект с {url} на {response.url}")

            all_characters.update(names(response.text))

        except Exception as e:
            print(f"Ошибка: {str(e)}")
            continue

    valid_characters = {c for c in all_characters if re.fullmatch(r'^[А-ЯЁ][а-яё]+\s[А-ЯЁ][а-яё]+$', c)}

    with open("data/characters.txt", "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(valid_characters)))

    character_info = {}

    for char in sorted(valid_characters):
        corrected_name = name_corrections.get(char, char)
        print(f"Сбор информации для {corrected_name}...")
        info = get_character_info(corrected_name)
        if info:
            character_info[char] = info

        time.sleep(1.5)

    with open("data/character_info.json", "w", encoding="utf-8") as f:
        json.dump(character_info, f, ensure_ascii=False, indent=2)

    print(f"Собрана информация по {len(character_info)} персонажам")


if __name__ == "__main__":
    main()
