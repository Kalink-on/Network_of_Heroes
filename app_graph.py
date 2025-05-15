import os
import json
import networkx as nx
import plotly.graph_objects as go
import tkinter as tk
from tkinter import ttk, messagebox
import threading
from colorsys import hls_to_rgb
import tempfile
import webbrowser
import platform
from PIL import Image, ImageTk


class HPNetworkVisualizer:
    def __init__(self, root):
        self.root = root
        self.temp_html_file = None
        self.setup_ui()

    def setup_ui(self):
        self.root.title("Анализатор социальной сети Гарри Поттера")
        self.root.geometry("900x700")
        self.root.resizable(True, True)
        self.root.configure(bg='#f0f8ff')

        header_frame = tk.Frame(self.root, bg='#1a237e', height=100)
        header_frame.pack(fill='x', pady=(0, 20))

        try:
            img = Image.open("data/hp_logo.jpg")
            if img:
                img = img.resize((80, 80), Image.LANCZOS)
                self.logo = ImageTk.PhotoImage(img)
                logo_label = tk.Label(header_frame, image=self.logo, bg='#1a237e')
                logo_label.pack(side='left', padx=20)
        except Exception as e:
            print(f"Не удалось загрузить логотип: {str(e)}")

        title_label = tk.Label(
            header_frame,
            text="Визуализация социальной сети персонажей Гарри Поттера",
            font=('Arial', 18, 'bold'),
            fg='white',
            bg='#1a237e'
        )
        title_label.pack(side='left', pady=20)
        content_frame = tk.Frame(self.root, bg='#f0f8ff')
        content_frame.pack(expand=True, fill='both', padx=50, pady=20)

        desc_text = (
            "Эта программа визуализирует социальные связи между персонажами "
            "вселенной Гарри Поттера.\n\n"
            "Цвет узлов обозначает сторону персонажа, а толщина и цвет линий "
            "отображают силу связи между персонажами."
        )

        desc_label = tk.Label(
            content_frame,
            text=desc_text,
            font=('Arial', 12),
            bg='#f0f8ff',
            wraplength=600,
            justify='center'
        )
        desc_label.pack(pady=(0, 30))

        btn_frame = tk.Frame(content_frame, bg='#f0f8ff')
        btn_frame.pack(pady=20)

        style = ttk.Style()
        style.configure('TButton', font=('Arial', 12), padding=10)
        style.map('TButton',
                  foreground=[('pressed', 'white'), ('active', 'white')],
                  background=[('pressed', '#303f9f'), ('active', '#3949ab')])

        self.load_btn = ttk.Button(
            btn_frame,
            text="Загрузить и визуализировать",
            command=self.load_and_visualize,
            style='TButton'
        )
        self.load_btn.pack(pady=10, ipadx=20, ipady=10)

        legend_frame = tk.Frame(content_frame, bg='#e3f2fd', bd=2, relief='groove')
        legend_frame.pack(pady=20, ipadx=10, ipady=10)

        legend_title = tk.Label(
            legend_frame,
            text="Легенда цветов узлов:",
            font=('Arial', 12, 'bold'),
            bg='#e3f2fd'
        )
        legend_title.pack(pady=(5, 10))

        colors = {
            "Положительный": "#4CAF50",
            "Отрицательный": "#F44336",
            "Нейтральный": "#607D8B",
            "Неопределённый": "#9C27B0",
            "Неизвестно": "#4682B4"
        }

        for side, color in colors.items():
            frame = tk.Frame(legend_frame, bg='#e3f2fd')
            frame.pack(fill='x', padx=10, pady=2)
            tk.Label(frame, text="⬤", fg=color, bg='#e3f2fd', font=('Arial', 14)).pack(side='left')
            tk.Label(frame, text=side, bg='#e3f2fd', font=('Arial', 11)).pack(side='left', padx=5)

        self.status_var = tk.StringVar()
        self.status_var.set("Готов к работе")
        status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            relief='sunken',
            anchor='w',
            font=('Arial', 10),
            bg='#e3f2fd'
        )
        status_bar.pack(side='bottom', fill='x')

    def load_json(self, file_path):
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                return json.load(file)
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось загрузить файл {file_path}: {str(e)}")
            return None

    def create_graph(self, data):
        G = nx.Graph()
        for char, relations in data.items():
            for other_char, weight in relations.items():
                G.add_edge(char, other_char, weight=weight)
        return G

    def blue_gradient(self, intensity):
        hue = 240 / 360
        saturation = 0.9
        lightness = 0.85 - (0.7 * intensity)
        r, g, b = hls_to_rgb(hue, lightness, saturation)
        return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"

    def interactive(self, G, character_info):
        pos = nx.spring_layout(G, k=0.5, iterations=50, seed=42)

        side_colors = {
            "Положительный": "#4CAF50",
            "Отрицательный": "#F44336",
            "Нейтральный": "#607D8B",
            "Неопределённый": "#9C27B0",
            "unknown": "#4682B4"
        }

        degrees = dict(G.degree())
        max_degree = max(degrees.values()) if degrees else 1
        node_sizes = [15 + 25 * (degrees[node] / max_degree) for node in G.nodes()]

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
                f"Связей: {degrees[node]}"
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
                color = self.blue_gradient(intensity)

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
                        size=node_sizes,
                        line=dict(width=2, color='#1A237E')
                    ),
                    textfont=dict(size=12, color='black', family="Arial"),
                    showlegend=False
                )
            ],
            layout=go.Layout(
                title=dict(
                    text='Социальная сеть персонажей "Гарри Поттера"',
                    font=dict(size=24, family="Arial", color='black'),
                    x=0.5,
                    xanchor='center'
                ),
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20, l=20, r=20, t=80),
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                paper_bgcolor='white',
                plot_bgcolor='white',
                width=1400,
                height=900,
                clickmode='event+select',
                dragmode='pan'
            )
        )

        try:
            temp_dir = tempfile.gettempdir()
            self.temp_html_file = os.path.join(temp_dir, "hp_network_visualization.html")

            if os.path.exists(self.temp_html_file):
                os.remove(self.temp_html_file)

            fig.write_html(self.temp_html_file, auto_open=False)

            if platform.system() == 'Windows':
                os.startfile(self.temp_html_file)
            elif platform.system() == 'Darwin':
                webbrowser.open('file://' + os.path.abspath(self.temp_html_file))
            else:
                webbrowser.open('file://' + os.path.abspath(self.temp_html_file))

        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось создать визуализацию: {str(e)}")
            self.status_var.set("Ошибка при создании визуализации")

    def load_and_visualize(self):
        self.status_var.set("Загрузка данных...")
        self.load_btn.config(state='disabled')
        self.root.update()

        try:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            network_path = os.path.join(base_dir, "data", "precise_character_network.json")
            character_path = os.path.join(base_dir, "data", "character_info_with_roles.json")

            if not os.path.exists(network_path):
                messagebox.showerror("Ошибка", f"Файл не найден: {network_path}")
                self.status_var.set("Файл данных не найден")
                return
            if not os.path.exists(character_path):
                messagebox.showerror("Ошибка", f"Файл не найден: {character_path}")
                self.status_var.set("Файл данных не найден")
                return

            network_data = self.load_json(network_path)
            character_data = self.load_json(character_path)

            if network_data is None or character_data is None:
                self.status_var.set("Ошибка загрузки данных")
                return

            G = self.create_graph(network_data)

            threading.Thread(
                target=self.interactive,
                args=(G, character_data),
                daemon=True
            ).start()

            self.status_var.set("Визуализация запущена в браузере")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Произошла ошибка: {str(e)}")
            self.status_var.set("Ошибка при обработке данных")
        finally:
            self.load_btn.config(state='normal')


def main():
    root = tk.Tk()
    app = HPNetworkVisualizer(root)
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry(f'+{x}+{y}')

    root.mainloop()


if __name__ == "__main__":
    main()
