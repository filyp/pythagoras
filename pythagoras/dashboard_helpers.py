import os
import json
import pathlib

import pygame
import numpy as np
import networkx as nx
import randomname

from config import *
from polyphonic_player import PolyphonicPlayer


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
            print(f"{keyname}: {[freq for freq, _, _ in chord]}")
        self.last_loaded_save_name = save_name

        # * note that save is a dict so it is passes by reference and will be modified
        return save
    
    def save_all_saves(self):
        with open(self.saved_chords_file, "w") as f:
            for save_name, save in self.all_saves.items():
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
        self.coordinate_center = np.array([resolution[1] * margin, resolution[1] * (1 - margin)])

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

    def draw_graph(self):
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
        for ratio, color0, color1 in draw_lines_for_ratios:
            for n1 in self.G.nodes:
                for n2 in self.G.nodes:
                    if n2 / n1 != ratio:
                        continue
                    self.G.add_edge(n1, n2, color0=color0, color1=color1, active=False)
        # ! draw edges
        for u, v, edge_data in self.G.edges.data():
            position1 = self.G.nodes[u]["position"]
            position2 = self.G.nodes[v]["position"]
            pygame.draw.line(self.dis, edge_data["color0"], position1, position2, line_width)
        # ! draw circles
        for n in self.G.nodes:
            self.redraw_circle(self.dis, circle_size, n)

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

    def draw_chord(self, chord):
        # deactivate
        for node in self.G.nodes:
            if self.G.nodes[node]["active"]:
                self.deactivate_node(node)
        # activate
        for freq, volume, _ in chord:
            self.activate_node(freq, volume)


class UndoHandler:
    def __init__(self):
        self.history = []
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
        

