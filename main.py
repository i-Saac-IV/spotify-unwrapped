import os
import json
from collections import defaultdict
from datetime import datetime, date
import pytz
import matplotlib.pyplot as plt
import numpy as np

MIN_PLAYTIME_S = 30
TOP_N = 50

# Define global start and end dates in "DD-MM-YYYY" format
START_DATE_STR  = '01-01-2000'
END_DATE_STR    = '31-01-2025'

START_DATE_STR = input("Input start date (DD-MM-YYYY): ")
END_DATE_STR = input("Input end date (DD-MM-YYYY): ")

#for testing
#START_DATE_STR = "01-01-2000"
#END_DATE_STR = "31-12-2025"

# Function to parse date from string
def parse_date(date_str):
    return datetime.strptime(date_str, "%d-%m-%Y").date()

# Parse start and end dates
START_DATE = parse_date(START_DATE_STR)
END_DATE = parse_date(END_DATE_STR)


track_playnum = defaultdict(int)
album_playnum = defaultdict(int)
artist_playnum = defaultdict(int)

# Function to process tracks within a specific date range
def process_tracks_within_date_range(tracks, start_date, end_date):
    track_playtime = defaultdict(int)
    album_playtime = defaultdict(int)
    artist_playtime = defaultdict(int)
    hourly_playtime = defaultdict(int)

    country_timezone_mapping = {
        "NZ": "Pacific/Auckland",  # New Zealand
        "US": "America/New_York",  # United States (Eastern Time)
        # Add more country code mappings as needed
    }

    for track in tracks:
        # Skip if any of the required fields are None
        if None in [track.get('master_metadata_track_name'), track.get('master_metadata_album_album_name'), track.get('master_metadata_album_artist_name')]:
            continue
        
        playtime = track['ms_played']
        if playtime < MIN_PLAYTIME_S * 1000:
            continue

        track_name = track['master_metadata_track_name']
        album_name = track['master_metadata_album_album_name']
        artist_name = track['master_metadata_album_artist_name']

        country_code = track.get('conn_country', 'UTC')  # Default to UTC if country code is not available
        timezone = country_timezone_mapping.get(country_code, 'UTC')  # Default to UTC if country code is not in mapping

        # Convert timestamp to the inferred timezone
        ts = datetime.fromisoformat(track['ts'].replace('Z', '+00:00'))
        ts_timezone = pytz.timezone(timezone)
        ts = ts.replace(tzinfo=pytz.utc).astimezone(ts_timezone)

        # Check if the timestamp is within the specified date range
        if start_date <= ts.date() <= end_date:
            # Aggregate playtime for tracks, albums, and artists
            track_playtime[track_name] += playtime
            album_playtime[album_name] += playtime
            artist_playtime[artist_name] += playtime
            track_playnum[track_name] += 1
            album_playnum[album_name] += 1
            artist_playnum[artist_name] += 1

            # Aggregate playtime by hour of the day in the inferred timezone
            hour = ts.hour
            hourly_playtime[hour] += playtime

    return track_playtime, album_playtime, artist_playtime, hourly_playtime

# Helper function to get the top N items from a dictionary
def get_top_n(d, n=TOP_N):
    return sorted(d.items(), key=lambda item: item[1], reverse=True)[:n]

# Initialize dictionaries to aggregate data from all files
all_track_playtime = defaultdict(int)
all_album_playtime = defaultdict(int)
all_artist_playtime = defaultdict(int)

all_hourly_playtime = defaultdict(int)

# Process all JSON files in the directory
for filename in os.listdir('.'):
    if filename.endswith('.json'):
        with open(filename, 'r', encoding='utf-8') as file:
            tracks = json.load(file)
        
        # Process the tracks within the specified date range
        track_playtime, album_playtime, artist_playtime, hourly_playtime = process_tracks_within_date_range(tracks, START_DATE, END_DATE)
        # Aggregate data from this file into the global dictionaries
        for track, playtime in track_playtime.items():
            all_track_playtime[track] += playtime
        for album, playtime in album_playtime.items():
            all_album_playtime[album] += playtime
        for artist, playtime in artist_playtime.items():
            all_artist_playtime[artist] += playtime
        for hour, playtime in hourly_playtime.items():
            all_hourly_playtime[hour] += playtime

# Display the aggregated statistics for all files
print(f"\n\nStats based off listening duration: {START_DATE_STR} -> {END_DATE_STR}")
print(f"\nMinium playtime: {MIN_PLAYTIME_S}s")

top_tracks = get_top_n(all_track_playtime)
print("\n\tTop Tracks:")
for track, playtime in top_tracks:
    print(f"\t\t{track}: {playtime / 1000 / 60:.2f} minutes ({int(playtime / 1000 / 60 / 60)}hs)")

top_albums = get_top_n(all_album_playtime)
print("\n\tTop Albums:")
for album, playtime in top_albums:
    print(f"\t\t{album}: {playtime / 1000 / 60:.2f} minutes ({int(playtime / 1000 / 60 / 60)}hs)")

top_artists = get_top_n(all_artist_playtime)
print("\n\tTop Artists:")
for artist, playtime in top_artists:
    print(f"\t\t{artist}: {playtime / 1000 / 60:.2f} minutes ({int(playtime / 1000 / 60 / 60)}hs)")

