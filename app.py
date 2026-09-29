import numpy as np
import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from PIL import Image
import io
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="Interactive Generative Poster", layout="wide")

# ---------------- CONFIG ----------------
POSTER_W, POSTER_H = 100, 133
N_BLOBS, BLOB_ALPHA, N_POINTS, SPIKE_AMOUNT = 12, 0.55, 240, 0.55
FIG_W, FIG_H, DPI = 6, 8, 100          # 600 x 800 px preview

PALETTES = {
    "pastel": ["#f4c2d7", "#c9e4de", "#dbcdf0", "#faedcb", "#c6def1", "#d0e6a5"],
    "vivid":  ["#8ee38e", "#5fd35f", "#a5d66b", "#f2a65a", "#e8c547", "#7bc96f"],
    "ocean":  ["#03045e", "#0077b6", "#00b4d8", "#90e0ef", "#caf0f8", "#48cae4"],
    "sunset": ["#ff5e5b", "#ff9f1c", "#ffd166", "#f78fb3", "#c44569", "#6a0572"],
}
BACKGROUNDS = {"pastel": "#ffffff", "vivid": "#ffffff",
               "ocean": "#f8fbff", "sunset": "#1b1030"}
DARK_BG = {"#1b1030"}

# ---------------- FUNCTIONS YOU CAN MODIFY ----------------
def base_blobs(seed, n=N_BLOBS):
    rng = np.random.default_rng(seed)
    return [{
        "cx": rng.uniform(20, POSTER_W - 20),
        "cy": rng.uniform(20, POSTER_H - 30),
        "r": rng.uniform(12, 26),
        "seed": int(rng.integers(0, 10**6)),
        "color_offset": int(rng.integers(0, 6)),
    } for _ in range(n)]

def make_click_blob(x, y, seed, k):
    rng = np.random.default_rng(seed + k * 97 + 1)
    return {"cx": float(x), "cy": float(y),
            "r": float(rng.uniform(10, 22)),
            "seed": int(rng.integers(0, 10**6)),
            "color_offset": int(rng.integers(0, 6))}

def blob_outline(cx, cy, r, wobble, seed):
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 2 * np.pi, N_POINTS, endpoint=False)
    radius = np.ones_like(t)
    for k in range(2, 6):
        radius += 0.25 * wobble * rng.uniform(0.3, 1) / k * np.sin(
            k * t + rng.uniform(0, 2 * np.pi))
    radius += wobble * SPIKE_AMOUNT * rng.uniform(-1, 1, size=t.size)
    radius = np.clip(radius, 0.25, None)
    return cx + r * radius * np.cos(t), cy + r * radius * np.sin(t)

def layer_style(blob, i, n_layers, colors):
    scale = 1.0 - 0.8 * (i / max(n_layers, 1))
    return scale, colors[(blob["color_offset"] + i) % len(colors)]

def render_poster(layers, wobble, palette, seed, clicked, dpi=DPI):
    colors, bg = PALETTES[palette], BACKGROUNDS[palette]
    fig = plt.figure(figsize=(FIG_W, FIG_H), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor(bg)
    ax.set_xlim(0, POSTER_W); ax.set_ylim(0, POSTER_H)
    ax.set_aspect("auto")              # keeps pixel->poster mapping exact
    ax.axis("off")
    for b in base_blobs(seed) + clicked:
        for i in range(layers):
            scale, color = layer_style(b, i, layers, colors)
            x, y = blob_outline(b["cx"], b["cy"], b["r"] * scale, wobble, b["seed"] + i)
            ax.add_patch(Polygon(np.column_stack([x, y]), closed=True,
                                 facecolor=color, edgecolor="none", alpha=BLOB_ALPHA))
    ax.text(3, POSTER_H - 4, f"Interactive Poster • {palette}", fontsize=13,
            fontweight="bold", va="top",
            color="white" if bg in DARK_BG else "black")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, facecolor=bg)
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()

# ---------------- STATE ----------------
ss = st.session_state
ss.setdefault("blobs", [])
ss.setdefault("last_click", None)
ss.setdefault("seed", 1210)

def random_seed():
    ss.seed = int(np.random.randint(0, 10000))

# ---------------- SIDEBAR CONTROLS ----------------
st.sidebar.title("Controls")
layers = st.sidebar.slider("Layers", 1, 20, 11)
wobble = st.sidebar.slider("Wobble", 0.0, 1.0, 0.23, 0.01)
palette = st.sidebar.selectbox("palette_mode", list(PALETTES), index=1)
seed = st.sidebar.slider("Seed", 0, 9999, key="seed")
st.sidebar.button("Random seed", on_click=random_seed)

c1, c2 = st.sidebar.columns(2)
if c1.button("Undo last"):
    if ss.blobs:
        ss.blobs.pop()
if c2.button("Clear clicks"):
    ss.blobs = []

# ---------------- MAIN: POSTER + CLICK ----------------
st.title("Interactive Generative Poster")
st.caption("Click on the poster to add a blob. Use Undo last / Clear clicks in the sidebar.")

png = render_poster(layers, wobble, palette, seed, ss.blobs)
click = streamlit_image_coordinates(Image.open(io.BytesIO(png)), key="poster", use_column_width=False)

if click:
    sig = (click["x"], click["y"], click.get("unix_time"))
    if sig != ss.last_click:                       # ignore the same click on reruns
        ss.last_click = sig
        px = click["x"] / click["width"] * POSTER_W
        py = (1 - click["y"] / click["height"]) * POSTER_H
        ss.blobs.append(make_click_blob(px, py, seed, len(ss.blobs)))
        st.rerun()

st.sidebar.write(f"Clicked blobs: {len(ss.blobs)}")
hi_png = render_poster(layers, wobble, palette, seed, ss.blobs, dpi=200)
st.sidebar.do
