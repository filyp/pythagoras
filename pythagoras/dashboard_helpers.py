import os
import json
import pathlib
from collections import defaultdict

import pygame
import numpy as np
import networkx as nx
import randomname

from config import *


def decompose_into_small_primes(n, primes=[2, 3, 5, 7]):
    factors = np.zeros_like(primes)
    while n != 1:
        updated = False
        for i, prime in enumerate(primes):
            if n % prime == 0:
                n /= prime
                factors[i] += 1
                updated = True
        if not updated:
            # n cannot be decomposed into those primes
            return None
    return factors


class ChordsSaver:
    def __init__(self):
        base_dir = pathlib.Path(__file__).parent.parent
        self.saved_chords_file = os.path.join(base_dir, "data", "saved_chords.txt")
        self.all_saves = dict()
        if os.path.isfile(self.saved_chords_file):
            with open(self.saved_chords_file, "r") as f:
                for line in f:
                    save_name, save_dict = json.loads(line).popitem()
                    self.all_saves[save_name] = save_dict

    def get_save(self, save_name):
        try:
            save = self.all_saves[save_name]
        except KeyError:
            print("Error: there is no save with this name")
            exit(1)

        print("\nloaded chords:")
        for keyname, chord in save.items():
            if keyname == "history":
                history = chord
                continue
            print(f"{keyname}: {[freq for freq, _, _ in chord]}")
        print("\nhistory:")
        for chord in history:
            print(f"{[freq for freq, _, _ in chord]}")
        self.last_loaded_save_name = save_name

        # * note that save is a dict so it is passes by reference and will be modified
        return save

    def save_all_saves(self):
        with open(self.saved_chords_file, "w") as f:
            for save_name, save in self.all_saves.items():
                if save:
                    f.write(json.dumps({save_name: save}) + "\n")
        print("\nchords saved")

    def create_new_save(self):
        save_name = randomname.get_name()
        self.all_saves[save_name] = dict()
        self.last_loaded_save_name = save_name
        return self.all_saves[save_name]


