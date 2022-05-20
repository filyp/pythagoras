from collections import Counter


def get_ratios():
    with open("ratios.csv") as file:
        for line in file:
            for elem in line.split(",")[2:]:
                if int(elem) != 0:
                    yield int(elem)


counts = Counter(get_ratios())
counts_list = list(counts.items())
counts_list.sort(key=lambda i: i[1])  # , reverse=True)
for pair in counts_list:
    print(pair)
