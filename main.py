import pennylane as qml
import numpy as np
from collections import Counter
from score_calculator import ScoreCalculator
from utils import pretty, shuffled_zero_to_33, std_shanten
from tqdm import tqdm
hand14 = [0, 0, 1, 1, 2, 2, 3, 3, 4, 5, 6, 7, 8, 8]
sc = ScoreCalculator()
def future_hands_scores(hand14, discard_tile, wall):
    base_hand = hand14.copy()
    base_hand.remove(discard_tile)
    n = len(wall)
    hands_scores = []
    for i in range(n):
        draw1 = wall[i]
        wall1 = wall[:i] + wall[i+1:]
        hand1 = base_hand + [draw1]  
        for d1 in set(hand1):
            hand2 = hand1.copy()
            hand2.remove(d1)
            for j in range(len(wall1)):
                draw2 = wall1[j]
                wall2 = wall1[:j] + wall1[j+1:]
                hand3 = hand2 + [draw2]  
                for d2 in set(hand3):
                    hand4 = hand3.copy()
                    hand4.remove(d2)
                    for k in range(len(wall2)):
                        draw3 = wall2[k]
                        hand5 = hand4 + [draw3]  
                        counts = Counter(hand5)
                        if all(c <= 4 for c in counts.values()):
                            hand_counts = [0]*34
                            for tid in hand5:
                                hand_counts[tid] += 1
                            if std_shanten(tuple(hand_counts)) == -1:
                                full_hand = []
                                for tid, count in enumerate(hand_counts):
                                    full_hand += [tid]*count
                                try:
                                    score = sc.score(full_hand, melds=[], win_tile=full_hand[0])["points"]
                                except Exception:
                                    score = 0
                            else:
                                score = 0
                            hands_scores.append(score)
    return hands_scores
def qae_amplitude(scores):
    n_outcomes = len(scores)
    n_qubits = int(np.ceil(np.log2(n_outcomes)))
    ancilla = n_qubits
    wires = n_qubits + 1
    WIN_ORACLE = np.array([1 if s > 0 else 0 for s in scores])
    def apply_uniform_superposition():
        for i in range(n_qubits):
            qml.Hadamard(wires=i)
    def quantum_oracle():
        for idx in range(n_outcomes):
            if WIN_ORACLE[idx]:
                bits = [(idx >> i) & 1 for i in range(n_qubits)]
                for i, bit in enumerate(bits):
                    if bit == 0:
                        qml.PauliX(wires=i)
                qml.MultiControlledX(wires=list(range(n_qubits)) + [ancilla])
                for i, bit in enumerate(bits):
                    if bit == 0:
                        qml.PauliX(wires=i)
    dev = qml.device("default.qubit", wires=wires)
    @qml.qnode(dev)
    def qae_circuit():
        apply_uniform_superposition()
        quantum_oracle()
        return qml.probs(wires=ancilla)
    probs = qae_circuit()
    return probs[1]
def qae_ev_for_discard(scores, qae_amp=None):
    n_outcomes = len(scores)
    if qae_amp is None:
        qae_amp = qae_amplitude(scores)
    mean_score_all = np.mean(scores)
    mean_score_win = np.mean([s for s in scores if s > 0]) if np.sum(np.array(scores) > 0) > 0 else 0
    win_rate = np.sum(np.array(scores) > 0) / n_outcomes
    ev_qae = mean_score_win * qae_amp
    return ev_qae, mean_score_all, win_rate
def print_ascii_bar_chart(labels, values, max_height=10):
    max_val = max(values) if max(values) > 0 else 1
    heights = [int((v / max_val) * max_height) for v in values]
    for row in range(max_height, 0, -1):
        line = ""
        for h in heights:
            if h >= row:
                line += "  |  "
            else:
                line += "     "
        print(line)
    label_line = ""
    for lbl in labels:
        label_line += f"{lbl:^5}"
    print(label_line)
    print()
N = 500  
print(f"\nAveraging QAE EVs for each discard over {N} random walls...")
unique_discards = sorted(set(hand14))
evs_by_discard = {d: [] for d in unique_discards}
counts_by_discard = {d: hand14.count(d) for d in unique_discards}
pretty_by_discard = {d: pretty(d) for d in unique_discards}
for wall_idx in tqdm(range(N), desc="QAE calculations (walls)"):
    wall = shuffled_zero_to_33()[:6]
    for discard_tile in unique_discards:
        scores = future_hands_scores(hand14, discard_tile, wall)
        qae_amp = qae_amplitude(scores)
        ev_qae, mean_score_all, win_rate = qae_ev_for_discard(scores, qae_amp)
        evs_by_discard[discard_tile].append(ev_qae)
results = []
for d in unique_discards:
    avg_ev = np.mean(evs_by_discard[d])
    results.append({
        "discard": d,
        "pretty": pretty_by_discard[d],
        "ev": avg_ev,
        "count": counts_by_discard[d],
    })
results.sort(key=lambda r: -r["ev"])
print("\nQAE EV (mean over walls) per Discard:\n")
labels = [r["pretty"] for r in results]
values = [r["ev"] for r in results]
print_ascii_bar_chart(labels, values)
print("Detailed EVs:")
for r in results:
    print(f"{r['pretty']:>4} (x{r['count']}): EV = {r['ev']:.2f}")
best_tile = results[0]["discard"]
print(f"\nRecommended discard: {pretty(best_tile)} (Avg QAE EV: {results[0]['ev']:.2f})")