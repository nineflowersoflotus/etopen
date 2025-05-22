import pennylane as qml
import numpy as np
from utils import std_shanten, hand_to_counts
from score_calculator import ScoreCalculator


# CONFIGURATION (tweak these for your setup)
TILE_TYPES = 9
N_WALL_TILES = 3
N_CYCLES = 2
INITIAL_HAND = [1, 1, 2, 2, 3, 3, 4, 4, 5, 6, 7, 8, 9, 9, 9]  # Example 14-tile hand

WALL_BITS = N_WALL_TILES * int(np.ceil(np.log2(TILE_TYPES)))
DRAW_BITS = [int(np.ceil(np.log2(N_WALL_TILES - i))) for i in range(N_CYCLES)]
DISCARD_BITS = [int(np.ceil(np.log2(len(INITIAL_HAND) + i + 1))) for i in range(N_CYCLES)]
TOTAL_BITS = WALL_BITS + sum(DRAW_BITS) + sum(DISCARD_BITS)
dev = qml.device("default.qubit", wires=TOTAL_BITS, shots=2000)

def bits_to_wall(bits):
    wall = []
    bits_per_tile = int(np.ceil(np.log2(TILE_TYPES)))
    for i in range(N_WALL_TILES):
        idx = 0
        for j in range(bits_per_tile):
            idx = (idx << 1) | bits[bits_per_tile * i + j]
        if idx >= TILE_TYPES:
            return None
        wall.append(idx)
    return wall

def decode_trajectory(bits, first_discard):
    offset = 0
    bits_per_tile = int(np.ceil(np.log2(TILE_TYPES)))
    wall_bits = bits[offset:offset + N_WALL_TILES * bits_per_tile]
    wall = bits_to_wall(wall_bits)
    if wall is None:
        return None
    offset += N_WALL_TILES * bits_per_tile

    draw_choices = []
    for i, db in enumerate(DRAW_BITS):
        if db == 0:
            draw_choices.append(0)
        else:
            val = 0
            for j in range(db):
                val = (val << 1) | bits[offset + j]
            if val >= len(wall) - i:
                return None
            draw_choices.append(val)
        offset += db

    discard_choices = []
    # The first discard is always fixed!
    discard_choices.append(first_discard)
    for i, db in enumerate(DISCARD_BITS[1:], start=1):
        if db == 0:
            discard_choices.append(0)
        else:
            val = 0
            for j in range(db):
                val = (val << 1) | bits[offset + j]
            if val >= len(INITIAL_HAND) + i:
                return None
            discard_choices.append(val)
        offset += db

    hand = INITIAL_HAND.copy()
    wall_left = wall.copy()
    for draw_idx, discard_idx in zip(draw_choices, discard_choices):
        if draw_idx >= len(wall_left):
            return None
        hand.append(wall_left[draw_idx])
        wall_left.pop(draw_idx)
        if discard_idx >= len(hand):
            return None
        hand.pop(discard_idx)
    return hand

def pretty_hand(hand):
    return " ".join(f"{t}m" for t in sorted(hand))

def is_win(hand):
    if hand is None:
        return False
    return std_shanten(tuple(hand_to_counts(hand))) == -1

scorecalc = ScoreCalculator()

def run_qae_for_discard(first_discard, discard0_offset, discard0_bits):
    discard0_bin = [int(x) for x in format(first_discard, f'0{discard0_bits}b')]

    @qml.qnode(dev)
    def circuit():
        for i in range(TOTAL_BITS):
            if discard0_offset <= i < discard0_offset + discard0_bits:
                continue
            qml.Hadamard(wires=i)
        for b, wire in zip(discard0_bin, range(discard0_offset, discard0_offset + discard0_bits)):
            if b == 1:
                qml.PauliX(wires=wire)
        return qml.sample(wires=range(TOTAL_BITS))

    samples = circuit()
    win_count = 0
    total_count = 0
    score_sum = 0
    for bits in samples:
        hand = decode_trajectory(bits, first_discard)
        if hand is not None:
            total_count += 1
            if is_win(hand):
                win_count += 1
                # --- Score Calculation ---
                # Determine the winning tile: last drawn tile
                # (Assume the last tile added was the win tile)
                win_tile = hand[-1]
                # You may need to reconstruct melds if possible; for now, assume fully closed hand
                result = scorecalc.score(full_hand=hand, melds=[], win_tile=win_tile, is_tsumo=True, riichi=False)
                score_sum += result['points']
    win_prob = win_count / total_count if total_count else 0
    ev = score_sum / total_count if total_count else 0
    return win_prob, ev, total_count

def main():
    # Offsets for first discard in the register
    discard0_offset = WALL_BITS + sum(DRAW_BITS)
    discard0_bits = DISCARD_BITS[0]
    print(f"Initial hand: {pretty_hand(INITIAL_HAND)}")
    print(f"Evaluating quantum win probability for all possible first discards...")

    # Try every possible initial discard index
    results = []
    for discard_idx in range(len(INITIAL_HAND)):
        win_prob, ev, total = run_qae_for_discard(discard_idx, discard0_offset, discard0_bits)
        print(f"  Discard {discard_idx} ({INITIAL_HAND[discard_idx]}m): Win probability = {win_prob:.6f}, EV = {ev:.2f}  (samples: {total})")
    print("\nSummary:")
    for idx, tile, prob, n in results:
        print(f"Discarding tile {idx} ({tile}m): Win probability {prob:.4f} (n={n})")

    

if __name__ == "__main__":
    main()
