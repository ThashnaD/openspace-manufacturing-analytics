# =========================================
# INVENTORY RISK & SUPPLIER RELIABILITY ANALYSIS
# Manufacturing Reporting Analytics Project
#
# This script analyses two connected procurement questions
# that the SQL views do not cover:
#
# 1. Which materials are at risk of running out?
#    (stock vs reorder level by plant)
#
# 2. How reliable are our suppliers per material?
#    (delayed vs closed vs open orders per supplier
#    AND per material specifically)
#
# 3. Where low stock overlaps with unreliable suppliers —
#    flagging the highest procurement risk combinations.
#
# Tools used: pandas, matplotlib, seaborn
# Data sources: inventory_levels.csv, purchase_orders.csv
# =========================================


# =========================================
# STEP 1 — IMPORT TOOLS
#
# Before we can use any tool we have to import it.
# Think of this like opening Excel, pgAdmin and
# a calculator before starting work.
#
# Standard syntax for importing:
#   import library_name as shortcut_name
#   from library_name import specific_tool
# =========================================

# pandas — tool for manipulating tables, similar to Excel
# but using code. Once imported, pd. gives us access to
# all pandas functions.
import pandas as pd

# matplotlib — the main library that pyplot and patches
# both live inside. We import it on its own line first
# so Python loads the full library before we access
# specific parts of it below.
import matplotlib

# matplotlib.pyplot — the chart drawing engine.
# plt. gives us access to all chart drawing functions.
import matplotlib.pyplot as plt

# matplotlib.patches — a small tool inside matplotlib
# that creates the coloured square blocks you see in
# chart legends.
import matplotlib.patches as mpatches

# seaborn — sits on top of matplotlib and makes charts
# look more polished with less code. Handles colours
# and styling automatically.
# sns. gives us access to all seaborn functions.
import seaborn as sns

# LinearSegmentedColormap — one specific tool from inside
# matplotlib. Lets us build a custom colour scale that
# blends from one colour to another, for example
# green to red for risk levels.
from matplotlib.colors import LinearSegmentedColormap


# =========================================
# STEP 2 — LOAD DATA
#
# pd.read_csv() reads a CSV file from your computer
# and loads it into a pandas table stored in memory.
# Think of it like opening an Excel sheet and giving
# it a name.
#
# Standard syntax:
#   variable_name = pd.read_csv(r"full\file\path.csv")
#
# The r before the path string is important — it tells
# Python to treat backslashes as literal path separators
# and not as escape characters. Without it you will get
# an error on Windows file paths.
# =========================================

inventory = pd.read_csv(r"C:\Users\thash\Downloads\manufacturing-reporting-analytics\data\inventory_levels.csv")
purchase_orders = pd.read_csv(r"C:\Users\thash\Downloads\manufacturing-reporting-analytics\data\purchase_orders.csv")

# Optional: uncomment these two lines to verify your
# data loaded correctly. head() shows the first 5 rows.
# print(inventory.head())
# print(purchase_orders.head())


# =========================================
# STEP 3 — CALCULATE STOCK BUFFER
#
# The stock buffer tells us how much breathing room
# each material has before it hits its reorder level.
#
# Standard syntax for creating a new column:
#   dataframe["new_column_name"] = calculation
#
# pandas performs the calculation row by row across
# the entire table automatically — no loop needed.
# This is like writing =B2-C2 in Excel and dragging
# it down across every row.
# =========================================

# Subtract reorder_level from stock_qty for every row.
# Positive buffer = stock is safely above reorder point.
# Negative buffer = stock has already fallen below
# the reorder point — critical situation.
inventory["stock_buffer"] = inventory["stock_qty"] - inventory["reorder_level"]


