from flask import Flask, render_template, request, jsonify
import os
import random
import math
import json

app = Flask(__name__)

# Constants
MEME_DIR = "static/memes"
SAVE_FILE = "data/meme_progress.json"

# Globals
meme_ratings = {}
comparisons = []


# Helper functions
def save_progress():
    """Save meme ratings and comparisons to a file."""
    with open(SAVE_FILE, "w") as f:
        json.dump({
            "meme_ratings": meme_ratings,
            "comparisons": comparisons
        }, f)


def load_progress():
    """Load meme ratings and comparisons from a file."""
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r") as f:
            data = json.load(f)
            return data.get("meme_ratings", {}), data.get("comparisons", [])
    return {}, []


def initialize_memes():
    """Initialize memes and load progress if available."""
    global meme_ratings, comparisons
    meme_ratings, comparisons = load_progress()

    if not meme_ratings or not comparisons:  # Start fresh if no save file
        valid_extensions = ('jpg', 'jpeg', 'png', 'gif', 'mp4', 'webm', 'ogg')
        memes = [f for f in os.listdir(MEME_DIR) if f.endswith(valid_extensions)]
        meme_ratings = {meme: 1000 for meme in memes}
        comparisons = [(memes[i], memes[j]) for i in range(len(memes)) for j in range(i + 1, len(memes))]
        random.shuffle(comparisons)
        save_progress()  # Save initial state


def calculate_elo_change(ratingA, ratingB, outcome):
    """Calculate Elo rating change based on match outcome."""
    K = 32
    expectedA = 1 / (1 + math.pow(10, (ratingB - ratingA) / 400))
    return K * (outcome - expectedA)


# Routes
@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')


@app.route('/get-pair', methods=['GET'])
def get_pair():
    """Get the next pair of memes to compare."""
    if comparisons:
        pair = comparisons.pop()
        save_progress()  # Save progress after popping a pair
        remaining = len(comparisons)
        total = remaining + len(meme_ratings) - 1  # Calculate total comparisons
        return jsonify({'pair': pair, 
                        'ratings': [meme_ratings[pair[0]], meme_ratings[pair[1]]],
                        'remaining': remaining,
                        'total': total})
    return jsonify({'pair': None})


@app.route('/submit-result', methods=['POST'])
def submit_result():
    """Process the result of a comparison."""
    data = request.json
    memeA, memeB = data['pair']
    winner = data['winner']

    ratingA = meme_ratings[memeA]
    ratingB = meme_ratings[memeB]

    if winner == 'A':
        changeA = calculate_elo_change(ratingA, ratingB, 1)
        changeB = -changeA
    elif winner == 'B':
        changeB = calculate_elo_change(ratingB, ratingA, 1)
        changeA = -changeB
    else:  # Tie
        changeA = 0
        changeB = 0

    meme_ratings[memeA] += changeA
    meme_ratings[memeB] += changeB

    save_progress()  # Save after each result

    return jsonify({'ratings': [meme_ratings[memeA], meme_ratings[memeB]]})


@app.route('/leaderboard', methods=['GET'])
def leaderboard():
    """Get the current leaderboard."""
    sorted_memes = sorted(meme_ratings.items(), key=lambda x: x[1], reverse=True)
    return jsonify(sorted_memes)


# Main entry point
if __name__ == '__main__':
    initialize_memes()
    app.run(debug=True)