class Drawer:
    def __init__(self, placement_matrix):
        self.placement_matrix = placement_matrix

        self.G = nx.Graph()
        self.dis = pygame.display.set_mode(resolution)
        self.coordinate_center = np.array([margin, resolution[1] - margin])

        pygame.display.init()
        pygame.font.init()
        pygame.display.set_caption("Pythagoras")
        self.font = pygame.font.SysFont("arial", int(text_size))

    def redraw_circle(self, dis, circle_size, n):
        if self.G.nodes[n]["active"]:
            color = yellow
        else:
            color = white
        pygame.draw.circle(dis, color, self.G.nodes[n]["position"], circle_size)
        # print a number in the circle
        text = self.font.render(str(n), True, black)
        text_rect = text.get_rect()
        text_rect.center = self.G.nodes[n]["position"]
        dis.blit(text, text_rect)

    def activate_node(self, n, volume=1):
        self.G.nodes[n]["active"] = True
        # paint edges
        for neighbor in self.G[n]:
            edge = self.G[n][neighbor]
            if self.G.nodes[neighbor]["active"]:
                edge["active"] = True
                position1 = self.G.nodes[n]["position"]
                position2 = self.G.nodes[neighbor]["position"]
                pygame.draw.line(self.dis, edge["color1"], position1, position2, line_width)
                self.redraw_circle(self.dis, circle_size, neighbor)
        self.redraw_circle(self.dis, circle_size, n)

    def deactivate_node(self, n):
        self.G.nodes[n]["active"] = False
        # paint edges
        for neighbor in self.G[n]:
            edge = self.G[n][neighbor]
            if self.G.nodes[neighbor]["active"]:
                # there was an active edge
                edge["active"] = False
                position1 = self.G.nodes[n]["position"]
                position2 = self.G.nodes[neighbor]["position"]
                pygame.draw.line(self.dis, edge["color0"], position1, position2, line_width)
                self.redraw_circle(self.dis, circle_size, neighbor)
        self.redraw_circle(self.dis, circle_size, n)

    def create_graph(self):
        # ! create circles
        for n in range(1, n_limit + 1):
            if n in avoid_numbers:
                continue
            decomposition = decompose_into_small_primes(n, primes=primes)
            if decomposition is None:
                continue
            position = (
                self.placement_matrix @ decomposition
            ) * displacement + self.coordinate_center
            self.G.add_node(n, active=False, position=position)
        # ! create edges
        for a, b, color0, color1 in draw_lines_for_ratios:
            for n1 in self.G.nodes:
                for n2 in self.G.nodes:
                    if n2 / n1 != a / b:
                        continue
                    self.G.add_edge(n1, n2, color0=color0, color1=color1, active=False)

    def draw_graph(self):
        # ! clear the screen
        self.dis.fill(black)
        # ! draw edges
        for u, v, edge_data in self.G.edges.data():
            position1 = self.G.nodes[u]["position"]
            position2 = self.G.nodes[v]["position"]
            if edge_data["active"]:
                color = edge_data["color1"]
            else:
                color = edge_data["color0"]
            pygame.draw.line(self.dis, color, position1, position2, line_width)
        # ! draw circles
        for n in self.G.nodes:
            self.redraw_circle(self.dis, circle_size, n)
        pygame.display.update()

    def get_clicked_node(self, click_pos):
        for n in self.G.nodes:
            position = self.G.nodes[n]["position"]
            if np.linalg.norm(click_pos - position) < circle_size:
                return n
        return None

    def is_active(self, node):
        return self.G.nodes[node]["active"]

    def clear_all(self):
        for node in self.G.nodes:
            if self.G.nodes[node]["active"]:
                self.deactivate_node(node)
        pygame.display.update()

    def draw_chord(self, chord):
        # deactivate
        for node in self.G.nodes:
            if self.G.nodes[node]["active"]:
                self.deactivate_node(node)
        # activate
        for freq, volume, _ in chord:
            self.activate_node(freq, volume)
        pygame.display.update()

    def draw_binding_view(self, chord, slope=1):
        def get_dot_position(freq, base_freq):
            pos = np.array([np.log2(freq), -(np.log2(freq) - np.log2(base_freq)) * slope])
            return pos * displacement + self.coordinate_center

        # clear the screen
        self.dis.fill(black)

        # draw a horizontal line
        position1 = self.coordinate_center
        position2 = self.coordinate_center + (resolution[0] - 2 * margin, 0)
        pygame.draw.line(self.dis, white, position1, position2, line_width)

        # draw notes on the line
        for freq, volume, _ in chord:
            log_position = np.log2(freq)
            dot_size = line_width + np.sqrt(volume) * 1 * line_width
            note_position = get_dot_position(freq, freq)
            pygame.draw.circle(self.dis, white, note_position, dot_size)

        # create gestalts
        # fmt: off
        ratios = [
            (2,1), (3,1), (4,1), (5,1), (6,1), (7,1), (8,1),
            (3,2), (5,2), (7,2), 
            (4,3), (5,3), (7,3), (8,3),
            (5,4), (7,4), 
            (6,5), (7,5), (8,5),
            (7,6), 
            (8,7),
        ]
        # fmt: on
        gestalt = defaultdict(set)  # for a base note, list te harmonics connected to it
        gestalt_affiliation = defaultdict(
            set
        )  # for a note, list the base notes of gestalts that it is in
        for a, b in ratios:
            for (
                freq1,
                vol1,
                _,
            ) in chord:
                for freq2, vol2, _ in chord:
                    if freq2 / freq1 != a / b:
                        continue
                    base_note = freq2 / a
                    gestalt[base_note].add(freq2)
                    gestalt[base_note].add(freq1)
                    gestalt_affiliation[freq1].add(base_note)
                    gestalt_affiliation[freq2].add(base_note)

        # draw gestalts
        volume_dict = {freq: vol for freq, vol, _ in chord}
        for base_note, freqs in gestalt.items():
            min_freq = min(freqs)
            max_freq = max(freqs)
            min_pos = get_dot_position(min_freq, base_note)
            max_pos = get_dot_position(max_freq, base_note)
            pygame.draw.line(self.dis, white, min_pos, max_pos, line_width)
            for freq in freqs:
                position = get_dot_position(freq, base_note)
                dot_size = line_width + np.sqrt(volume_dict[freq]) * 1 * line_width
                pygame.draw.circle(self.dis, white, position, dot_size)

        # draw gestalt binding
        for freq, base_notes in gestalt_affiliation.items():
            min_base_note = min(base_notes)
            max_base_note = max(base_notes)
            min_pos = get_dot_position(freq, min_base_note)
            max_pos = get_dot_position(freq, max_base_note)
            pygame.draw.line(self.dis, white, min_pos, max_pos, line_width)

        pygame.display.update()


class UndoHandler:
    def __init__(self, history=[]):
        self.history = history
        self.redo_stack = []

    def save(self, item):
        self.history.append(item)
        # # saving clears redo stack
        # self.redo_stack = []

    def undo(self, current_state):
        self.redo_stack.append(current_state)

        while self.history:
            item = self.history.pop()
            if item == current_state:
                continue
            return item
        return None

    def redo(self, current_state):
        self.history.append(current_state)

        while self.redo_stack:
            item = self.redo_stack.pop()
            if item == current_state:
                continue
            return item
        return None
    
    def get_whole_histroy(self, current_state):
        return self.history + [current_state] + list(reversed(self.redo_stack))
