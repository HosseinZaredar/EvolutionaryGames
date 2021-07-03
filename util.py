import os
from os.path import join
import pickle
from pathlib import Path
import shutil

# save players of this generation in file
def save_generation(players, gen_num, mode):
    path = Path(join('checkpoint', mode, str(gen_num)))
    try:
        shutil.rmtree(path)
    except OSError as e:
        pass

    path.mkdir(parents=True, exist_ok=True)
    for i, p in enumerate(players):
        player_path = join(path, str(i))
        with open(player_path, 'wb') as file:
            pickle.dump(p, file)


# load players from file
def load_generation(checkpoint_path):
    files = os.listdir(checkpoint_path)
    prev_players = []
    for f in files:
        with open(join(checkpoint_path, f), 'rb') as file:
            p = pickle.load(file)
            prev_players.append(p)

    return prev_players