# =========================================
# STEP 4 — ASSIGN RISK LABELS
#
# We turn the buffer number into a human readable
# risk label: Critical, At Risk, or Adequate.
#
# First we define a function, then we apply it to
# every row in the stock_buffer column automatically.
#
# Standard syntax for defining a function:
#   def function_name(input_variable):
#       if condition:
#           return value
#       elif condition:
#           return value
#       else:
#           return value
#
# Standard syntax for applying a function to a column:
#   dataframe["new_column"] = dataframe["column"].apply(function_name)
# =========================================

# Define the risk labelling function.
# buffer is the input — whatever number we pass in
# from the stock_buffer column will be called buffer
# inside this function.
def assign_risk(buffer):
    if buffer < 0:
        # Stock has already fallen below reorder level.
        return "Critical"
    elif buffer < 150:
        # Stock is within 150 units of reorder level —
        # getting close to the danger zone.
        return "At Risk"
    else:
        # Stock level is comfortable.
        return "Adequate"

# Apply the function to every row in stock_buffer.
# .apply() runs the function once for each row value
# and stores the result in a new column called risk_level.
inventory["risk_level"] = inventory["stock_buffer"].apply(assign_risk)


# =========================================
# STEP 5 — SUPPLIER RELIABILITY SUMMARY
#
# We count how many orders each supplier has per status
# (Closed, Delayed, Open) and calculate their delay rate.
#
# This step creates a brand new summary table called
# supplier_status. The original purchase_orders table
# is never changed — exactly like creating a pivot
# table on a separate sheet in Excel.
#
# Standard syntax for groupby and unstack:
#   dataframe.groupby(["col1","col2"]).size().unstack(fill_value=0).reset_index()
# =========================================

# Group purchase orders by supplier and status together,
# count the rows in each group, then spread the status
# values into their own columns.
#
# .groupby(["supplier","status"]) — groups rows where
#   supplier AND status are the same together. Like
#   sorting by two columns in Excel or GROUP BY in SQL.
#
# .size() — counts how many rows are in each group.
#
# .unstack(fill_value=0) — takes the status values
#   (Closed, Delayed, Open) and turns them into their
#   own columns. fill_value=0 puts 0 where a combination
#   does not exist instead of leaving it blank.
#
# .reset_index() — after groupby and unstack the supplier
#   name moves into the index (like row labels on the
#   side). reset_index() moves it back into a proper
#   column with a heading and resets row numbers to
#   plain 0, 1, 2, 3, 4.
supplier_status = (
    purchase_orders
    .groupby(["supplier", "status"])
    .size()
    .unstack(fill_value=0)
    .reset_index()
)

# Safety check — make sure all three status columns
# exist even if one status never appeared in the data.
# A for loop runs through the list one item at a time.
# If a column is missing it gets created with zeros.
for col in ["Closed", "Delayed", "Open"]:
    if col not in supplier_status.columns:
        supplier_status[col] = 0

# Add the three status columns together to get total
# orders per supplier. Like =B2+C2+D2 in Excel but
# applied to every row at once.
supplier_status["total_orders"] = (
    supplier_status["Closed"] +
    supplier_status["Delayed"] +
    supplier_status["Open"]
)

# Calculate delay rate as a percentage.
# Delayed divided by total multiplied by 100.
# .round(1) rounds to 1 decimal place.
supplier_status["delay_rate_pct"] = (
    supplier_status["Delayed"] / supplier_status["total_orders"] * 100
).round(1)

# Sort from highest to lowest delay rate so the worst
# supplier appears at the top of the chart.
# ascending=False means highest first.
supplier_status = supplier_status.sort_values("delay_rate_pct", ascending=False)


# =========================================
# STEP 6 — MATERIAL SPECIFIC SUPPLIER DELAY RATE
#
# We calculate delay rate per MATERIAL AND SUPPLIER
# combination specifically — not per supplier overall.
#
# This is important because a supplier might be reliable
# for Wood Chips but delay Starch constantly. Combining
# those into one number hides that distinction.
#
# We then average the delay rates per material across
# all its suppliers to get one honest risk score per
# material and join it back onto the inventory table.
# =========================================

