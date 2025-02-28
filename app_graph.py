import json
import networkx as nx
import plotly.graph_objects as go
import tkinter as tk
from tkinter import ttk
import threading


def load_json(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)
    return data


def create_graph(data):
    G = nx.Graph()
    for char, relations in data.items():
        for other_char, weight in relations.items():
            G.add_edge(char, other_char, weight=weight)
    return G


def interactive(G):
    pos = nx.spring_layout(G, k=0.5, iterations=50)
    edge_trace = []
    for edge in G.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_trace.append(go.Scatter(
            x=[x0, x1, None], y=[y0, y1, None],
            line=dict(width=0.5, color='#888'),
            hoverinfo='none',
            mode='lines'))
    node_trace = go.Scatter(
        x=[], y=[], text=[], mode='markers+text', hoverinfo='text',
        marker=dict(
            showscale=False,
            colorscale='YlGnBu',
            size=10,
            color='turquoise',
            line=dict(width=2)))
    for node in G.nodes():
        x, y = pos[node]
        node_trace['x'] += tuple([x])
        node_trace['y'] += tuple([y])
        node_trace['text'] += tuple([node])
    fig = go.Figure(data=edge_trace + [node_trace],
                    layout=go.Layout(
                        showlegend=False,
                        hovermode='closest',
                        margin=dict(b=0, l=0, r=0, t=0),
                        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False))
                    )
    fig.show()


def main():
    root = tk.Tk()
    root.title("Граф взаимодействий персонажей 'Гарри Поттера'")
    root.geometry("800x600")
    def load_graph():
        file_path = "character_relations.json"
        data = load_json(file_path)
        G = create_graph(data)
        threading.Thread(target=interactive, args=(G,)).start()
    load_button = ttk.Button(root, text="Загрузить граф", command=load_graph)
    load_button.pack(pady=20)
    root.mainloop()


if __name__ == "__main__":
    main()