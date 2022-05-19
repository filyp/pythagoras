import pygame
import numpy as np
import networkx as nx

from config import *
from dashboard_helpers import *
from polyphonic_player import PolyphonicPlayer


"""
HELP

click nodes to toggle
click with right button to stash this node, and then click on some other with left to change old ones to new

press ESC to quit
press 0 to reset notes

to save the chord, press SPACE and then some key
to load a chord just pressed the key you used for saving
"""


pygame.display.init()
pygame.font.init()
dis = pygame.display.set_mode(resolution)
pygame.display.set_caption("Pythagoras")
font = pygame.font.SysFont('arial', int(text_size))
coordinate_center = np.array([resolution[1] * margin, resolution[1] * (1-margin)])

player = PolyphonicPlayer(base_freq=10)
# player.volumes = volumes
player.start()
G = nx.Graph()


def redraw_circle(dis, circle_size, n):
    if G.nodes[n]["active"]:
        color = yellow
    else:
        color = white
    pygame.draw.circle(dis, color, G.nodes[n]["position"], circle_size)
    # print a number in the circle
    text = font.render(str(n), True, black)
    text_rect = text.get_rect()
    text_rect.center = G.nodes[n]["position"]
    dis.blit(text, text_rect)


def activate_node(n):
    G.nodes[n]['active'] = True
    player.add_note(n)
    # paint edges
    for neighbor in G[n]:
        edge = G[n][neighbor]
        if G.nodes[neighbor]['active']:
            edge["active"] = True
            pygame.draw.line(dis, edge["color1"], edge["position1"], edge["position2"], 5)
            redraw_circle(dis, circle_size, neighbor)
    redraw_circle(dis, circle_size, n)
                        

def deactivate_node(n):
    G.nodes[n]['active'] = False
    player.remove_note(n)
    # paint edges
    for neighbor in G[n]:
        edge = G[n][neighbor]
        if G.nodes[neighbor]['active']:
            # there was an active edge
            edge["active"] = False
            pygame.draw.line(dis, edge["color0"], edge["position1"], edge["position2"], 5)
            redraw_circle(dis, circle_size, neighbor)
    redraw_circle(dis, circle_size, n)


# draw lines
for ratio, color0, color1 in draw_lines_for_ratios:
    for n1 in range(1, n_limit + 1):
        for n2 in range(1, n_limit + 1):
            if n2 / n1 != ratio:
                continue
            if n1 in avoid_numbers or n2 in avoid_numbers:
                continue
            decomposition1 = decompose_into_small_primes(n1, primes=primes)
            decomposition2 = decompose_into_small_primes(n2, primes=primes)
            if decomposition1 is None or decomposition2 is None:
                continue
            position1 = (placement_matrix @ decomposition1) * displacement + coordinate_center
            position2 = (placement_matrix @ decomposition2) * displacement + coordinate_center
            pygame.draw.line(dis, color0, position1, position2, 5)
            G.add_edge(n1, n2, color0=color0, color1=color1, position1=position1, position2=position2, active=False)

# draw circles
circle_positions = dict()
for n in range(1, n_limit + 1):
    if n in avoid_numbers:
        continue
    decomposition = decompose_into_small_primes(n, primes=primes)
    if decomposition is None:
        continue
    position = (placement_matrix @ decomposition) * displacement + coordinate_center
    circle_positions[n] = position
    G.add_node(n, active=False, position=position)
    redraw_circle(dis, circle_size, n)



pygame.display.update()



notes_to_change_from = []
notes_to_change_to = []
game_over = False
await_key_to_save_chord = False
saved_chords = dict()
while not game_over:
    pygame.time.wait(20)
    for event in pygame.event.get():
        # print(event)
        # check exit
        if event.type == pygame.QUIT:
            game_over = True
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                game_over = True
            # ! 0 resets notes
            elif event.key == pygame.K_0:
                for node in G.nodes:
                    if G.nodes[node]['active']:
                        deactivate_node(node)
            # ! space saves chord
            elif event.key == pygame.K_SPACE:
                await_key_to_save_chord = True
            else:
                if await_key_to_save_chord:
                    # save chord TODO
                    saved_chords[event.key] = [note for note in G.nodes if G.nodes[note]['active']]
                    await_key_to_save_chord = False
                else:
                    # load chord
                    if event.key in saved_chords:
                        chord = saved_chords[event.key]
                        # deactivate
                        for node in G.nodes:
                            if G.nodes[node]['active']:
                                deactivate_node(node)
                        # activate
                        for note in chord:
                            activate_node(note)
                        pygame.display.update()


        # ! detect clicks
        if event.type == pygame.MOUSEBUTTONDOWN:
            click_pos = event.pos
            for n, position in circle_positions.items():
                if np.linalg.norm(click_pos - position) < circle_size:
                    # clicked a circle - now check if it was already clicked
                    if G.nodes[n]['active'] and event.button == 1:
                        # ! just deactivate
                        deactivate_node(n)
                    elif G.nodes[n]['active'] and event.button == 3:
                        # ! mark it for change
                        notes_to_change_from.append(n)
                    elif not G.nodes[n]['active'] and event.button == 1:
                        if notes_to_change_from == []:
                            # ! just activate immediately
                            activate_node(n)
                        else:
                            notes_to_change_to.append(n)
                            if len(notes_to_change_from) == len(notes_to_change_to):
                                # ! switch all
                                for note in notes_to_change_from:
                                    deactivate_node(note)
                                    notes_to_change_from = []
                                for note in notes_to_change_to:
                                    activate_node(note)
                                    notes_to_change_to = []
                    elif not G.nodes[n]['active'] and event.button == 3:
                        # ! invalid move
                        pass

                    pygame.display.update()
                    # print(player.notes)
                    # print(notes_to_change_from, notes_to_change_to)


player.kill()
player.join()
pygame.quit()

print(saved_chords)


# TODO change chord smoothly