print("\n\nStats based off number of plays:")
top_tracks = get_top_n(track_playnum)
print("\n\tTop Tracks:")
for track, playtime in top_tracks:
    print(f"\t\t{track}: {playtime} plays")

top_albums = get_top_n(album_playnum)
print("\n\tTop Albums:")
for album, playtime in top_albums:
    print(f"\t\t{album}: {playtime} plays")

top_artists = get_top_n(artist_playnum)
print("\n\tTop Artists:")
for artist, playtime in top_artists:
    print(f"\t\t{artist}: {playtime} plays")

print("\n\nPlaytime by Hour of the Day:")
total_playtime = 0
for hour, playtime in sorted(all_hourly_playtime.items()):
    total_playtime += playtime
    print(f"\t{hour}:00 \t-> {playtime / 1000 / 60:.2f} mins ({int(playtime / 1000 / 60 / 60)}hs)")


print("\n\nTotals:")
print(f"\tNumber of tracks: \t{len(track_playnum)}")
print(f"\tNumber of albums: \t{len(album_playnum)}")
print(f"\tNumber of artists: \t{len(artist_playnum)}")
print(f"\n\tPlaytime: {total_playtime / 1000 / 60:.2f} mins ({int(total_playtime / 1000 / 60 / 60)}hs) ({int(total_playtime / 1000 / 60 / 60 / 24)}d)")


def graph_most_played(data, title, x_label, is_in_hours):
    """graphs the most played thing"""
    top_datapoints = dict(get_top_n(data))
    if is_in_hours:
        top_datapoints_hours = {key: value / 1000 / 60 / 60 for key, value in top_datapoints.items()}  # Convert milliseconds to hours
    else:
        top_datapoints_hours = {key: value for key, value in top_datapoints.items()}  # Convert milliseconds to hours
    plt.figure(figsize=(16, 8))
    plt.barh(list(top_datapoints_hours.keys()), list(top_datapoints_hours.values()), color='brown')
    plt.xlabel(x_label)
    plt.grid(axis='x', which='major', linestyle='--')
    plt.title(title)
    plt.gca().invert_yaxis()
    plt.tight_layout()
    plt.show()

def graph_playtime_by_hour(hourly_playtime, title):
    """Graphs the playtime by hour of the day on a polar axis."""
    hours = sorted(hourly_playtime.keys())
    playtime = [(hourly_playtime[hour] / 1000 / 60 / 60) for hour in hours]  # Convert milliseconds to minutes

    # Repeat the first hour at the end to close the loop in the polar plot
    hours.append(hours[0])
    playtime.append(playtime[0])

    theta = np.linspace(0, 2 * np.pi, len(hours), endpoint=True)
    width = np.pi / (len(hours) / 2) * 0.75

    plt.figure(figsize=(8, 8))
    ax = plt.subplot(111, polar=True)
    ax.bar(theta, playtime, color='brown', width=width)
    ax.set_xticks(theta[:-1])  # Exclude the last theta value to match the number of ticks to labels
    ax.set_xticklabels([f"{hour}:00" for hour in hours[:-1]])  # Exclude the last hour label to prevent overlap
    ax.grid(axis='y', linestyle='--')
    ax.grid(axis='x', linestyle='')
    ax.set_theta_zero_location('S')
    ax.set_theta_direction(-1)
    ax.set_title(title)
    plt.show()

def export_unique_tracks(tracks, filename):
    """Export unique tracks to a file."""
    unique_tracks = set((track['master_metadata_track_name'], track['master_metadata_album_artist_name'], track['master_metadata_album_album_name']) for track in tracks)
    with open(filename, 'w', encoding='utf-8') as file:
        for track_info in unique_tracks:
            file.write(f"{track_info[0]}*& {track_info[1]}@% {track_info[2]}\n")

# Process all JSON files in the directory
for filename in os.listdir('.'):
    if filename.endswith('.json'):
        with open(filename, 'r', encoding='utf-8') as file:
            tracks = json.load(file)
        
        # Export unique tracks to a file
        export_unique_tracks(tracks, f'tracks_{START_DATE_STR}_{END_DATE_STR}.txt')

graph_playtime_by_hour(all_hourly_playtime, f"Time of listening ({START_DATE_STR} - {END_DATE_STR})")
graph_most_played(all_track_playtime, f"Top {TOP_N} tracks based on listening duration ({START_DATE_STR} - {END_DATE_STR})", 'Playtime (hours)',  True)
graph_most_played(all_artist_playtime, f"Top {TOP_N} artists based on listening duration ({START_DATE_STR} - {END_DATE_STR})", 'Playtime (hours)', True)
graph_most_played(all_album_playtime, f"Top {TOP_N} albums based on listening duration ({START_DATE_STR} - {END_DATE_STR})", 'Playtime (hours)', True)

graph_most_played(track_playnum, f"Top {TOP_N} tracks based on number of plays ({START_DATE_STR} - {END_DATE_STR})", 'Plays', False)
graph_most_played(artist_playnum, f"Top {TOP_N} artists based on number of plays ({START_DATE_STR} - {END_DATE_STR})", 'Plays', False)
graph_most_played(album_playnum, f"Top {TOP_N} albums based on number of plays ({START_DATE_STR} - {END_DATE_STR})", 'Plays', False)

input("\nPress enter to exit.")