# Group by material, supplier AND status together.
# This gives us the count of each status for every
# specific material and supplier combination.
material_supplier_delay = (
    purchase_orders
    .groupby(["material", "supplier", "status"])
    .size()
    .unstack(fill_value=0)
    .reset_index()
)

# Same safety check for status columns.
for col in ["Closed", "Delayed", "Open"]:
    if col not in material_supplier_delay.columns:
        material_supplier_delay[col] = 0

# Calculate total orders per material and supplier.
material_supplier_delay["total_orders"] = (
    material_supplier_delay["Closed"] +
    material_supplier_delay["Delayed"] +
    material_supplier_delay["Open"]
)

# Calculate delay rate per material and supplier pair.
material_supplier_delay["delay_rate_pct"] = (
    material_supplier_delay["Delayed"] /
    material_supplier_delay["total_orders"] * 100
).round(1)

# Now average the delay rate per material across all
# its suppliers to get one overall risk score per material.
#
# .groupby("material") — groups by material only now.
# ["delay_rate_pct"] — selects just the delay rate column.
# .mean() — calculates the average across all suppliers
#   for each material.
# .reset_index() — moves material back into a proper column.
# .rename() — renames the column to make clear it is an
#   average. Standard syntax:
#   .rename(columns={"old_name": "new_name"})
material_delay = (
    material_supplier_delay
    .groupby("material")["delay_rate_pct"]
    .mean()
    .reset_index()
    .rename(columns={"delay_rate_pct": "avg_supplier_delay_pct"})
)

# Join the material delay rates onto the inventory table.
# .merge() joins two tables together — like a VLOOKUP
# in Excel or a JOIN in SQL.
#
# Standard syntax:
#   table1.merge(table2, on="matching_column", how="join_type")
#
# on="material" — match rows where the material name
#   is the same in both tables.
# how="left" — keep every row from inventory even if
#   there is no matching material in material_delay.
#   This prevents inventory rows from disappearing.
risk_combined = inventory.merge(material_delay, on="material", how="left")

# Create the final procurement risk flag.
# True only when BOTH conditions are met at the same time.
#
# .isin(["Critical","At Risk"]) — checks if the value
#   is one of the items in the list. Returns True or False.
# >= 30 — checks if delay rate is 30% or higher.
# & — AND operator. Both conditions must be True.
risk_combined["procurement_risk"] = (
    (risk_combined["risk_level"].isin(["Critical", "At Risk"])) &
    (risk_combined["avg_supplier_delay_pct"] >= 30)
)


# =========================================
# STEP 7 — BUILD CHARTS
#
# We create one figure containing three charts
# stacked vertically.
#
# Standard syntax for creating a multi-chart figure:
#   fig, axes = plt.subplots(rows, columns, figsize=(width, height))
#
# fig — the entire canvas/page.
# axes — a list of chart placeholders.
#   axes[0] = first chart
#   axes[1] = second chart
#   axes[2] = third chart
#
# figsize=(width, height) — size in inches.
# =========================================

fig, axes = plt.subplots(3, 1, figsize=(12, 18))

# Set the canvas background colour to white.
# fig.patch refers to the background of the entire figure.
# Standard syntax: fig.patch.set_facecolor("hex_colour")
fig.patch.set_facecolor("#FFFFFF")

# Add a main title across the top of the entire figure.
# \n inside a string means new line.
# y=0.98 positions it just below the very top edge.
# Standard syntax:
#   fig.suptitle("title text", fontsize=, fontweight=, y=, color=)
fig.suptitle(
    "Inventory Risk & Supplier Reliability Analysis\nManufacturing Operations",
    fontsize=15,
    fontweight="bold",
    y=0.98,
    color="#1F3864"
)


# -----------------------------------------------
# CHART 1 — STOCK BUFFER BY MATERIAL AND PLANT
#
# Grouped bar chart showing how much buffer each
# material has above its reorder level, split by plant.
# -----------------------------------------------

# Give the first chart placeholder a simpler name.
ax1 = axes[0]

