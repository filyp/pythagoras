import numpy as np

white = (255, 255, 255)
black = (0, 0, 0)
yellow = (255, 255, 0)

# brown = (139, 69, 19)
brown = (100, 50, 13)
blue = (0, 0, 100)
orange = (255, 165, 0)
light_blue = (0, 191, 255)

resolution = (2560, 1440)
# resolution = (3920, 2160)
n_limit = 325
displacement = resolution[0] * 0.1
circle_size = resolution[0] * 0.009
text_size = circle_size * 0.9
margin = 0.1  # of height

primes = [2, 3, 5]
draw_lines_for_ratios = [   # ratio, inactive_color, active_color
    (2, blue, light_blue),
    (3/2, blue, light_blue),
    (4/3, blue, light_blue),
    (5/3, brown, orange),
    (5/4, brown, orange),
    (6/5, brown, orange),
]
avoid_numbers = [125, 250, 375, 243]

# placement_matrix = np.array([
#     [1, 0.500, 0.500],
#     [0, -0.866, -0.289],
# ])
# placement_matrix = np.array([
#     [1, 1.500, 2.000],
#     [0, -0.866, -0.577],
# ])
placement_matrix = np.array([
    [1, 1.500, 2.030],
    [0, -0.866, -0.300],
])