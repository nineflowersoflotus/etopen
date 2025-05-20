from collections import Counter
from itertools import combinations
YAKU_LIST = [
    'Riichi', 'Double Riichi', 'Ippatsu', 'Menzen Tsumo', 'Pinfu', 'Iipeikou',
    'Tanyao', 'Yakuhai', 'Haitei Raoyue', 'Houtei Raoyui', 'Rinshan Kaihou', 'Chankan',
    'Chanta', 'Sanshoku Doujun', 'Ittsuu', 'Toitoi', 'Sanankou', 'Sanshoku Doukou',
    'Sankantsu', 'Chiitoitsu', 'Honroutou', 'Shousangen',
    'Honitsu', 'Junchantaiyaochu', 'Ryanpeikou',
    'Chinitsu'
]
def id_to_tile(tile_id):
    if tile_id < 27:
        suit = tile_id // 9
        rank = tile_id % 9 + 1
        return (['m','p','s'][suit], rank)
    honors = ['east','south','west','north','white','green','red']
    return ('z', honors[tile_id-27])
class ScoreCalculator:
    def __init__(self):
        pass
    def detect_yakus(self, full_hand, melds, win_tile, is_tsumo=False,
                     riichi=False, last_draw=False, last_discard=False, dora_count=0):
        yakus = {}
        ids = full_hand.copy()
        suits = [tid//9 for tid in ids if tid<27]
        honors_tiles = [tid for tid in ids if tid>=27]
        counts = Counter(ids)
        if riichi:
            yakus['Riichi'] = 1
        if is_tsumo and not melds:
            yakus['Menzen Tsumo'] = 1
        if not melds:
            if max(counts.values()) == 2 and all(tid < 27 for tid in ids):
                pair_tiles = [t for t, c in counts.items() if c == 2]
                if pair_tiles:
                    p = pair_tiles[0]
                    if p % 9 in (0,8):
                        pair_tiles = []
                    elif p >= 27:
                        honor = HONORS[p-27]
                        if honor in (round_wind, seat_wind, player_wind):
                            pair_tiles = []
                if pair_tiles:
                    rem = full_hand.copy()
                    for m in melds:
                        for t in m:
                            rem.remove(t)
                    rem.remove(pair_tiles[0])
                    rem.remove(pair_tiles[0])
                    rem_counts = Counter(rem)
                    if rem_counts[win_tile] == 2:
                        pass
                    else:
                        r = win_tile % 9 + 1
                        s = win_tile // 9
                        if not ((r == 3 and rem_counts[s*9] and rem_counts[s*9+1]) or \
                                (r == 7 and rem_counts[s*9+7] and rem_counts[s*9+8])):
                            if not (0 <= win_tile-1 < 27 and 0 <= win_tile+1 < 27 and \
                                    rem_counts[win_tile-1] and rem_counts[win_tile+1]):
                                yakus['Pinfu'] = 1  
        if not melds:
            seqs = []
            for suit in range(3):
                for r in range(1,8):
                    seq = tuple([suit*9+(r-1), suit*9+r, suit*9+(r+1)])
                    if all(counts[t]>0 for t in seq): seqs.append(seq)
            if any(seqs.count(s)>=2 for s in set(seqs)):
                yakus['Iipeikou'] = 1
        if all((tid<27 and 1<tid%9<8) for tid in ids):
            yakus['Tanyao'] = 1
        for t,c in counts.items():
            if c>=3 and (t>=27 or t//9==3):
                yakus['Yakuhai'] = yakus.get('Yakuhai',0)+1
        if last_draw and is_tsumo:
            yakus['Haitei Raoyue'] = 1
        if last_discard and not is_tsumo:
            yakus['Houtei Raoyui'] = 1
        if last_draw and melds:
            yakus['Rinshan Kaihou'] = 1
        if last_discard and melds:
            yakus['Chankan'] = 1
        if all((tid>=27) or (tid%9 in (0,8)) for tid in ids):
            yakus['Chanta'] = 2
        runs = {r:0 for r in range(1,8)}
        for suit in range(3):
            for r in range(1,8):
                seq = [suit*9+(r-1), suit*9+r, suit*9+(r+1)]
                if all(counts[t]>0 for t in seq): runs[r]+=1
        if any(v==3 for v in runs.values()): yakus['Sanshoku Doujun'] = 2
        for suit in range(3):
            if all(counts[suit*9+i]>0 for i in range(9)):
                yakus['Ittsuu'] = 2
        if all(c in (0,3,4) for c in counts.values()): yakus['Toitoi'] = 2
        closed_trip = sum(1 for t,c in counts.items() if c>=3 and all(t not in m for m in melds))
        if closed_trip>=3: yakus['Sanankou'] = 2
        for r in range(9):
            if all(counts[s*9+r]>=3 for s in range(3)):
                yakus['Sanshoku Doukou'] = 2
        if sum(1 for m in melds if len(m)==4)>=3: yakus['Sankantsu'] = 2
        if sum(1 for c in counts.values() if c==2)==7: yakus['Chiitoitsu'] = 2
        if all((tid>=27) or (tid%9 in (0,8)) for tid in ids): yakus['Honroutou'] = 2
        dragons=[31,32,33]
        if sum(counts[d]>=3 for d in dragons)==2 and any(counts[d]==2 for d in dragons):
            yakus['Shousangen'] = 2
        if len(set(tid//9 for tid in ids if tid<27))==1 and honors_tiles:
            yakus['Honitsu'] = 3
        if all((tid>=27) or (tid%9 in (0,8)) for tid in ids): yakus['Junchantaiyaochu'] = 3
        if not melds:
            seqs = []
            for suit in range(3):
                for r in range(1,8):
                    seq=(suit*9+(r-1),suit*9+r,suit*9+(r+1))
                    if all(counts[t]>0 for t in seq): seqs.append(seq)
            if sum(seqs.count(s) for s in set(seqs) if seqs.count(s)>=2)>=2:
                yakus['Ryanpeikou'] = 3
        if len(set(tid//9 for tid in ids if tid<27))==1 and not honors_tiles:
            yakus['Chinitsu'] = 6
        return yakus
    def calculate_fu(self, full_hand, melds, win_tile, is_tsumo=False):
        fu = 20
        counts = Counter(full_hand)
        for m in melds:
            cnt = Counter(m)
            if len(cnt) == 1:
                t = m[0]
                is_terminal = (t % 9 in (0, 8)) or t >= 27
                if len(m) == 4:
                    fu += 16 if is_terminal else 8
                else:
                    fu += 4 if is_terminal else 2
        rem = full_hand.copy()
        for m in melds:
            for t in m:
                if t in rem:
                    rem.remove(t)
        pair_fu = 0
        for t, c in Counter(rem).items():
            if c == 2 and (t >= 27 or t // 9 == 3):
                pair_fu = 2
                break
        fu += pair_fu
        if is_tsumo:
            fu += 2
        if rem.count(win_tile) == 2:
            fu += 2
        else:
            penchan_fu = 0
            kanchan_fu = 0
            if win_tile < 27:
                rank = win_tile % 9
                suit = win_tile // 9
                if rank == 2 and all(rem.count(suit*9 + i) > 0 for i in (0,1)):
                    penchan_fu = 2
                if rank == 6 and all(rem.count(suit*9 + i) > 0 for i in (7,8)):
                    penchan_fu = 2
                prev_, next_ = win_tile-1, win_tile+1
                if 0 <= prev_ < 27 and 0 <= next_ < 27:
                    if rem.count(prev_) > 0 and rem.count(next_) > 0:
                        kanchan_fu = 2
            fu += max(penchan_fu, kanchan_fu)
        return ((fu + 9) // 10) * 10
    def score(self, full_hand, melds, win_tile,
              is_tsumo=False, riichi=False,
              last_draw=False, last_discard=False, dora_count=0):
        yakus = self.detect_yakus(full_hand, melds, win_tile,
                                  is_tsumo, riichi,
                                  last_draw, last_discard, dora_count)
        han = sum(yakus.values()) + dora_count
        if han <= 0:
            return {'han': 0, 'fu': 0, 'points': 0}
        fu = self.calculate_fu(full_hand, melds, win_tile, is_tsumo)
        limit_base = None
        if han >= 13:
            limit_base = 8000    
        elif han >= 11:
            limit_base = 6000    
        elif han >= 8:
            limit_base = 4000    
        elif han >= 6:
            limit_base = 3000    
        elif han >= 5 or (han == 4 and fu >= 40) or (han == 3 and fu >= 70):
            limit_base = 2000    
        if limit_base is not None:
            base = limit_base
        else:
            base = fu * (2 ** (han + 2))
        points = ((base * 4 + 99) // 100) * 100
        return {'han': han, 'fu': fu, 'points': points}