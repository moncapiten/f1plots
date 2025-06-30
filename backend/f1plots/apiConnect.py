import requests
import json
from datetime import datetime
import matplotlib.pyplot as plt
import numpy as np

# F1 Points system
RACE_POINTS = {
    1: 25, 2: 18, 3: 15, 4: 12, 5: 10, 6: 8, 7: 6, 8: 4, 9: 2, 10: 1
}

SPRINT_POINTS = {
    1: 8, 2: 7, 3: 6, 4: 5, 5: 4, 6: 3, 7: 2, 8: 1
}

def get_all_season_results(year=2025, debug=False):
    """
    Fetches all F1 race and sprint results for the specified season
    Returns three dictionaries:
    1. driver_positions: {driver_number: [list of positions]}
    2. driver_points: {driver_number: total_points}
    3. driver_names: {driver_number: name_acronym}
    """
    
    driver_positions = {}
    driver_points = {}
    driver_names = {}
    driver_teams = {}
    driver_colors = {}
    driver_history = {}
    session_names = []
    sessionCounter = 0
    
    try:
        print(f"Fetching all sessions for {year}...")
        
        # Get all sessions for the year
        sessions_url = "https://api.openf1.org/v1/sessions"
        params = {'year': year}
        
        sessions_response = requests.get(sessions_url, params=params)
        sessions_response.raise_for_status()
        sessions = sessions_response.json()
        
        if not sessions:
            print(f"No sessions found for {year}")
            return driver_positions, driver_points, driver_names
        
        # Filter for Race and Sprint sessions only
        race_sessions = [s for s in sessions if s.get('session_type') in ['Race'] and 
                        s.get('session_name') in ['Race', 'Sprint']]
        
        print(f"Found {len(race_sessions)} race/sprint sessions")
        
        # Sort sessions by date
        race_sessions.sort(key=lambda x: x['date_start'])
        
        for session in race_sessions:
            session_key = session['session_key']
            session_name = session.get('session_name', 'Unknown')
            meeting_name = session.get('country_name', 'Unknown')
            is_sprint = session_name == 'Sprint'
            
            session_names.append(meeting_name if not is_sprint else meeting_name + " Sprint")
            
            if debug:
                print(f"\nDebug: Processing session {session_key} - {meeting_name} - {session_name}")
            
            # Get driver names for this session (if we don't have them yet)
            if not driver_names:
                drivers_response = requests.get(
                    "https://api.openf1.org/v1/drivers",
                    params={'session_key': session_key}
                )
                if drivers_response.status_code == 200:
                    drivers_data = drivers_response.json()
                    for driver in drivers_data:
                        driver_num = driver.get('driver_number')
                        name_acronym = driver.get('name_acronym')
                        team_name = driver.get('team_name', 'Unknown Team')
                        color = driver.get('team_colour', '#777777')  # Default to grey if no color provided
                        if driver_num and name_acronym:
                            driver_names[driver_num] = name_acronym
                        if driver_num and team_name:
                            driver_teams[driver_num] = team_name
                        if driver_num and color:
                            driver_colors[driver_num] = color
            
            # Get positions for this session
            position_response = requests.get(
                "https://api.openf1.org/v1/position",
                params={'session_key': session_key}
            )
            
            if position_response.status_code == 200:
                positions = position_response.json()
                if positions:
                    # Get final positions for each driver
                    final_positions = get_final_positions(positions)
                    

                    # Process results
                    for driver_num, position in final_positions.items():
                        # Initialize driver data if not exists
                        if driver_num not in driver_positions:
                            driver_positions[driver_num] = [None] * sessionCounter
                            driver_points[driver_num] = 0
                            driver_history[driver_num] = [0] * sessionCounter
                        

                        
                        # Add position to driver's list
                        driver_positions[driver_num].append(position)
                        
                        # Calculate and add points
                        points_table = SPRINT_POINTS if is_sprint else RACE_POINTS
                        points = points_table.get(position, 0)
                        driver_points[driver_num] += points
                        driver_history[driver_num].append(driver_points[driver_num])
                        
                        if debug:
                            print(f"  Driver {driver_num}: P{position} ({points} pts)")

                    for driver_num in driver_positions:
                        if driver_num not in final_positions:
                            # If driver has no position in this session, we can assume they didn't participate
                            driver_positions[driver_num].append(None)
                            driver_history[driver_num].append(driver_points[driver_num])

                else:
                    print(f"  No position data found")
            else:
                print(f"  Failed to get position data (status: {position_response.status_code})")
            
            sessionCounter += 1
        
        # Fill in driver names for any remaining drivers
        fill_missing_driver_names(driver_names, driver_teams, driver_colors, driver_positions.keys(), year)
        
        return driver_positions, driver_points, driver_names, driver_teams, driver_colors, driver_history, session_names, sessionCounter
        
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return driver_positions, driver_points, driver_names, driver_teams, driver_colors, driver_history, session_names, sessionCounter
    except Exception as e:
        print(f"Unexpected error: {e}")
        return driver_positions, driver_points, driver_names, driver_teams, driver_colors, driver_history, session_names, sessionCounter

