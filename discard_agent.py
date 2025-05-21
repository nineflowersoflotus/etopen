from itertools import permutations
from collections import Counter
from tqdm import tqdm

from score_calculator import ScoreCalculator
from utils import std_shanten, pretty

_sc = ScoreCalculator()


def all_wall_draws(num_draws):
    return list(permutations(range(34), num_draws))

def compute_scores_for_discard(base_hand, discard, num_draws_left):
    hand_minus = base_hand.copy()
    hand_minus.remove(discard)
    scores = []
    wall_draws = all_wall_draws(num_draws_left)
    best_score = 0
    best_trajectory = None  # (draws, hand_at_end)
    for draws in tqdm(wall_draws,
                      desc=f"Scoring discard {pretty(discard)} ({num_draws_left} draws left)",
                      unit="draw", leave=False):
        h = hand_minus + list(draws)
        counts = Counter(h)
        if any(c > 4 for c in counts.values()) or std_shanten(tuple(counts[i] for i in range(34))) != -1:
            scores.append(0)
            continue
        full_hand = []
        for t, c in counts.items():
            full_hand += [t]*c
        try:
            pts = _sc.score(full_hand, melds=[], win_tile=full_hand[0])["points"]
        except Exception:
            pts = 0
        scores.append(pts)
        if pts > best_score:
            best_score = pts
            best_trajectory = (draws, h.copy())
    return scores, best_score, best_trajectory

def evaluate_discards(hand14, num_draws_left=3):
    results = []
    wall_draws = all_wall_draws(num_draws_left)
    total_sequences = len(wall_draws)
    best_global = None
    best_global_score = -1
    best_global_discard = None
    best_global_trajectory = None

    for discard in set(hand14):
        scores, best_score, best_trajectory = compute_scores_for_discard(hand14, discard, num_draws_left)
        win_scores = [s for s in scores if s > 0]
        n_wins = len(win_scores)
        p_win = n_wins / total_sequences
        avg_win = (sum(win_scores) / n_wins) if n_wins else 0
        ev = p_win * avg_win

        if best_score > best_global_score:
            best_global_score = best_score
            best_global_trajectory = (discard, best_trajectory)
            best_global_discard = discard

        results.append({
            'discard': discard,
            'p_win': p_win,
            'avg_win': avg_win,
            'ev': ev,
            'best_score': best_score,
            'best_trajectory': best_trajectory,
        })
    best = max(results, key=lambda x: x['ev'])
    # Attach global-best trajectory for use in UI
    best['global_best_trajectory'] = best_global_trajectory
    best['global_best_score'] = best_global_score
    return results, best

if __name__ == "__main__":
    sample_hand = [0,1,2, 9,10,11, 18,19,20, 27,28,29, 5, 6]
    results, best = evaluate_discards(sample_hand, num_draws_left=3)
    print("All discards:")
    for r in results:
        print(f"  {pretty(r['discard'])}: P(win)={r['p_win']:.3f}, "
              f"AvgPts|win={r['avg_win']:.1f}, EV={r['ev']:.1f}, BestPts={r['best_score']}")
    print("\n>> Best discard:", pretty(best['discard']))
    print(">> Highest scoring trajectory:", best['global_best_trajectory'])
