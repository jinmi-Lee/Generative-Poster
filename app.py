# =====================================================================
# Interactive Generative Poster - spiky "vivid" style (Colab)
# All controls are matplotlib sliders/buttons drawn under the poster
# Left-click = add blob | Right-click = remove nearest clicked blob
# Setup: !pip install -q -U ipympl ipywidgets -> restart runtime -> run this
# =====================================================================
from google.colab import output
output.enable_custom_widget_manager()
get_ipython().run_line_magic("matplotlib", "widget")

import random
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon
from matplotlib.widgets import Slider, Button

# ---------------------------------------------------------------------
# 1. CONFIG
# ---------------------------------------------------------------------
POSTER_W, POSTER_H = 100, 133
N_BLOBS      = 12
BLOB_ALPHA   = 0.55
N_POINTS     = 240
SPIKE_AMOUNT = 0.55            # higher = sharper spikes

DEFAULTS = {"layers": 11, "wobble": 0.23, "palette": 1, "seed": 1210}

PALETTES = {
    "pastel": ["#f4c2d7", "#c9e4de", "#dbcdf0", "#faedcb", "#c6def1", "#d0e6a5"],
    "vivid":  ["#8ee38e", "#5fd35f", "#a5d66b", "#f2a65a", "#e8c547", "#7bc96f"],
    "ocean":  ["#03045e", "#0077b6", "#00b4d8", "#90e0ef", "#caf0f8", "#48cae4"],
    "sunset": ["#ff5e5b", "#ff9f1c", "#ffd166", "#f78fb3", "#c44569", "#6a0572"],
}
BACKGROUNDS = {"pastel": "#ffffff", "vivid": "#ffffff",
               "ocean": "#f8fbff", "sunset": "#1b1030"}
DARK_BG = {"#1b1030"}
PALETTE_NAMES = list(PALETTES)

# ---------------------------------------------------------------------
# 2. STATE
# ---------------------------------------------------------------------
clicked_blobs = []

# ---------------------------------------------------------------------
# 3. FUNCTIONS YOU CAN MODIFY
# ---------------------------------------------------------------------
def base_blobs(seed, n=N_BLOBS):
    rng = np.random.default_rng(seed)
    return [{
        "cx": rng.uniform(20, POSTER_W - 20),
        "cy": rng.uniform(20, POSTER_H - 30),
        "r": rng.uniform(12, 26),
        "seed": int(rng.integers(0, 10**6)),
        "color_offset": int(rng.integers(0, 6)),
    } for _ in range(n)]

def make_click_blob(x, y, seed):
    rng = np.random.default_rng(seed + len(clicked_blobs) * 97 + 1)
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
    color = colors[(blob["color_offset"] + i) % len(colors)]
    return scale, color

def draw_poster(ax, layers, wobble, palette, seed):
    ax.clear()
    colors, bg = PALETTES[palette], BACKGROUNDS[palette]
    ax.set_facecolor(bg)
    ax.set_xlim(0, POSTER_W); ax.set_ylim(0, POSTER_H)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xticks([]); ax.set_yticks([])
    for sp in ax.spines.values():
        sp.set_visible(False)
    for b in base_blobs(seed) + clicked_blobs:
        for i in range(layers):
            scale, color = layer_style(b, i, layers, colors)
            x, y = blob_outline(b["cx"], b["cy"], b["r"] * scale, wobble, b["seed"] + i)
            ax.add_patch(Polygon(np.column_stack([x, y]), closed=True,
                                 facecolor=color, edgecolor="none", alpha=BLOB_ALPHA))
    ax.text(3, POSTER_H - 4, f"Interactive Poster • {palette}",
            fontsize=12, fontweight="bold", va="top",
            color="white" if bg in DARK_BG else "black")

# ---------------------------------------------------------------------
# 4. FIGURE + CONTROLS (sliders under the poster)
# ---------------------------------------------------------------------
fig = plt.figure(figsize=(7, 10))
try:
    fig.canvas.header_visible = False
except Exception:
    pass