# Create a pivot table for the grouped bar chart.
# pivot_table() summarises data like a pivot table in Excel.
#
# Standard syntax:
#   dataframe.pivot_table(
#       index="row_labels_column",
#       columns="column_headers_column",
#       values="values_column",
#       aggfunc="aggregation_method"
#   ).fillna(0)
#
# index="material" — materials become row labels.
# columns="plant" — each plant becomes its own column.
# values="stock_buffer" — the numbers inside are buffers.
# aggfunc="sum" — if multiple rows exist for the same
#   material and plant, add them together.
# .fillna(0) — put 0 where a combination does not exist.
pivot = inventory.pivot_table(
    index="material",
    columns="plant",
    values="stock_buffer",
    aggfunc="sum"
).fillna(0)

# Draw the grouped bar chart from the pivot table.
# Standard syntax for plotting from a pandas table:
#   table.plot(kind="chart_type", ax=axes_placeholder, ...)
#
# kind="bar" — grouped bar chart (vertical bars).
# ax=ax1 — draw inside the first chart placeholder.
# colormap="Blues_r" — blue colour palette. _r reverses
#   it so darker blue appears first.
# edgecolor="white" — thin white border between bars
#   so they are visually separated.
# width=0.7 — how wide the bars are. 1.0 makes them
#   touch, 0.7 gives a small gap between groups.
pivot.plot(
    kind="bar",
    ax=ax1,
    colormap="Blues_r",
    edgecolor="white",
    width=0.7
)

# Draw a horizontal reference line at zero — the reorder
# threshold. Any bar below this line means stock is critical.
# Standard syntax:
#   ax.axhline(y_value, color=, linewidth=, linestyle=, label=)
#
# linestyle options: "-" solid, "--" dashed, ":" dotted
ax1.axhline(
    0,
    color="#C0392B",
    linewidth=1.5,
    linestyle="--",
    label="Reorder threshold (buffer = 0)"
)

# Add chart title and axis labels.
# Standard syntax:
#   ax.set_title("text", fontsize=, color=, pad=)
#   ax.set_xlabel("text", fontsize=)
#   ax.set_ylabel("text", fontsize=)
#
# pad= controls the space between the title and the chart.
ax1.set_title(
    "Stock Buffer Above Reorder Level by Material & Plant",
    fontsize=12,
    color="#1F3864",
    pad=10
)
ax1.set_xlabel("Material", fontsize=10)
ax1.set_ylabel("Buffer (units above reorder level)", fontsize=10)

# Rotate the x axis labels so material names do not
# overlap each other.
# Standard syntax:
#   ax.tick_params(axis="x" or "y", rotation=degrees)
ax1.tick_params(axis="x", rotation=30)

# Add a legend showing which colour represents which plant.
# Standard syntax:
#   ax.legend(title="text", fontsize=)
ax1.legend(title="Plant", fontsize=9)

# Set the chart background to a very light grey.
# Standard syntax: ax.set_facecolor("hex_colour")
ax1.set_facecolor("#F8F9FA")

# Remove the top and right border lines from the chart.
# This is a standard professional design choice —
# charts look cleaner without the full box around them.
# Standard syntax:
#   ax.spines[["top","right"]].set_visible(False)
ax1.spines[["top", "right"]].set_visible(False)


# -----------------------------------------------
# CHART 2 — SUPPLIER DELAY RATE
#
# Horizontal bar chart showing each supplier's delay
# rate with colour coded risk levels and percentage
# labels on each bar.
# -----------------------------------------------

ax2 = axes[1]

# Build a list of colours — one per supplier — based
# on their delay rate. This is called a list comprehension.
# It is a compact loop that builds a list in one line.
#
# Standard syntax:
#   [value_if_true if condition else value_if_false
#    for item in iterable]
#
# We chain two conditions:
# If rate >= 45 use red (high risk)
# Else if rate >= 25 use orange (medium risk)
# Else use green (low risk)
bar_colours = [
    "#C0392B" if r >= 45
    else "#E67E22" if r >= 25
    else "#27AE60"
    for r in supplier_status["delay_rate_pct"]
]

