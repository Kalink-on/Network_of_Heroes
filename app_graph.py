import json
import networkx as nx
import plotly.graph_objects as go
import tkinter as tk
from tkinter import ttk
import threading
from colorsys import hls_to_rgb


def load_json(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception as e:
        print(f"Ошибка загрузки {file_path}: {str(e)}")
        return {}


def create_graph(data):
    G = nx.Graph()
    for char, relations in data.items():
        for other_char, weight in relations.items():
            G.add_edge(char, other_char, weight=weight)
    return G


def blue_gradient(intensity):
    hue = 240 / 360
    saturation = 0.9
    lightness = 0.85 - (0.7 * intensity)
    r, g, b = hls_to_rgb(hue, lightness, saturation)
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


def interactive(G, character_info):
    pos = nx.spring_layout(G, k=0.5, iterations=50)

    side_colors = {
        "Положительный": "#4CAF50",
        "Отрицательный": "#F44336",
        "Нейтральный": "#607D8B",
        "Неопределённый": "#9C27B0",
        "unknown": "#4682B4"
    }

    node_colors = []
    hover_texts = []
    for node in G.nodes():
        info = character_info.get(node, {})
        side = info.get("side", "unknown")
        role = info.get("role", "Неизвестно")
        node_colors.append(side_colors.get(side, "#4682B4"))

        text = (
            f"<b>{node}</b><br>"
            f"Роль: {role}<br>"
            f"Факультет: {info.get('faculty', 'неизвестно')}<br>"
            f"Сторона: {side}<br>"
            f"Статус крови: {info.get('blood_status', 'неизвестно')}<br>"
            f"Лояльность: {info.get('loyalty', 'не указана')}<br>"
            f"Связей: {G.degree[node]}"
        )
        hover_texts.append(text)
    edge_traces = []
    weights = [G.edges[edge]['weight'] for edge in G.edges()]
    if weights:
        min_weight = min(weights)
        max_weight = max(weights)
        weight_range = max_weight - min_weight if max_weight != min_weight else 1
        for edge in G.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            weight = G.edges[edge]['weight']
            normalized_width = max(1, min(8, 1 + 7 * (weight - min_weight) / weight_range))
            intensity = (weight - min_weight) / weight_range
            color = blue_gradient(intensity)

            edge_trace = go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                line=dict(width=normalized_width, color=color),
                hoverinfo='text',
                hovertext=f"{edge[0]} ↔ {edge[1]}<br>Сила связи: {weight:.1f}",
                mode='lines',
                showlegend=False
            )
            edge_traces.append(edge_trace)

    fig = go.Figure(
        data=edge_traces + [
            go.Scatter(
                x=[pos[node][0] for node in G.nodes()],
                y=[pos[node][1] for node in G.nodes()],
                mode='markers+text',
                text=list(G.nodes()),
                textposition='top center',
                hovertext=hover_texts,
                hoverinfo='text',
                marker=dict(
                    color=node_colors,
                    size=20,
                    line=dict(width=2, color='#1A237E')
                ),
                textfont=dict(size=10, color='black'),
                showlegend=False
            )
        ],
        layout=go.Layout(
            title=dict(
                text='Социальная сеть персонажей "Гарри Поттера"',
                font=dict(size=20, family="Arial", color='black')
            ),
            showlegend=False,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=50),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            paper_bgcolor='white',
            plot_bgcolor='white',
            width=1400,
            height=1000
        )
    )

    fig.show()


def main():
    root = tk.Tk()
    root.title("Анализатор социальной сети Гарри Поттера")
    root.geometry("800x600")

    def load_and_visualize():
        network_data = load_json("data/precise_character_network.json")
        character_data = load_json("data/character_info_with_roles.json")

        if not network_data or not character_data:
            print("Ошибка: Не удалось загрузить данные")
            return

        G = create_graph(network_data)
        threading.Thread(
            target=interactive,
            args=(G, character_data),
            daemon=True
        ).start()
        
    ttk.Label(
        root,
        text="Визуализация социальной сети персонажей",
        font=('Arial', 14)
    ).pack(pady=20)

    load_btn = ttk.Button(
        root,
        text="Загрузить и визуализировать",
        command=load_and_visualize
    )
    load_btn.pack(pady=10)

    ttk.Label(
        root,
        text="После нажатия кнопки откроется браузер с визуализацией",
        font=('Arial', 10)
    ).pack(pady=5)

    root.mainloop()


if __name__ == "__main__":
    main()
