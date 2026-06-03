import json
from flask import Flask, jsonify, request
import pandas as pd
from supabase import create_client, Client
import os
from dotenv import load_dotenv
from flask_cors import CORS, cross_origin
from nba_api.stats.static import players

app = Flask(__name__)
cors = CORS(app) 
load_dotenv()

supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")

if not supabase_url or not supabase_key:
    raise ValueError("Missing Supabase credentials. Check .env file.")

supabase = create_client(supabase_url, supabase_key)


@app.route('/about')
def about():
    return 'About'





@app.route('/players', methods=["GET"])
def get_players_data():
    
    try:
        name_filter = request.args.get('name', default='', type=str)
        team_filter = request.args.get('team', default='', type=str)
        position_filter = request.args.get('position', default='', type=str)
        
        query = supabase.table("player").select("*")
        
        if name_filter:
            query = query.ilike("player", f"%{name_filter}%")  # Case-insensitive search for name
        if team_filter:
            query = query.ilike("team", f"%{team_filter}%")
        if position_filter:
            query = query.ilike("position", f"%{position_filter}%")
        query.ilike('to',  "2025.0%")
        
        response = query.execute()

        return jsonify(response.data), 200
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({"error": str(e)}), 500
    
    
    
@app.route('/career_stats', methods=["GET"])
def get_career_stats_data():
    try:
        response = supabase.table("career_stats").select("*").execute()
        return jsonify(response.data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

    
    
@app.route('/season_stats', methods=["GET"])
def get_current_stats_data():
    try:
        response = supabase.table("current_stats").select("*").execute()
        
        return jsonify(response.data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/player/<player_id>', methods=['GET'])
def get_player_with_stats(player_id):
    try:
        player_response = supabase.table("player").select("*").eq("player_id", player_id).single().execute()
        player_data = player_response.data if player_response and hasattr(player_response, 'data') else None

        if not player_data:
            return jsonify({"error": "Player not found"}), 404

        player_name = player_data['player']  # Assuming 'player' contains the player's full name
        nba_api_id = fetch_nba_api(player_name)

        # Fetch stats data
        stats_response = supabase.table("current_stats").select("*").eq("player_id", player_id).single().execute()
        stats_data = stats_response.data if stats_response and hasattr(stats_response, 'data') else {}

        # Fetch awards data
        awards_response = supabase.table("awards").select("*").eq("player_id", player_id).execute()
        awards_data = awards_response.data if awards_response and hasattr(awards_response, 'data') else {}

        shots = fetch_shot_data(player_id)
        
        result = {
            "player": player_data,
            "stats": stats_data,
            "awards": awards_data,
            "nba_id": nba_api_id,
            "headshot_url": f"https://cdn.nba.com/headshots/nba/latest/1040x760/{nba_api_id}.png" if nba_api_id else None,
            "shot_data": shots
        }

        return jsonify(result)
    except Exception as e:
        print("Error:", e)
        return jsonify({"error": str(e)}), 500

# Function to fetch NBA API player ID by full name
def fetch_nba_api(player_name):
    try:
        found = players.find_players_by_full_name(player_name)
        if found:
            return found[0]['id']  # Return the first matching player's ID
        return None  # Return None if player not found
    except Exception as e:
        print("Error fetching NBA API data:", e)
        return None
    
#function to fetch shot chart data from local json file     
def fetch_shot_data(player_id):
    try:
        df = pd.read_json('api/shots.json')
        df.set_index('playerId',inplace=True)
       
        return df.loc[player_id].to_list()
    except Exception as e:
        print("Error fetch_shot_data:", e)
        return None


# API endpoint to fetch multiple player images
# @app.route('/players/imgs', methods=['GET'])
# def fetch_nba_imgs():
   
#     try:
#         player_names = request.args.getlist('players')  # Get list of player names from query params
#         input_string = player_names[0]
#         player_names_list = input_string.split(',')
#         print(player_names_list)
#         if not player_names_list:
#             return jsonify({"error": "No player names provided"}), 400

#         images = {}
#         for name in player_names_list:
#             nba_id = fetch_nba_api(name)
#             images[name] = f"https://cdn.nba.com/headshots/nba/latest/1040x760/{nba_id}.png" if nba_id else None

#         return jsonify(images)
#     except Exception as e:
#         print("Error:", e)
        return jsonify({"error": str(e)}), 500
    

if __name__ == "__main__":
    app.run(debug=True)

