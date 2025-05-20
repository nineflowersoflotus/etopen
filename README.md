
---

# Etopen

*A Quantum-Enhanced Mahjong Discard Analyzer*

---

## Table of Contents

* [Overview](#overview)
* [Features](#features)
* [Algorithms & Methodology](#algorithms--methodology)

  * [Mahjong Hand Evaluation](#mahjong-hand-evaluation)
  * [Quantum Amplitude Estimation (QAE)](#quantum-amplitude-estimation-qae)
  * [Expected Value Computation](#expected-value-computation)
* [Project Structure](#project-structure)
* [Installation](#installation)
* [Usage](#usage)
* [API & Code Reference](#api--code-reference)
* [Development Notes](#development-notes)
* [License](#license)

---

## Overview

**Etopen** is a research-driven tool for optimal discard analysis in Japanese (Riichi) Mahjong, blending classical hand evaluation with **quantum-inspired algorithms** using [PennyLane](https://pennylane.ai/) for quantum circuit simulation.

It answers the question:

> *“Which tile should I discard to maximize my hand’s winning expected value, as estimated by quantum amplitude estimation (QAE) on plausible draws?”*

---

## Features

* **Riichi Mahjong Hand Evaluation**: Supports full scoring, yaku detection, and fu calculation.
* **QAE-based Discard Simulation**: For each discard, simulates all plausible future hands under random wall draws, and estimates win probability using quantum amplitude estimation.
* **Monte Carlo Sampling**: Repeats discard simulations across many randomized walls for robust EV (expected value) estimates.
* **API for Integrating/Extending**: All logic is implemented as importable, extensible Python modules.
* **Pretty Console Output**: ASCII bar charts for EV per discard, summary tables, and a recommended discard.
* **Stateless, Fully Reproducible**: Random seed control and functional code structure.

---

## Algorithms & Methodology

### Mahjong Hand Evaluation

* Tiles are represented as integers `0-33`:

  * Manzu: `0-8`, Pinzu: `9-17`, Souzu: `18-26`, Honors: `27-33`
* Hand scoring (`score_calculator.py`):

  * **Yaku detection**: Recognizes all major 1-han, 2-han, 3-han, and yakuman patterns.
  * **Fu calculation**: Computes hand value using fu points, melds, waits, and terminal/honor rules.
  * **Score calculation**: Applies Japanese scoring rules for han/fu/limit hands.

### Quantum Amplitude Estimation (QAE)

* **Quantum circuit** (via PennyLane):

  * For a batch of possible future hands after a discard, win/loss outcomes are encoded as amplitudes in a quantum state.
  * A quantum oracle marks winning outcomes.
  * **Amplitude estimation** extracts the (simulated) quantum probability of drawing a win.
* **Simulation**: All quantum operations run in simulation (classical hardware) for research and development.

### Expected Value Computation

* For each discard in your 14-tile hand:

  * Enumerate all plausible three-draw sequences after discarding that tile, using a randomly shuffled wall.
  * For each future hand, score it using mahjong rules.
  * **QAE**: Simulate a quantum amplitude estimation to measure win probability.
  * Compute expected win value as `EV = mean(win hand value) × QAE win probability`.
  * Repeat across many random walls (default: 500) and average results.
* **Best discard**: The tile with highest mean QAE EV is recommended.

---

## Project Structure

```
etopen/
├── main.py                # Entry point. Discard simulation, QAE, and reporting.
├── score_calculator.py    # Full hand/yaku/fu scoring engine.
├── utils.py               # Hand parsing, tile pretty-printing, shanten/ukeire calculators, wall shuffling, etc.
├── README.md              # You are here!
```

---

## Installation

### 1. Clone the repository

```sh
git clone https://github.com/yourusername/etopen.git
cd etopen
```

### 2. Install dependencies

**Python 3.8+** recommended.
All dependencies are installable via pip:

```sh
pip install -r requirements.txt
```

If `requirements.txt` is missing, install manually:

```sh
pip install pennylane numpy tqdm
```

---

## Usage

### Quickstart

Run the main analyzer on the included example hand:

```sh
python main.py
```

* By default, `main.py` runs an analysis on `hand14 = [0, 0, 1, 1, 2, 2, 3, 3, 4, 5, 6, 7, 8, 8]`.
* It simulates all possible discards, performs QAE-based expected value computation for each, and prints results as a bar chart.

#### Example Output

```
Averaging QAE EVs for each discard over 500 random walls...
QAE EV (mean over walls) per Discard:

   |        |     
   |  |     |  | 
   |  |     |  | 
--------------------
 1m  2m  3m  ... 8m

Detailed EVs:
 1m (x2): EV = 823.20
 2m (x2): EV = 851.34
 ...
Recommended discard: 2m (Avg QAE EV: 851.34)
```

### Custom Hands

Edit the `hand14` variable in `main.py` to analyze a different hand (use tile IDs or adapt the parsing function in `utils.py`).

---

## API & Code Reference

### main.py

* **future\_hands\_scores(hand14, discard\_tile, wall)**: Enumerate all plausible hands after discarding `discard_tile` and drawing three new tiles, scoring each one.
* **qae\_amplitude(scores)**: Runs simulated quantum amplitude estimation to estimate probability of a win among candidate hands.
* **qae\_ev\_for\_discard(scores, qae\_amp=None)**: Computes expected value of a discard, combining mean win value with QAE win probability.
* **print\_ascii\_bar\_chart(labels, values)**: Pretty bar chart output.
* **Main logic**: Monte Carlo loop over random walls, reporting results and recommending best discard.

### utils.py

* **encode\_features(hand14, discard\_tile, dora\_indicator)**: Generate feature vector for ML/research purposes.
* **std\_shanten(tiles)**: Calculate standard shanten number (distance from tenpai).
* **ukeire(tiles, wall\_counts)**: Calculate ukeire (number of winning tiles).
* **pretty(tile\_index)**: Pretty-print a tile (e.g., `3m`, `7s`, `白`).
* **hand\_to\_counts(hand)**: Convert hand list to tile count vector.
* **shuffled\_zero\_to\_33()**: Generate a randomized wall (all tiles, shuffled).
* **parse\_mahjong\_hand(s)**: Parse a textual mahjong hand (like `'112233m4455p77z'`).

### score\_calculator.py

* **ScoreCalculator**:

  * **detect\_yakus(...)**: Returns yaku and han breakdown for a hand.
  * **calculate\_fu(...)**: Calculates fu for a hand.
  * **score(...)**: Computes `{'han', 'fu', 'points'}` for a given hand, melds, and win tile.

---

## Development Notes

* **Quantum backend**: Simulated via [PennyLane](https://pennylane.ai/)’s `default.qubit` device. No real quantum hardware is required.
* **Hand limitations**: Melded/open hands supported in scoring; QAE simulations assume a closed hand for simplicity.
* **Performance**: The algorithm is exponential in the number of draws and hand permutations—keep `N` (walls) small for quick runs, or high for accuracy.
* **Extending**: For real-world play, integrate with a full game engine, add dora handling, and interface with actual hand parsing UI.

---

## License

This project is open source and available under the [MIT License](LICENSE).

---

### Citation / Academic Use

If you use Etopen for research or publications, please cite or credit the project!

---

**Contributions and PRs are welcome! Enjoy exploring quantum mahjong\~**

---

*Mahjong is love, mahjong is life… and now, quantum!*
