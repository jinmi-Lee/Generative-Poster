import io
import numpy as np
import streamlit as st
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from PIL import Image
from streamlit_image_coordinates import streamlit_image_coordinates

st.set_page_config(page_title="Interactive Generative Poster", layout="wide")

# ---------------- CONFIG ----------------
POSTER_W, POSTER_H = 100, 133
N_BLOBS, BLOB_ALPHA, N_POINTS = 6, 0.75, 240
FIG_W, FIG_H = 6, 8

PALETTES = {
    "Sunset": ("#1b1030", ["#ff5e5b", "#ff9f1c", "#ffd166", "#f78fb3", "#c44569"]),
    "Ocean":  ("#04202c", ["#0a9396", "#94d2bd", "#005f73", "#48cae4", "#ade8f4"]),
    "Forest": ("#10200f", ["#2d6a4f", "#74c69d", "#b7e4c7", "#d8f3dc", "#95d5b2"]),
    "Candy":  ("#fff5f7", ["#ff70a6", "#ff9770", "#ffd670", "#70d6ff", "#e9ff70"]),
    "Mono":   ("#f2f2f2", ["#111111", "#444444", "#777777", "#aaaaaa", "#d0d0d0"]),
}
DARK_BG = {"#1b1030", "#04202c", "#10200f"}

# ---------------- FUNCTIONS YOU CAN MODIFY ----------------
def base_blobs(seed, n=N_BLOBS):
    rng = np.random.default_rng(seed)
    return [{
        "cx": rng.uniform(15, POSTER_W - 15),
        "cy": rng.uniform(15, POSTER_H - 15),
        "r": rng.uniform(10, 24),
        "seed": int(rng.integers(0, 10**6)),
        "color_offset": int(rng.integers(0, 5)),
    } for _ in range(n)]

def make_click_blob(x, y, seed, k):
    rng = np.random.default_rng(seed + k * 97 + 1)
    return {"cx": float(x), "cy": float(y),
            "r": float(rng.uniform(9, 20)),
            "seed": int(rng.integers(0, 10**6)),
            "color_offset": int(rng.integers(0, 5))}

def blob_outline(cx, cy, r, wobble, seed, style):
    rng = np.random.default_rng(seed)
    t = np.linspace(0, 2 * np.pi, N_POINTS, endpoint=False)
    radius = np.ones_like(t)
    for k in range(2, 7):                                  # smooth lobes
        radius += wobble * rng.uniform(0.3, 1.0) / k * np.sin(
            k * t + rng.uniform(0, 2 * np.pi))
    if style == "spiky":                                   # extra jagged noise
        radius += wobble * 0.55 * rng.uniform(-1, 1, size=t.size)
    radius = np.clip(radius, 0.2, None)
    return cx + r * radius * np.cos(t), cy + r * radius * np.sin(t)

def layer_style(blob, i, n_layers, colors):
    scale = 1.0 - 0.85 * (i / max(n_layers, 1))
    return scale, colors[(blob["color_offset"] + i) % len(colors)]

def render_poster(layers, wobble, palette, seed, style, clicked, dpi=100):
    bg, colors = PALETTES[palette]
    fig = plt.figure(figsize=(FIG_W, FIG_H), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor(bg)
    ax.set_xlim(0, POSTER_W); ax.set_ylim(0, POSTER_H)
    ax.set_aspect("auto")
    ax.axis("off")
    for b in base_blobs(seed) + clicked:
        for i in range(layers):
            scale, color = layer_style(b, i, layers, colors)
            x, y = blob_outline(b["cx"], b["cy"], b["r"] * scale,
                                wobble, b["seed"] + i, style)
            ax.add_patch(Polygon(np.column_stack([x, y]), closed=True,
                                 facecolor=color, edgecolor="none",
                                 alpha=BLOB_ALPHA))
    ax.text(3, POSTER_H - 4, f"Interactive Poster • {palette}",
            fontsize=13, fontweight="bold", va="top",
            color="white" if bg in DARK_BG else "black")
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=dpi, facecolor=bg)
    plt.close(fig)
    return buf.getvalue()

# ---------------- STATE ----------------
ss = st.session_state
ss.setdefault("blobs", [])
ss.setdefault("last_click", None)

# ---------------- SIDEBAR CONTROLS ----------------
st.sidebar.title("Controls")
layers  = st.sidebar.slider("Layers", 1, 12, 6)
wobble  = st.sidebar.slider("Wobble", 0.0, 1.5, 0.59, 0.01)
palette = st.sidebar.select_slider("Palette", options=list(PALETTES), value="Ocean")
style   = st.sidebar.selectbox("outline_style", ["smooth", "spiky"])
seed    = st.sidebar.slider("Seed", 0, 9999, 42)

c1, c2 = st.sidebar.columns(2)
if c1.button("Undo last") and ss.blobs:
    ss.blobs.pop()
if c2.button("Clear clicks"):
    ss.blobs = []

# ---------------- MAIN: POSTER + CLICK ----------------
st.title("Interactive Generative Poster")
st.caption("Click on the poster to add a blob.")

png = render_poster(layers, wobble, palette, seed, style, ss.blobs)
click = streamlit_image_coordinates(Image.open(io.BytesIO(png)), key="poster")

if click:
    sig = (click["x"], click["y"], click.get("unix_time"))
    if sig != ss.last_click:
        ss.last_click = sig
        px = click["x"] / click["width"] * POSTER_W
        py = (1 - click["y"] / click["height"]) * POSTER_H
        ss.blobs.append(make_click_blob(px, py, seed, len(ss.blobs)))
        st.rerun()

st.sidebar.write(f"Clicked blobs: {len(ss.blobs)}")
st.sidebar.download_button(
    "Download PNG",
    render_poster(layers, wobble, palette, seed, style, ss.blobs, dpi=200),
    "poster.png", "image/png")
