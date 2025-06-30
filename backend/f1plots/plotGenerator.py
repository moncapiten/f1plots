import matplotlib.pyplot as plt
import io
from apiConnect import *

def generate_plots(year=2025):
    driver_positions, driver_points, driver_names, driver_teams, driver_colors, driver_history, session_names, sessionCounter = get_all_season_results(year)

    standings = sorted(driver_points.items(), key=lambda x: x[1], reverse=True)
    complete_standings = [ 
        (driver_num, points, driver_names.get(driver_num, 'UNK'), driver_teams.get(driver_num, 'Unknown Team'), driver_colors.get(driver_num, '777777')) 
        for driver_num, points in standings 
    ]

    # Prepare data for plotting
    plt_pts = [points for _, points, _, _, _ in complete_standings]
    plt_names = [name + '\n' + str(num) for num, _, name, _, _ in complete_standings]
    plt_clrs = ['#' + color for _, _, _, _, color in complete_standings]

    # --- Plot 1: Points Distribution ---
    fig1, ax1 = plt.subplots(figsize=(12, 6))
    fig1.patch.set_facecolor('#333333')  # Dark gray background
    ax1.set_facecolor('#333333')  # Dark gray background
    ax1.bar(plt_names, plt_pts, color=plt_clrs)
    ax1.hlines(plt_pts[0] - 25, 0, len(plt_names) - 1, colors='black', linestyles='--')
    ax1.set_xlabel('Drivers')
    ax1.set_ylabel('Points')
    ax1.set_title(f'F1 {year} Season Points Distribution')
    ax1.set_xticklabels(plt_names, rotation=45)
    ax1.grid(linestyle='-.', which='both')
    fig1.tight_layout()

    # Save to buffer
    buf1 = io.BytesIO()
    fig1.savefig(buf1, format='png')
    buf1.seek(0)
    plt.close(fig1)

    # --- Plot 2: Points History ---
    fig2, ax2 = plt.subplots(figsize=(12, 6))
    fig2.patch.set_facecolor('#333333')  # Dark gray background
    ax2.set_facecolor('#333333')  # Dark gray background
    for key, values in driver_history.items():
        label = driver_names.get(key, f"Driver {key}")
        color = '#' + driver_colors.get(key, '777777')
        ax2.plot(session_names, values, label=label, marker='o', color=color)
        ax2.text(session_names[-1], values[-1], f' {label}', va='center', ha='left', color=color, fontsize=10)
    ax2.set_title(f'F1 {year} Season Points History')
    ax2.set_xlabel("Session")
    ax2.set_ylabel("Points")
    ax2.grid(linestyle='-.', which='both')
    ax2.set_xticklabels(session_names, rotation=45)
    fig2.tight_layout()

    # Save to buffer
    buf2 = io.BytesIO()
    fig2.savefig(buf2, format='png')
    buf2.seek(0)
    plt.close(fig2)

    return buf1, buf2
