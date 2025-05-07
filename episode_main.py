import json


def determine_roles(network_file, character_file, output_file):
    with open(network_file, 'r', encoding='utf-8') as f:
        network_data = json.load(f)

    with open(character_file, 'r', encoding='utf-8') as f:
        character_data = json.load(f)

    connection_counts = {char: len(relations) for char, relations in network_data.items()}
    avg_connections = sum(connection_counts.values()) / len(connection_counts) if connection_counts else 0
    for char in character_data:
        count = connection_counts.get(char, 0)
        if count > avg_connections * 1.5:
            character_data[char]['role'] = 'Главный'
        elif count > avg_connections * 0.7:
            character_data[char]['role'] = 'Второстепенный'
        else:
            character_data[char]['role'] = 'Эпизодический'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(character_data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    determine_roles(
        network_file="data/precise_character_network.json",
        character_file="data/character_info.json",
        output_file="data/character_info_with_roles.json"
    )