# Draw the horizontal bar chart.
# Standard syntax for a horizontal bar chart:
#   ax.barh(y_labels, x_values, color=, edgecolor=, height=)
#
# barh — horizontal bars. h stands for horizontal.
# supplier_status["supplier"] — supplier names on y axis.
# supplier_status["delay_rate_pct"] — bar lengths.
# height= — thickness of each bar (equivalent to width
#   in a vertical bar chart).
#
# We store the result in bars so we can reference
# each individual bar in the label loop below.
bars = ax2.barh(
    supplier_status["supplier"],
    supplier_status["delay_rate_pct"],
    color=bar_colours,
    edgecolor="white",
    height=0.55
)

# Add percentage labels to the end of each bar.
# zip() pairs two lists together so we can loop through
# both at the same time — bar 1 with value 1, etc.
#
# Standard syntax for adding text labels to a chart:
#   ax.text(x_position, y_position, "text",
#           ha="horizontal_alignment",
#           va="vertical_alignment",
#           fontsize=, color=, fontweight=)
#
# bar.get_width() — gets the length of the bar (its value).
# + 0.5 — positions the label just past the end of the bar.
# bar.get_y() + bar.get_height()/2 — centres the label
#   vertically on the bar.
# f"{val}%" — f-string. The f before the string means
#   {val} gets replaced with the actual number.
#   So if val is 46.9 the label shows 46.9%.
# ha="center" — horizontal alignment.
# va="center" — vertical alignment.
for bar, val in zip(bars, supplier_status["delay_rate_pct"]):
    ax2.text(
        bar.get_width() + 0.5,
        bar.get_y() + bar.get_height() / 2,
        f"{val}%",
        ha="center",
        va="center",
        fontsize=11,
        color="#333333",
        fontweight="bold"
    )

# Draw a vertical reference line at 40% — the risk
# threshold. Suppliers to the right of this line are
# considered high risk.
# Standard syntax:
#   ax.axvline(x_value, color=, linewidth=, linestyle=)
ax2.axvline(
    40,
    color="#1F3864",
    linewidth=1.2,
    linestyle="--"
)

# Build the legend manually using mpatches.Patch for
# the coloured squares and plt.Line2D for the line symbol.
#
# Standard syntax for a manual legend patch:
#   mpatches.Patch(color="hex_colour", label="text")
#
# Standard syntax for a manual legend line:
#   plt.Line2D([0], [0], color=, linestyle=, label=)
#
# Then pass them to ax.legend() using handles=[]:
#   ax.legend(handles=[patch1, patch2, line1], fontsize=, loc=)
#
# loc options: "upper right", "upper left", "lower right",
#   "lower left", "center", etc.
high_p     = mpatches.Patch(color="#C0392B", label="High risk (≥45%)")
med_p      = mpatches.Patch(color="#E67E22", label="Medium risk (25–44%)")
low_p      = mpatches.Patch(color="#27AE60", label="Low risk (<25%)")
thresh_line = plt.Line2D([0], [0], color="#1F3864", linestyle="--", label="40% risk threshold")
ax2.legend(handles=[high_p, med_p, low_p, thresh_line], fontsize=9, loc="lower right")

# Set x axis limit to give labels room to show.
# Standard syntax: ax.set_xlim(min_value, max_value)
ax2.set_xlim(0, 65)

ax2.set_title("Supplier Delay Rate (% of Orders Delayed)", fontsize=12, color="#1F3864", pad=10)
ax2.set_xlabel("Delay Rate (%)", fontsize=10)
ax2.set_ylabel("Supplier", fontsize=10)
ax2.set_facecolor("#F8F9FA")
ax2.spines[["top", "right"]].set_visible(False)