def get_final_positions(positions):
    """
    Process position data to get final positions for each driver
    """
    if not positions:
        return {}
    
    # Sort positions by date to get chronological order
    positions.sort(key=lambda x: x['date'])
    
    # Get the final position for each driver (their last recorded position)
    final_positions = {}
    for position in positions:
        driver_number = position.get('driver_number')
        final_position = position.get('position')
        
        if driver_number is not None and final_position is not None:
            final_positions[driver_number] = final_position
    
    return final_positions

def fill_missing_driver_names(driver_names, driver_teams, driver_colors, driver_numbers, year):
    """
    Try to fill in missing driver names by querying different sessions
    """
    missing_drivers = [num for num in driver_numbers if num not in driver_names]
    
    if not missing_drivers:
        return
    
    print(f"\nTrying to find names for {len(missing_drivers)} drivers({missing_drivers})...")
    
    try:
        # Get a few random sessions to try to find driver names
        sessions_response = requests.get(
            "https://api.openf1.org/v1/sessions",
            params={'year': year}
        )
        
        if sessions_response.status_code == 200:
            sessions = sessions_response.json()
            # Try first few sessions
            for session in sessions[:5]:
                if not missing_drivers:
                    break
                    
                drivers_response = requests.get(
                    "https://api.openf1.org/v1/drivers",
                    params={'session_key': session['session_key']}
                )
                
                if drivers_response.status_code == 200:
                    drivers_data = drivers_response.json()
                    for driver in drivers_data:
                        driver_num = driver.get('driver_number')
                        name_acronym = driver.get('name_acronym')
                        if driver_num in missing_drivers and name_acronym:
                            driver_names[driver_num] = name_acronym
                            missing_drivers.remove(driver_num)
    except Exception as e:
        print(f"Error filling driver names with method 1: {e}")
    
    if missing_drivers:
        print(f"\nTrying to find names for remaining {len(missing_drivers)} drivers with method 2...")
        for driver_num in missing_drivers:
            try:
                driver_response = requests.get(f"https://api.openf1.org/v1/drivers?driver_number={driver_num}")
                if driver_response.status_code == 200:
                    driver_data = driver_response.json()
                    name_acronym = driver_data[0].get('name_acronym', 'Unknown Driver')

                    team_name = driver_data[0].get('team_name', 'Unknown Team')
                    color = driver_data[0].get('team_colour', '777777')  #

                    driver_names[driver_num] = name_acronym
                    if team_name:
                        driver_teams[driver_num] = team_name
                    if color:
                        driver_colors[driver_num] = color
                    missing_drivers.remove(driver_num)
            except Exception as e:
                print(f"Error fetching driver name for {driver_num}: {e}")
                driver_names[driver_num] = 'UNK'
    
                        


def print_summary(complete_standings, driver_positions, sessionCounter):
    """
    Print a nice summary of the season results
    """
    print("\n" + "="*60)
    print("SEASON SUMMARY")
    print("="*60)
    
    # Championship standings (sorted by points)
    print("\nCHAMPIONSHIP STANDINGS:")
    print("-" * 40)
    
    
    for i, (driver_num, points, driver_name, driver_team, _) in enumerate(complete_standings, 1):
        races_completed = len(driver_positions.get(driver_num, []))
        avg_position = sum(driver_positions.get(driver_num, [])) / races_completed if races_completed > 0 else 0
        
        print(f"{i:2d}. {driver_num:2d} - {driver_name:3s} - {points:3d} pts ({driver_team}, {races_completed} races, avg: {avg_position:.1f})")
    
    print(f"\nTOTAL RACES/SPRINTS PROCESSED: {sessionCounter}")


def main(year = 2025, summary_printout=False, verbose=False, compact=False):
    """Main function to run the script"""
