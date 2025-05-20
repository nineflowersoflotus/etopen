import random
from functools import lru_cache
from score_calculator import ScoreCalculator
import math
from collections import Counter
import pennylane as qml
from pennylane import numpy as np
from pennylane.templates import QuantumMonteCarlo
from tqdm import tqdm
from score_calculator import ScoreCalculator
def encode_features(hand14, discard_tile, dora_indicator):
    counts = hand_to_counts(hand14)
    hand_feat = np.array(counts, dtype=np.float32) / 4.0
    disc_feat = np.zeros(34, dtype=np.float32); disc_feat[discard_tile] = 1.0
    dora_feat = np.zeros(34, dtype=np.float32); dora_feat[dora_indicator] = 1.0
    return np.concatenate([hand_feat, disc_feat, dora_feat])
NUM_TILES = 34
@lru_cache(maxsize=None)
def suit_dfs(counts):
    best = (0, 0)
    for i, c in enumerate(counts):
        if c:
            break
    else:
        return best
    c_list = list(counts)
    if c_list[i] >= 3:
        c_list[i] -= 3
        r, t = suit_dfs(tuple(c_list)); best = max(best, (r + 1, t)); c_list[i] += 3
    if i <= 6 and all(c_list[j] for j in (i, i+1, i+2)):
        for j in (i, i+1, i+2): c_list[j] -= 1
        r, t = suit_dfs(tuple(c_list)); best = max(best, (r + 1, t))
        for j in (i, i+1, i+2): c_list[j] += 1
    if c_list[i] >= 2:
        c_list[i] -= 2
        r, t = suit_dfs(tuple(c_list)); best = max(best, (r, t + 1)); c_list[i] += 2
    if i <= 7 and c_list[i] and c_list[i+1]:
        c_list[i] -= 1; c_list[i+1] -= 1
        r, t = suit_dfs(tuple(c_list)); best = max(best, (r, t + 1))
        c_list[i] += 1; c_list[i+1] += 1
    if i <= 6 and c_list[i] and c_list[i+2]:
        c_list[i] -= 1; c_list[i+2] -= 1
        r, t = suit_dfs(tuple(c_list)); best = max(best, (r, t + 1))
        c_list[i] += 1; c_list[i+2] += 1
    c_list[i] = 0
    best = max(best, suit_dfs(tuple(c_list)))
    return best
@lru_cache(maxsize=None)
def honor_dfs(counts):
    best = (0, 0)
    for i, c in enumerate(counts):
        if c:
            break
    else:
        return best
    c_list = list(counts)
    if c_list[i] >= 3:
        c_list[i] -= 3
        r, t = honor_dfs(tuple(c_list)); best = max(best, (r + 1, t)); c_list[i] += 3
    if c_list[i] >= 2:
        c_list[i] -= 2
        r, t = honor_dfs(tuple(c_list)); best = max(best, (r, t + 1)); c_list[i] += 2
    c_list[i] -= 1
    r, t = honor_dfs(tuple(c_list)); best = max(best, (r, t + 1))
    return best
@lru_cache(maxsize=None)
def std_shanten(tiles):
    def meld_taatsu(counts):
        m = t = 0
        for b in (0, 9, 18):
            r, s = suit_dfs(tuple(counts[b:b+9])); m += r; t += s
        r2, s2 = honor_dfs(tuple(counts[27:])); return m + r2, t + s2
    cnts = list(tiles)
    best = 8
    for i in range(NUM_TILES):
        if cnts[i] >= 2:
            cnts[i] -= 2
            m, t = meld_taatsu(cnts)
            best = min(best, 8 - 2*m - min(t, 4-m) - 1)
            cnts[i] += 2
    m, t = meld_taatsu(cnts)
    return min(best, 8 - 2*m - min(t, 4-m))
@lru_cache(maxsize=None)
def ukeire(tiles, wall_counts):
    t_list = list(tiles)
    base = std_shanten(tuple(t_list))
    u = 0
    for i in range(NUM_TILES):
        wc = wall_counts[i]
        if not wc:
            continue
        t_list[i] += 1
        if std_shanten(tuple(t_list)) < base:
            u += wc
        t_list[i] -= 1
    return u
def pretty(tile_index):
    if 0 <= tile_index < 27:
        num = (tile_index % 9) + 1
        suit = ['m', 'p', 's'][tile_index // 9]
        return f"{num}{suit}"
    honors = ['東', '南', '西', '北', '白', '發', '中']
    return honors[tile_index - 27]
def index_to_tile(i):
    return i
NUM_TILES, COPIES = 34, 4
ALL_TILES = [i for i in range(NUM_TILES) for _ in range(COPIES)]
def hand_to_counts(hand):
    cnt = [0]*NUM_TILES
    for t in hand:
        cnt[t] += 1
    return cnt
def shuffled_zero_to_33():
    arr = np.tile(np.arange(34), 4)  
    np.random.shuffle(arr)
    return arr.tolist()
def parse_mahjong_hand(s):
    s = s.replace("　", " ")  
    parts = s.strip().split()
    tiles = []
    for part in parts:
        numbers = ''
        for ch in part:
            if ch.isdigit():
                numbers += ch
            else:
                suit = ch
                for n in numbers:
                    n = int(n)
                    if suit == 'm':
                        tiles.append(n-1)
                    elif suit == 'p':
                        tiles.append(9 + n-1)
                    elif suit == 's':
                        tiles.append(18 + n-1)
                    elif suit == 'z':
                        tiles.append(27 + n-1)
                    else:
                        raise ValueError(f"Unknown suit: {suit}")
                numbers = ''
    return tiles