# -----------------------------------------------
# CHART 3 — INVENTORY RISK HEATMAP
#
# A grid showing risk level per material and plant
# combination using a green to red colour scale.
# -----------------------------------------------

ax3 = axes[2]

# Seaborn heatmap needs numbers not text labels.
# We convert risk labels to scores using a dictionary.
#
# A dictionary in Python is a lookup table.
# Standard syntax: {"key": value, "key": value}
# .map(dictionary) replaces each value in a column
# with its matching value from the dictionary.
risk_score_map = {"Critical": 3, "At Risk": 2, "Adequate": 1}
risk_combined["risk_score"] = risk_combined["risk_level"].map(risk_score_map)

# Create the pivot table for the heatmap.
# aggfunc="max" — if a material appears multiple times
# for the same plant take the worst (highest) risk score.
# We use max because 3 is Critical and we want to
# surface the worst situation, not average it away.
heatmap_data = risk_combined.pivot_table(
    index="material",
    columns="plant",
    values="risk_score",
    aggfunc="max"
).fillna(1)

# Build a custom colour scale blending green to red.
# Standard syntax:
#   LinearSegmentedColormap.from_list(
#       "name",
#       ["colour1", "colour2", "colour3"],
#       N=number_of_distinct_colours
#   )
#
# N=3 means exactly 3 colours with no blending —
# one for each risk level.
risk_cmap = LinearSegmentedColormap.from_list(
    "risk",
    ["#27AE60", "#E67E22", "#C0392B"],
    N=3
)

# Draw the heatmap using seaborn.
# Standard syntax:
#   sns.heatmap(
#       data,
#       ax=axes_placeholder,
#       cmap=colour_scale,
#       vmin=minimum_value,
#       vmax=maximum_value,
#       linewidths=grid_line_thickness,
#       linecolor="grid_line_colour",
#       annot=True/False,
#       cbar_kws={"shrink": size_as_decimal}
#   )
#
# vmin=1, vmax=3 — tells seaborn our scale goes from
#   1 to 3 so colours map correctly to risk scores.
# linewidths=0.8, linecolor="white" — white grid lines
#   between cells so they are clearly separated.
# annot=False — turns off seaborn's automatic number
#   labels. We add our own text labels below so we
#   can control exactly what they say.
# cbar_kws={"shrink":0.6} — shrinks the colour bar
#   legend on the side to 60% of chart height.
sns.heatmap(
    heatmap_data,
    ax=ax3,
    cmap=risk_cmap,
    vmin=1, vmax=3,
    linewidths=0.8,
    linecolor="white",
    annot=False,
    cbar_kws={"shrink": 0.6}
)

# Add text labels inside each cell manually.
# We use a double loop — one for rows, one for columns.
#
# enumerate() — loops through items and gives you both
#   the position number and the value at the same time.
#   i = row number, material = material name.
#   j = column number, plant = plant name.
#
# heatmap_data.iloc[i, j] — iloc selects a value by
#   its row and column position numbers.
#   i = row position, j = column position.
#
# {3:"Critical", 2:"At Risk", 1:"Adequate"}.get(int(score),"")
#   — dictionary lookup. Converts score back to a label.
#   .get(..., "") means return empty string if not found.
#
# j+0.5, i+0.5 — centres the label in each cell.
#   Cells start at whole numbers so +0.5 moves to middle.
for i, material in enumerate(heatmap_data.index):
    for j, plant in enumerate(heatmap_data.columns):
        score = heatmap_data.iloc[i, j]
        label = {3: "Critical", 2: "At Risk", 1: "Adequate"}.get(int(score), "")
        ax3.text(
            j + 0.5,
            i + 0.5,
            label,
            ha="center",
            va="center",
            fontsize=9,
            color="white",
            fontweight="bold"
        )

