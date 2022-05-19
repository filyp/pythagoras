import argparse
import pygame
import numpy as np
import networkx as nx

from config import *
from dashboard_helpers import *


help_message = """

click nodes to toggle
click with right button to stash this node, and then click on some other with left to change old ones to new

press ESC to quit
press 0 to reset notes

to save the chord, press SPACE and then some key
to load a chord just pressed the key you used for saving
"""


# ! load command line arguments
parser = argparse.ArgumentParser(description='Pythagoras', epilog=help_message)
parser.add_argument('-p', '--placement', type=str, default='clear', help=f'possible values: {list(placement_matrices.keys())}')
parser.add_argument('-l', '--load_chords', type=int, default=None, help='load some set of chords - specify the line number in saved_chords.txt file')
args = parser.parse_args()
placement_matrix = placement_matrices[args.placement]

if args.load_chords is not None:
    # ! load the saved chords
    saved_chords = load_chords(args.load_chords)
else:
    saved_chords = dict()
original_saved_chords = saved_chords.copy()
print()

drawer = Drawer(placement_matrix)
drawer.draw_graph()
pygame.display.update()

notes_to_change_from = []
notes_to_change_to = []
game_over = False
await_key_to_save_chord = False
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
                drawer.deactivate_all()
                pygame.display.update()
            # ! space saves chord
            elif event.key == pygame.K_SPACE:
                await_key_to_save_chord = True
            else:
                if await_key_to_save_chord:
                    saved_chords[event.key] = drawer.player.get_chord()
                    keyname = pygame.key.name(event.key)
                    print(f"saved chord {keyname}: {saved_chords[event.key]}")
                    await_key_to_save_chord = False
                else:
                    # load chord
                    if event.key in saved_chords:
                        chord = saved_chords[event.key]
                        drawer.set_chord(chord)


        # ! detect clicks
        if event.type == pygame.MOUSEBUTTONDOWN:
            clicked_node = drawer.get_clicked_node(event.pos)
            if clicked_node is None:
                continue

            # clicked a circle - now check if it was already clicked
            if drawer.is_active(clicked_node) and event.button == 1:
                # ! just deactivate
                drawer.deactivate_node(clicked_node)
            elif drawer.is_active(clicked_node) and event.button == 3:
                # ! mark it for change
                notes_to_change_from.append(clicked_node)
            elif not drawer.is_active(clicked_node) and event.button == 1:
                if notes_to_change_from == []:
                    # ! just activate immediately
                    drawer.activate_node(clicked_node)
                else:
                    notes_to_change_to.append(clicked_node)
                    if len(notes_to_change_from) == len(notes_to_change_to):
                        # ! switch all
                        for note in notes_to_change_from:
                            drawer.deactivate_node(note)
                            notes_to_change_from = []
                        for note in notes_to_change_to:
                            drawer.activate_node(note)
                            notes_to_change_to = []
            elif not drawer.is_active(clicked_node) and event.button == 3:
                # ! invalid move
                pass
            # ! scrolling changes volume
            elif event.button == 4:
                print("scrolled up")
            elif event.button == 5:
                print("scrolled down")

            pygame.display.update()

drawer.quit()

if original_saved_chords != saved_chords:
    # save the chords to a file
    save_chords(saved_chords)


# TODO change chords smoothly
# implemetn settin gvolumes
# when changing notes, keep the old volumes