import os
import json
import spacy
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor


nlp = spacy.load("ru_core_news_lg")
nlp.max_length = 2000000


def load_known(file_path):
    full_names = set()
    name_to_full = {}
    with open(file_path, "r", encoding="utf-8") as file:
        for line in file:
            full_name = line.strip().lower()
            full_names.add(full_name)
            parts = full_name.split()
            if len(parts) == 2:
                name, surname = parts
                name_to_full[name] = full_name
                name_to_full[surname] = full_name
            name_to_full[full_name] = full_name
    return full_names, name_to_full


known_characters, name_to_full = load_known("characters.txt")


def extract_characters(doc):
    characters = set()
    for ent in doc.ents:
        if ent.label_ == "PER":
            name_parts = [token.lemma_.lower() for token in ent]
            if len(name_parts) == 1:
                name = name_parts[0]
                if name in name_to_full:
                    characters.add(name_to_full[name])
            elif len(name_parts) == 2:
                full_name = " ".join(name_parts)
                if full_name in name_to_full:
                    characters.add(name_to_full[full_name])
    return list(characters)


def process_book(file_path, nlp):
    with open(file_path, "r", encoding="utf-8") as file:
        text = file.read()
        doc = nlp(text)
        characters = extract_characters(doc)
        print(f"Обработана книга: {file_path}, найдено персонажей: {len(characters)}")
        return characters


def process_books(folder_path, nlp):
    relations = defaultdict(lambda: defaultdict(int))
    character_counter = Counter()
    file_paths = [os.path.join(folder_path, filename) for filename in os.listdir(folder_path) if
                  filename.endswith(".txt")]
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(lambda fp: process_book(fp, nlp), file_paths))
    for characters in results:
        character_counter.update(characters)
        for i in range(len(characters)):
            for j in range(i + 1, len(characters)):
                char1, char2 = characters[i], characters[j]
                if char1 != char2:
                    relations[char1][char2] += 1
                    relations[char2][char1] += 1
    return relations, character_counter


def format_name(name):
    return " ".join(word.capitalize() for word in name.split())


def save_to_json(data, output_file):
    if not data:
        print("Нет данных для сохранения.")
        return
    formatted_data = {
        format_name(char): {format_name(other_char): count for other_char, count in rel.items()}
        for char, rel in data.items()
    }
    with open(output_file, "w", encoding="utf-8") as file:
        json.dump(formatted_data, file, indent=4, ensure_ascii=False)
    print(f"Данные успешно сохранены в {output_file}.")


if __name__ == "__main__":
    books = "books"
    output_file = "character_relations.json"
    relations, character_counter = process_books(books, nlp)
    min_mentions = 5
    filtered_characters = {char for char, count in character_counter.items() if count >= min_mentions}
    filtered_relations = {
        char: {other_char: count for other_char, count in rel.items() if other_char in filtered_characters}
        for char, rel in relations.items() if char in filtered_characters
    }
    save_to_json(filtered_relations, output_file)