import argparse
import pygame

from config import *
from dashboard_helpers import *

from polyphonic_player import PolyphonicPlayer


help_message = """

click nodes to turn them on/off

click with the right button on an active node to stash it, and then click on some other inactive node with the left button to change old node to new one
you can do this to multiple nodes at once, for example click 3 nodes with right and then 3 nodes with left

press ESC to quit
press 0 to turn everything off

to save the chord, press SPACE and then some key
to load a chord just pressed the key you used for saving

scroll on a node to change it's volume

left/right arrows undo/redo chord changes

pressing b toggles binding view

pressing h saves the whole history to the current save
"""

# ! load command line arguments
parser = argparse.ArgumentParser(
    description="Pythagoras",
    epilog=help_message,
    formatter_class=argparse.RawDescriptionHelpFormatter,
)
parser.add_argument(
    "-p",
    "--placement",
    type=str,
    default="logarithmic",
    help=f"possible values: {list(placement_matrices.keys())}",
)
parser.add_argument(
    "-l",
    "--load",
    type=str,
    default=None,
    help="load some set of chords - specify the name of the save in saved_chords.txt file",
)
parser.add_argument(
    "-f",
    "--base-freq",
    type=int,
    default=10,
    help="all numbers will be multiplied by this number to get frequencies in Hz",
)
parser.add_argument(
    "-n",
    "--number-limit",
    type=int,
    default=600,
    help="draw numbers up to this number",
)
args = parser.parse_args()
placement_matrix = placement_matrices[args.placement]
placement_matrix = placement_matrix[:, : len(primes)]

chords_saver = ChordsSaver()
if args.load is not None:
    # ! load the saved chords
    saved_chords = chords_saver.get_save(args.load)
else:
    saved_chords = chords_saver.create_new_save()
undo_handler = UndoHandler(saved_chords.get("history", []))
print()

drawer = Drawer(placement_matrix, args.number_limit)
drawer.create_graph()
drawer.draw_graph()
player = PolyphonicPlayer(base_freq=args.base_freq)
player.start()

notes_to_change_from = []
notes_to_change_to = []
game_over = False
await_key_to_save_chord = False
binding_view = False
while not game_over:
    pygame.time.wait(20)
    for event in pygame.event.get():
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
            # ! arrows undo chord switches
            elif event.key == pygame.K_LEFT:
                chord = undo_handler.undo(player.get_chord())
                if chord is not None:
                    player.set_chord(chord)
                    drawer.draw_chord(chord)
            # ! redo
            elif event.key == pygame.K_RIGHT:
                chord = undo_handler.redo(player.get_chord())
                if chord is not None:
                    player.set_chord(chord)
                    drawer.draw_chord(chord)
            # ! b toggles binding view
            elif event.key == pygame.K_b:
                if binding_view:
                    binding_view = False
                    drawer.draw_graph()
                else:
                    binding_view = True
                    drawer.draw_binding_view(player.get_chord())
            # ! h saves the whole history
            elif event.key == pygame.K_h:
                saved_chords["history"] = undo_handler.get_whole_histroy(player.get_chord())
                print("history saved")
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
                    # ! load chord
                    if keyname in saved_chords:
                        chord = saved_chords[keyname]
                        player.set_chord(chord)
                        drawer.draw_chord(chord)

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
                            undo_handler.save(player.get_chord())
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
                player.move_note(clicked_node, volume_change=1 / 1.1)

            pygame.display.update()

player.kill()
player.join()
pygame.quit()
chords_saver.save_all_saves()
print(f"save name: {chords_saver.last_loaded_save_name}")