#    year = 2025  # Change this to get different seasons
    
    print(f"Fetching complete F1 {year} season results...")
    print("This includes both regular races and sprint races")
    print("-" * 50)
    
    # Get all season data
    driver_positions, driver_points, driver_names, driver_teams, driver_colors, driver_history, session_names, sessionCounter = get_all_season_results(year)
    
    if not driver_positions:
        print("No results found. This could be because:")
        print("1. No race data available for the specified year")
        print("2. API connection issues")
        print("3. The season hasn't started yet")
        print("Exiting...")
        quit()

    standings = sorted(driver_points.items(), key=lambda x: x[1], reverse=True)

    complete_standings = [ (driver_num, points, driver_names.get(driver_num, 'UNK'), driver_teams.get(driver_num, 'Unknown Team'), driver_colors.get(driver_num, '777777')) for driver_num, points in standings ]

    # Print summary
    if summary_printout:
        print_summary(complete_standings, driver_positions, sessionCounter)
    
    # Print the dictionaries as requested
    if verbose:
        print(f"\n" + "="*60)
        print("REQUESTED DICTIONARIES:")
        print("="*60)
        
        print(f"\n1. DRIVER POSITIONS (driver_number: [list of positions]):")
        print("-" * 55)
        for driver_num in sorted(driver_positions.keys()):
            positions = driver_positions[driver_num]
            name = driver_names.get(driver_num, f"UNK")
            print(f"Driver {driver_num:2d} ({name}): {positions}")
        
        print(f"\n2. DRIVER POINTS (driver_number: total_points):")
        print("-" * 45)
        for driver_num in sorted(driver_points.keys()):
            points = driver_points[driver_num]
            name = driver_names.get(driver_num, f"UNK")
            print(f"Driver {driver_num:2d} ({name}): {points} points")
        
        print(f"\n3. DRIVER NAMES (driver_number: name_acronym):")
        print("-" * 45)
        for driver_num in sorted(driver_names.keys()):
            name = driver_names[driver_num]
            print(f"Driver {driver_num:2d}: '{name}'")
    
    if compact:
        print(f"\n" + "-"*60)
        print("Raw dictionaries for easy copying:")
        print("-"*60)
        print(f"\ndriver_positions = {driver_positions}")
        print(f"\ndriver_points = {driver_points}")
        print(f"\ndriver_names = {driver_names}")

    print("1" if all(len(i) == sessionCounter for i in driver_positions.values()) else "0")
#    print(''.join("1" if len))
    print(driver_positions)
    print(driver_history)




    plt.figure(figsize=(12, 6))
    plt_pts = [ points for _, points, _, _, _ in complete_standings ]
    plt_names = [ name+'\n'+str(num) for num, _, name, _, _ in complete_standings ]
    plt_clrs = [ '#'+color for _, _, _, _, color in complete_standings ]
    plt.bar(plt_names, plt_pts, color=plt_clrs)
    plt.hlines(plt_pts[0]-25, 0, plt_names[-1], colors='black', linestyles='--')
    plt.xlabel('Drivers')
    plt.ylabel('Points')
    plt.title(f'F1 {year} Season Points Distribution')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.grid(linestyle='-.', which='both')
    plt.show()


    plt.figure(figsize=(12, 6))
    for key, values in driver_history.items():
        label = driver_names.get(key, f"Driver {key}")
        color = '#' + driver_colors.get(key, '777777')
        plt.plot(session_names, values, label=label, marker='o', color=color)
        
        # Place label near the last point
        plt.text(session_names[-1], values[-1], f' {label}', va='center', ha='left', color=color, fontsize=10)
#    for key, values in driver_history.items():
#        plt.plot(session_names, values, label=driver_names.get(key, f"Driver {key}"), marker='o', color='#'+driver_colors.get(key, '777777'))
    plt.xticks(rotation=45)
    plt.title(f'F1 {year} Season Points History')
#    plt.xticks(np.arange(len(session_names)), session_names, rotation=45)
    plt.tight_layout()
    plt.xlabel("Session")
    plt.ylabel("Points")
    plt.grid(linestyle='-.', which='both')
    plt.show()


def plotting(year = 2025):

    driver_positions, driver_points, driver_names, driver_teams, driver_colors, driver_history, session_names, sessionCounter = get_all_season_results(year)

    standings = sorted(driver_points.items(), key=lambda x: x[1], reverse=True)

    complete_standings = [ (driver_num, points, driver_names.get(driver_num, 'UNK'), driver_teams.get(driver_num, 'Unknown Team'), driver_colors.get(driver_num, '777777')) for driver_num, points in standings ]

    plt.figure(figsize=(12, 6))
    plt_pts = [ points for _, points, _, _, _ in complete_standings ]
    plt_names = [ name+'\n'+str(num) for num, _, name, _, _ in complete_standings ]
    plt_clrs = [ '#'+color for _, _, _, _, color in complete_standings ]
    plt.bar(plt_names, plt_pts, color=plt_clrs)
    plt.hlines(plt_pts[0]-25, 0, plt_names[-1], colors='black', linestyles='--')
    plt.xlabel('Drivers')
    plt.ylabel('Points')
    plt.title(f'F1 {year} Season Points Distribution')
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.grid(linestyle='-.', which='both')
    plt.show()


    plt.figure(figsize=(12, 6))
    for key, values in driver_history.items():
        label = driver_names.get(key, f"Driver {key}")
        color = '#' + driver_colors.get(key, '777777')
        plt.plot(session_names, values, label=label, marker='o', color=color)
        
        # Place label near the last point
        plt.text(session_names[-1], values[-1], f' {label}', va='center', ha='left', color=color, fontsize=10)
    plt.xticks(rotation=45)
    plt.title(f'F1 {year} Season Points History')
    plt.tight_layout()
    plt.xlabel("Session")
    plt.ylabel("Points")
    plt.grid(linestyle='-.', which='both')
    plt.show()
