import requests
from bs4 import BeautifulSoup
import re


urls = [
    "https://harrypotter.fandom.com/ru/wiki/Гарри_Поттер_и_Философский_камень_(персонажи)",
    "https://harrypotter.fandom.com/ru/wiki/Гарри_Поттер_и_Тайная_комната_(персонажи)",
    "https://harrypotter.fandom.com/ru/wiki/Гарри_Поттер_и_Узник_Азкабана_(персонажи)",
    "https://harrypotter.fandom.com/ru/wiki/Гарри_Поттер_и_Кубок_огня_(персонажи)",
    "https://harrypotter.fandom.com/ru/wiki/Гарри_Поттер_и_Орден_Феникса_(персонажи)",
    "https://harrypotter.fandom.com/ru/wiki/Гарри_Поттер_и_Принц-полукровка_(персонажи)",
    "https://harrypotter.fandom.com/ru/wiki/Гарри_Поттер_и_Дары_Смерти_(персонажи)"
]


def names(html):
    soup = BeautifulSoup(html, 'html.parser')
    characters = set()
    for el in soup.find_all('li'):
        text = el.get_text(strip=True)
        if re.match(r'^[А-ЯЁ][а-яё]+\s[А-ЯЁ][а-яё]+$', text):
            characters.add(text)
    return characters


def main():
    all_characters = set()
    for url in urls:
        print(f"Обрабатывается {url}...")
        response = requests.get(url)
        if response.status_code == 200:
            characters = names(response.text)
            all_characters.update(characters)
        else:
            print(f"Не удалось получить доступ к {url}")
    with open("characters.txt", "w", encoding="utf-8") as file:
        for character in sorted(all_characters):
            file.write(character + "\n")
    print(f"Найдено {len(all_characters)} уникальных персонажей.")

if __name__ == "__main__":
    main()