# Fix the colour bar tick labels on the side.
# By default it shows numbers 1, 2, 3.
# We replace them with readable risk words.
#
# ax3.collections[0].colorbar — accesses the colour bar.
# set_ticks([1.33, 2.0, 2.67]) — positions tick marks at
#   the centre of each colour band. Our scale goes from
#   1 to 3 with 3 equal bands so centres are at
#   1.33, 2.0 and 2.67.
# set_ticklabels([...]) — replaces numbers with words.
cbar = ax3.collections[0].colorbar
cbar.set_ticks([1.33, 2.0, 2.67])
cbar.set_ticklabels(["Adequate", "At Risk", "Critical"])

ax3.set_title("Inventory Risk Level by Material & Plant", fontsize=12, color="#1F3864", pad=10)
ax3.set_xlabel("Plant", fontsize=10)
ax3.set_ylabel("Material", fontsize=10)
ax3.tick_params(axis="x", rotation=15)
ax3.tick_params(axis="y", rotation=0)


# =========================================
# STEP 8 — SAVE AND DISPLAY
# =========================================

# Automatically adjust spacing between the three charts
# so they do not overlap each other.
# rect=[left, bottom, right, top] reserves space for
# the main title at the top. 0.96 means the charts
# use the bottom 96% of the figure, leaving 4% for
# the title above.
# Standard syntax: plt.tight_layout(rect=[0, 0, 1, top])
plt.tight_layout(rect=[0, 0, 1, 0.96])

# Save the figure as a PNG file.
# Standard syntax:
#   plt.savefig(r"full\path\filename.png", dpi=, bbox_inches=)
#
# dpi=150 — resolution. 150 is clear for a portfolio
#   without making the file too large.
# bbox_inches="tight" — trims extra white space around
#   the edges when saving.
plt.savefig(
    r"C:\Users\thash\Downloads\manufacturing-reporting-analytics\data\inventory_risk_analysis.png",
    dpi=150,
    bbox_inches="tight"
)

# Open a pop-up window to view the chart immediately.
# Standard syntax: plt.show()
plt.show()


# =========================================
# STEP 9 — PRINT SUMMARIES TO CONSOLE
#
# Print three summary tables to the terminal so
# you can read the key findings as text.
# =========================================

# \n adds a blank line before the heading for readability.
print("\n--- INVENTORY RISK SUMMARY ---")
# groupby("risk_level").size() — counts how many rows
# fall into each risk category.
# reset_index(name="count") — moves risk_level back into
# a column and names the count column "count".
# .to_string(index=False) — prints as clean text without
# row numbers on the left side.
print(
    inventory
    .groupby("risk_level")
    .size()
    .reset_index(name="count")
    .to_string(index=False)
)

print("\n--- MATERIAL SPECIFIC SUPPLIER DELAY RATES ---")
# Print only the most relevant columns from our detailed
# material and supplier delay table.
# [["col1","col2",...]] — double brackets select specific
# columns only.
print(
    material_supplier_delay[["material", "supplier", "total_orders", "Delayed", "delay_rate_pct"]]
    .sort_values(["material", "delay_rate_pct"], ascending=[True, False])
    .to_string(index=False)
)

print("\n--- OVERALL SUPPLIER DELAY RATES ---")
print(
    supplier_status[["supplier", "total_orders", "Delayed", "delay_rate_pct"]]
    .to_string(index=False)
)

print("\n--- HIGH PROCUREMENT RISK FLAGS ---")
# Filter to only show rows where procurement_risk is True.
# Standard syntax for filtering a table:
#   dataframe[dataframe["column"] == value]
#
# This is like filtering a column in Excel to show
# only TRUE values.
high_risk = risk_combined[risk_combined["procurement_risk"] == True][[
    "material", "plant", "stock_qty", "reorder_level",
    "stock_buffer", "risk_level", "avg_supplier_delay_pct"
]].sort_values("stock_buffer")

# Conditional print — if the table has rows print them,
# if it is empty print a message instead of a blank table.
# Standard syntax:
#   print(value_if_true if condition else value_if_false)
print(
    high_risk.to_string(index=False)
    if not high_risk.empty
    else "No high procurement risk combinations identified."
)
