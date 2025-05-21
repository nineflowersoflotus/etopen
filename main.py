import streamlit as st
from PIL import ImageFont, ImageDraw, Image
import numpy as np
import importlib.util
import sys
import os

# ---- Import your discard agent dynamically ----
spec = importlib.util.spec_from_file_location("discard_agent", "discard_agent.py")
discard_agent = importlib.util.module_from_spec(spec)
sys.modules["discard_agent"] = discard_agent
spec.loader.exec_module(discard_agent)

# ---- Import utils for pretty and tile parsing ----
spec2 = importlib.util.spec_from_file_location("utils", "utils.py")
utils = importlib.util.module_from_spec(spec2)
sys.modules["utils"] = utils
spec2.loader.exec_module(utils)

def index_to_tile_string(i):
    # i is 0-33
    if 0 <= i < 9: return f"{i+1}m"
    if 9 <= i < 18: return f"{i-8}p"
    if 18 <= i < 27: return f"{i-17}s"
    if 27 <= i < 34: return f"{i-26}z"
    return "?"

def tile_to_char(tile):
    mapping = {
        '1z': '1',  # East wind
        '2z': '2',  # South wind
        '3z': '3',  # West wind
        '4z': '4',  # North wind
        '5z': '5',  # White dragon
        '6z': '6',  # Green dragon
        '7z': '7',  # Red dragon
        **{f"{i+1}m": "qwertyuiop"[i] for i in range(9)},
        **{f"{i+1}p": "asdfghjkl"[i] for i in range(9)},
        **{f"{i+1}s": "zxcvbnm,."[i] for i in range(9)},
    }
    return mapping.get(tile, '?')

def draw_hand(hand, font, tile_size=48):
    chars = [tile_to_char(index_to_tile_string(t)) for t in hand]

    text = ''.join(chars)
    w = tile_size * len(chars)
    h = tile_size + 20
    img = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.text((0, 0), text, font=font, fill='white')
    return img

def parse_hand_input(txt):
    try:
        hand = utils.parse_mahjong_hand(txt)
        if len(hand) != 14:
            return None, f"Hand must have 14 tiles (you entered {len(hand)})."
        return hand, None
    except Exception as e:
        return None, f"Parse error: {e}"

# ---- Streamlit UI ----
st.set_page_config(page_title="Riichi Mahjong EV Calculator", layout="centered")
st.markdown(
    "<h1 style='display:flex; align-items:center; gap:20px;'>"
    "Riichi Mahjong EV Calculator <span style='font-size:1.1em;'>🀄</span>"
    "</h1>",
    unsafe_allow_html=True
)

st.markdown("Enter your **14-tile hand** (e.g. <code>123m 456p 789s 11z 777z</code>), then press <b>Evaluate Discard</b>!", unsafe_allow_html=True)

# --- Font loading
try:
    font = ImageFont.truetype("mahjong.ttf", 48)
except Exception:
    st.error("Missing mahjong.ttf! Please put the font file in the same folder.")
    st.stop()

with st.form("hand_input_form", clear_on_submit=False):
    hand_input = st.text_input("Your Hand", "11m 223344p 567899s")
    submit = st.form_submit_button("Evaluate Discard", use_container_width=True)

if submit:
    hand, err = parse_hand_input(hand_input)
    if err:
        st.error(err)
    else:
        st.markdown("### Your Hand")
        st.image(draw_hand(hand, font), use_container_width=False)
        with st.spinner("Calculating best discard... (3-step simulation, may take a few seconds)"):
            try:
                results, best = discard_agent.evaluate_discards(hand)
            except Exception as e:
                st.error(f"Failed to evaluate: {e}")
                st.stop()

        st.success(f"**Best Discard:** {utils.pretty(best['discard'])}")
        st.markdown(
            f"""
            <b>Winning Probability:</b> {best['p_win']:.2%}  
            <b>Average Points (if win):</b> {best['avg_win']:.1f}  
            <b>Expected Value:</b> {best['ev']:.1f}
            """, unsafe_allow_html=True
        )

        # Show detailed table
        st.markdown("#### All Discard Options")
        import pandas as pd
        table = pd.DataFrame([{
            "Discard": utils.pretty(r['discard']),
            "Win %": f"{r['p_win']:.2%}",
            "Avg Points (if win)": f"{r['avg_win']:.1f}",
            "EV": f"{r['ev']:.1f}",
        } for r in results]).sort_values("EV", ascending=False)
        st.dataframe(table, hide_index=True, use_container_width=True)

# Footer and credits
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:gray;font-size:0.92em;'>"
    "Inspired by <b>Etopen Project</b>. Made with love and cuddles for Julia ♥"
    "</div>", unsafe_allow_html=True
)
