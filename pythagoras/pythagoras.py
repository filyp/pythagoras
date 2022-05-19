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

scroll on a node to change it's volume
"""


# ! load command line arguments
parser = argparse.ArgumentParser(description='Pythagoras', epilog=help_message)
parser.add_argument('-p', '--placement', type=str, default='logarithmic', help=f'possible values: {list(placement_matrices.keys())}')
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
player = PolyphonicPlayer(base_freq=10)
player.start()
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
                drawer.clear_all()
                player.turn_off_all()
                pygame.display.update()
            # ! space saves chord
            elif event.key == pygame.K_SPACE:
                await_key_to_save_chord = True
            else:
                keyname = pygame.key.name(event.key)
                if await_key_to_save_chord:
                    saved_chords[keyname] = player.get_chord()
                    print(f"saved chord {keyname}: {saved_chords[keyname]}")
                    await_key_to_save_chord = False
                else:
                    # load chord
                    if keyname in saved_chords:
                        chord = saved_chords[keyname]
                        player.set_chord(chord)
                        drawer.draw_chord(chord)
                        pygame.display.update()

        # ! detect clicks
        if event.type == pygame.MOUSEBUTTONDOWN:
            clicked_node = drawer.get_clicked_node(event.pos)
            if clicked_node is None:
                continue

            # clicked a circle - now check if it was already clicked
            if drawer.is_active(clicked_node) and event.button == 1:
                # ! just deactivate
                drawer.deactivate_node(clicked_node)
                player.remove_note(clicked_node)
            elif drawer.is_active(clicked_node) and event.button == 3:
                # ! mark it for change
                if clicked_node not in notes_to_change_from:
                    notes_to_change_from.append(clicked_node)
            elif not drawer.is_active(clicked_node) and event.button == 1:
                if notes_to_change_from == []:
                    # ! just activate immediately
                    drawer.activate_node(clicked_node)
                    player.add_note(clicked_node, volume=1)
                else:
                    if clicked_node not in notes_to_change_to:
                        notes_to_change_to.append(clicked_node)
                    if len(notes_to_change_from) == len(notes_to_change_to):
                        # ! switch all
                        for freq1, freq2 in zip(notes_to_change_from, notes_to_change_to):
                            drawer.deactivate_node(freq1)
                            drawer.activate_node(freq2)
                            player.move_note(freq1, new_freq=freq2)
                        notes_to_change_from = []
                        notes_to_change_to = []
            elif not drawer.is_active(clicked_node) and event.button == 3:
                # ! invalid move
                pass
            # ! scrolling changes volume
            elif event.button == 4:
                player.move_note(clicked_node, volume_change=1.1)
            elif event.button == 5:
                player.move_note(clicked_node, volume_change=1/1.1)

            pygame.display.update()

player.kill()
player.join()
pygame.quit()

if original_saved_chords != saved_chords:
    # save the chords to a file
    save_chords(saved_chords)