ax = fig.add_axes([0.05, 0.30, 0.90, 0.68])

ax_layers  = fig.add_axes([0.20, 0.23, 0.55, 0.025])
ax_wobble  = fig.add_axes([0.20, 0.19, 0.55, 0.025])
ax_palette = fig.add_axes([0.20, 0.15, 0.55, 0.025])
ax_seed    = fig.add_axes([0.20, 0.11, 0.55, 0.025])

s_layers  = Slider(ax_layers,  "Layers",  1, 20, valinit=DEFAULTS["layers"], valstep=1, valfmt="%d")
s_wobble  = Slider(ax_wobble,  "Wobble",  0.0, 1.0, valinit=DEFAULTS["wobble"], valstep=0.01)
s_palette = Slider(ax_palette, "Palette", 0, len(PALETTE_NAMES) - 1,
                   valinit=DEFAULTS["palette"], valstep=1, valfmt="%d")
s_seed    = Slider(ax_seed,    "Seed",    0, 9999, valinit=DEFAULTS["seed"], valstep=1, valfmt="%d")

ax_reset  = fig.add_axes([0.12, 0.03, 0.17, 0.045])
ax_random = fig.add_axes([0.32, 0.03, 0.17, 0.045])
ax_clear  = fig.add_axes([0.52, 0.03, 0.17, 0.045])
ax_save   = fig.add_axes([0.72, 0.03, 0.17, 0.045])
b_reset  = Button(ax_reset,  "Reset")
b_random = Button(ax_random, "Random")
b_clear  = Button(ax_clear,  "Clear")
b_save   = Button(ax_save,   "Save PNG")

def settings():
    return (int(s_layers.val), float(s_wobble.val),
            PALETTE_NAMES[int(s_palette.val)], int(s_seed.val))

def redraw(_=None):
    layers, wobble, pal, seed = settings()
    draw_poster(ax, layers, wobble, pal, seed)
    s_palette.valtext.set_text(pal)          # show the name instead of the index
    fig.canvas.draw_idle()

# ---------------------------------------------------------------------
# 5. EVENTS
# ---------------------------------------------------------------------
def toolbar_active():
    tb = getattr(fig.canvas, "toolbar", None)
    return str(getattr(tb, "mode", "") or "") not in ("", "_Mode.NONE")

def on_click(event):
    if event.inaxes is not ax or event.xdata is None or toolbar_active():
        return
    if event.button == 1:
        clicked_blobs.append(make_click_blob(event.xdata, event.ydata, int(s_seed.val)))
    elif event.button == 3 and clicked_blobs:
        d = [(b["cx"] - event.xdata) ** 2 + (b["cy"] - event.ydata) ** 2
             for b in clicked_blobs]
        clicked_blobs.pop(int(np.argmin(d)))
    else:
        return
    redraw()

def on_reset(_):
    clicked_blobs.clear()
    s_layers.set_val(DEFAULTS["layers"]); s_wobble.set_val(DEFAULTS["wobble"])
    s_palette.set_val(DEFAULTS["palette"]); s_seed.set_val(DEFAULTS["seed"])
    redraw()

def on_random(_):
    s_seed.set_val(random.randint(0, 9999))

def on_clear(_):
    clicked_blobs.clear()
    redraw()

def on_save(_):
    from matplotlib.figure import Figure
    out = Figure(figsize=(6, 8))
    ax_out = out.add_axes([0, 0, 1, 1])
    draw_poster(ax_out, *settings())
    out.savefig("poster.png", dpi=200)
    print("Saved poster.png (see the Files panel)")

# ---------------------------------------------------------------------
# 6. WIRING
# ---------------------------------------------------------------------
for s in (s_layers, s_wobble, s_palette, s_seed):
    s.on_changed(redraw)
b_reset.on_clicked(on_reset)
b_random.on_clicked(on_random)
b_clear.on_clicked(on_clear)
b_save.on_clicked(on_save)
fig.canvas.mpl_connect("button_press_event", on_click)

redraw()
plt.show()
