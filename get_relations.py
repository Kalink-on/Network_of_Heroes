import os
import json
import spacy
from collections import defaultdict, Counter
from concurrent.futures import ThreadPoolExecutor

nlp = spacy.load("ru_core_news_lg")
nlp.max_length = 3000000


class PrecisionCharacterResolver:
    def __init__(self, character_file):
        self.characters = set()
        self.name_variants = defaultdict(set)
        self.primary_names = {}
        self.load_characters(character_file)
        self.pronouns = {
            'он': 'male', 'она': 'female', 'они': 'plural',
            'его': 'male', 'её': 'female', 'их': 'plural'
        }
        self.context_window = []
        self.max_context_size = 5
        self.gender_cache = {}
        self.dialogue_participants = set()
        self.in_dialogue = False

    def load_characters(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            for line in f:
                full_name = line.strip().lower()
                if not full_name:
                    continue
                self.characters.add(full_name)
                self.primary_names[full_name] = full_name
                parts = full_name.split()
                variants = {full_name, parts[0], parts[-1]} if len(parts) > 1 else {full_name}
                for variant in variants:
                    self.name_variants[variant].add(full_name)

    def resolve_name(self, text):
        if not text:
            return None
        text = text.lower().strip()
        if text in self.characters:
            return self.primary_names[text]
        if text in self.name_variants:
            variants = self.name_variants[text]
            if variants:
                for recent in reversed(self.context_window):
                    if recent in variants:
                        return self.primary_names[recent]
                return self.primary_names[next(iter(variants))]

        return None

    def update_context(self, character):
        if character and character in self.primary_names:
            canonical_name = self.primary_names[character]
            if canonical_name in self.context_window:
                self.context_window.remove(canonical_name)
            self.context_window.append(canonical_name)
            if len(self.context_window) > self.max_context_size:
                self.context_window.pop(0)

    def process_dialogue(self, token):
        if token.text in ('"', "'", '«', '»'):
            self.in_dialogue = not self.in_dialogue
            if not self.in_dialogue:
                participants = list(self.dialogue_participants)
                self.dialogue_participants = set()
                return participants
        return []


def analyze_interactions(doc, resolver):
    interactions = defaultdict(Counter)
    current_section_chars = set()

    for sent in doc.sents:
        dialogue_interactions = []
        for token in sent:
            participants = resolver.process_dialogue(token)
            if participants:
                dialogue_interactions.extend(participants)
        sent_chars = set()
        for ent in sent.ents:
            if ent.label_ == 'PER':
                char = resolver.resolve_name(ent.text)
                if char:
                    sent_chars.add(char)
                    resolver.update_context(char)

        for char in dialogue_interactions:
            sent_chars.add(char)

        if len(sent_chars) > 1:
            chars = list(sent_chars)
            for i in range(len(chars)):
                for j in range(i + 1, len(chars)):
                    weight = 1.0 if (chars[i] in dialogue_interactions and
                                     chars[j] in dialogue_interactions) else 0.5

                    interactions[chars[i]][chars[j]] += weight
                    interactions[chars[j]][chars[i]] += weight

        current_section_chars.update(sent_chars)

    return interactions


def process_book(file_path, resolver):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
            print(f"Анализ {os.path.basename(file_path)}...")
            doc = nlp(text)
            return analyze_interactions(doc, resolver)
    except Exception as e:
        print(f"Ошибка при обработке {file_path}: {str(e)}")
        return defaultdict(Counter)


def normalize_relations(relations, min_links=3, min_weight=2.0):

    filtered = defaultdict(Counter)
    for char, links in relations.items():
        for other, weight in links.items():
            if weight >= min_weight:
                filtered[char][other] = weight

    strong_chars = {char for char in filtered
                    if sum(filtered[char].values()) >= min_links}

    final_relations = {
        char: {other: weight for other, weight in links.items()
               if other in strong_chars}
        for char, links in filtered.items()
        if char in strong_chars
    }

    return final_relations


def save_network(relations, output_file):
    if not relations:
        print("Нет данных для сохранения. Проверьте входные файлы.")
        return

    formatted = {
        ' '.join(word.capitalize() for word in k.split()): {
            ' '.join(word.capitalize() for word in vk.split()): round(vv, 1)
            for vk, vv in v.items()
        }
        for k, v in relations.items()
    }

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(formatted, f, indent=2, ensure_ascii=False)
    print(f"Сохранено в {output_file}")


def main():
    if not os.path.exists("characters.txt"):
        print("Создайте файл characters.txt со списком персонажей!")
        return

    if not os.path.exists("books"):
        print("Создайте папку books с текстами в формате .txt!")
        return

    book_files = [os.path.join("books", f) for f in os.listdir("books") if f.endswith('.txt')]
    if not book_files:
        print("Добавьте файлы книг в папку books!")
        return

    resolver = PrecisionCharacterResolver("characters.txt")
    all_relations = defaultdict(Counter)

    with ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(process_book, f, resolver) for f in book_files]
        for future in futures:
            book_relations = future.result()
            for char, links in book_relations.items():
                for other, weight in links.items():
                    all_relations[char][other] += weight

    final_relations = normalize_relations(all_relations)
    save_network(final_relations, "precise_character_network.json")


if __name__ == "__main__":
    main()
