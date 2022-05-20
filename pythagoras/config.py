import numpy as np

white = (255, 255, 255)
black = (0, 0, 0)

blue = (0, 0, 255)
blue_dim = (0, 0, 70)
green = (0, 255, 0)
green_dim = (0, 70, 0)
yellow = (255, 255, 0)
yellow_dim = (70, 70, 0)
orange = (255, 165, 0)
orange_dim = (70, 40, 0)

resolution = (2560, 1440)
# resolution = (3920, 2160)
n_limit = 325
displacement = resolution[0] * 0.1
circle_size = resolution[0] * 0.009
line_width = int(resolution[0] * 0.002)
dot_size = line_width * 3
text_size = circle_size * 0.9
margin = resolution[1] * 0.1

primes = [2, 3, 5]
draw_lines_for_ratios = [  # ratio, inactive_color, active_color
    (2, 1, yellow_dim, yellow),
    # (3, 1, yellow_dim, yellow),
    (3, 2, yellow_dim, yellow),
    (4, 3, yellow_dim, yellow),
    (5, 3, green_dim, green),
    (5, 4, green_dim, green),
    (6, 5, green_dim, green),
    (7, 5, blue_dim, blue),
    (7, 6, blue_dim, blue),
]
avoid_numbers = set([243])
for i in range(10):
    avoid_numbers.add(i * 125)
    avoid_numbers.add(i * 49)

placement_matrices = dict(
    logarithmic=np.array(
        [
            [np.log2(2), np.log2(3), np.log2(5), np.log2(7)],
            [0, -0.866, -0.200, -0.740],
        ]
    ),
    # TODO add a fourth row for the fourth prime
    clear=np.array(
        [
            [1, 1.500, 2.030],
            [0, -0.866, -0.300],
        ]
    ),
    symmetric=np.array(
        [
            [1, 1.500, 2.000],
            [0, -0.866, -0.577],
        ]
    ),
    prime_view=np.array(
        [
            [1, 0.500, 0.500],
            [0, -0.866, -0.289],
        ]
    ),
)