import json
import numpy as np

# Load data
with open('bot/montecarlosimulation4feb19.json') as f:
    data = json.load(f)

drawdowns = [r['max_drawdown'] for r in data['results']]
yields = [r['final_yield_rate'] for r in data['results']]

# Define bins
# X: Drawdown (0 to 0.15)
# Y: Yield (0.10 to 0.35)
x_bins = np.linspace(0, 0.15, 21)
y_bins = np.linspace(0.10, 0.35, 21)

# Create 2D histogram
H, xedges, yedges = np.histogram2d(drawdowns, yields, bins=(x_bins, y_bins))

# H is shape (20, 20). H[i, j] is count in x_bins[i] and y_bins[j]
# We want to render this in CSS grid.
# CSS grid usually goes top-to-bottom, left-to-right.
# So row 0 is top (highest yield), row 19 is bottom (lowest yield).
# Col 0 is left (lowest drawdown), col 19 is right (highest drawdown).

# H[x, y] where x is drawdown (col), y is yield (row from bottom)
# We need to transpose and flip to match CSS grid (row, col)
# row 0 = highest yield (y=19)
# col 0 = lowest drawdown (x=0)

grid = np.zeros((20, 20))
for i in range(20): # x (drawdown)
    for j in range(20): # y (yield)
        # CSS row = 19 - j (since j=0 is lowest yield, we want it at bottom row 19)
        # CSS col = i
        grid[19 - j, i] = H[i, j]

# Normalize to 0-1 for opacity/color intensity
max_val = np.max(grid)
if max_val > 0:
    grid_norm = grid / max_val
else:
    grid_norm = grid

# Flatten for easy copy-pasting into React
flat_grid = grid_norm.flatten().tolist()

# Format as a JS array string
print("const heatmapData = [")
for i in range(0, 400, 20):
    row = flat_grid[i:i+20]
    row_str = ", ".join([f"{val:.3f}" for val in row])
    print(f"  {row_str},")
print("];")