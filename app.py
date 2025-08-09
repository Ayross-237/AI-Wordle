from flask import Flask, render_template, request, jsonify, session, redirect, url_for
import random
import json
from collections import Counter

app = Flask(__name__)
app.secret_key = "replace_this_with_a_random_secret_in_production"

# --- Word lists (a compact set for demo) ---
# You can expand these lists with official Wordle lists if you want.
SOLUTIONS = [
    "crane","slate","shine","grace","baker","panel","trace","flute","pride","place",
    "plane","charm","glory","fling","sword","brush","light","grain","brand","stone",
    "sound","greet","sweet","right","might","world","house","score","proud","bring",
    "shard","clear","faint","stare","pride","heart","steal","phase","quake","orbit",
    "cabin","ember","eager","vivid","storm","chime","beach","ditch","forge","glide",
    "jumbo","knelt","liver","medal","naval","ocean","pound","quart","retry","shrub",
    "tango","ultra","vapor","wrist","xenon","yacht","zesty","about","other","which",
    "their","there","would","could","light","apple","berry","chess","drove","eagle",
    "fable","ghost","hover","idiom","jelly","karma","lobby","mango","noble","opium",
    "piano","quilt","robin","salty","tempo","union","vigor","whale","yodel","zebra",
    "adore","blush","civic","dodge","elope","fiscal","gorge","hover","ideal","joust",
    "kneel","lager","mimic","nexus","olive","proxy","radii","siren","tepid","usage",
    "vowel","wrath","young","zonal","amber","bloom","caper","diner","epoch","feast",
    "gamer","harpy","ivory","japan","knock","lunar","moral","nomad","ovary","perch",
    "quest","ranch","sheen","tulip","uncle","vicar","wedge","yummy","amber","briar",
    "clasp","dwarf","endue","frozen","gusto","hefty","inlet","jolly","kudos","lemur",
]
# Allowed guesses: include solutions plus some extras (kept simple)
ALLOWED = list(set(SOLUTIONS + [
    "arise","roate","later","crate","slant","stole","slump","pacer","admit","blend",
    "crown","flick","glint","prank","shone","snail","taste","unite","vouch","worst",
    "xerox","yours","zings"
]))

# --- Utility functions ---
def compute_feedback(guess: str, target: str):
    """
    Return feedback as list: 'correct' (green), 'present' (yellow), 'absent' (gray)
    Wordle rules apply (greens assigned first, then yellows respecting counts).
    """
    guess = guess.lower()
    target = target.lower()
    fb = ['absent'] * 5
    target_counts = Counter(target)

    # Greens first
    for i, (g, t) in enumerate(zip(guess, target)):
        if g == t:
            fb[i] = 'correct'
            target_counts[g] -= 1

    # Yellows
    for i, g in enumerate(guess):
        if fb[i] == 'correct':
            continue
        if target_counts[g] > 0:
            fb[i] = 'present'
            target_counts[g] -= 1
    return fb

def filter_candidates(candidates, guess, feedback):
    """
    Return a filtered list of candidates that would produce the same feedback
    if guess were applied to them.
    """
    out = []
    for cand in candidates:
        if compute_feedback(guess, cand) == feedback:
            out.append(cand)
    return out

def score_word(word, candidates):
    """
    Score by letter frequency across candidates, favoring unique letters.
    """
    freq = Counter("".join(candidates))
    score = 0
    seen = set()
    for ch in word:
        if ch not in seen:
            score += freq[ch]
            seen.add(ch)
    return score

def ai_pick(candidates):
    """
    Choose best-scoring candidate from allowed list. Prefer true candidates if tie.
    """
    best = None
    best_score = -1
    for w in ALLOWED:
        sc = score_word(w, candidates)
        if sc > best_score or (sc == best_score and w in candidates and best not in candidates):
            best_score = sc
            best = w
    return best

# --- Session game helpers ---
def new_game():
    p_target = random.choice(SOLUTIONS)
    ai_target = random.choice(SOLUTIONS)
    # ensure different to be fair (optional)
    while ai_target == p_target:
        ai_target = random.choice(SOLUTIONS)

    state = {
        "player": {
            "target": p_target,
            "board": [],  # list of {guess, feedback}
            "won": False
        },
        "ai": {
            "target": ai_target,
            "board": [],
            "won": False,
            "candidates": SOLUTIONS.copy(),
            "last_guess": None
        },
        "game_over": False
    }
    return state

def get_state():
    if 'game' not in session:
        session['game'] = new_game()
    return session['game']

def save_state(state):
    session['game'] = state

# --- Routes ---
@app.route("/")
def index():
    # ensure a game exists
    state = get_state()
    return render_template("index.html", state=json.dumps(state))

@app.route("/new", methods=["POST"])
def restart():
    state = new_game()
    save_state(state)
    return jsonify(success=True, state=state)

@app.route("/guess", methods=["POST"])
def guess():
    data = request.get_json()
    guess = data.get("guess", "").lower().strip()
    if not guess or len(guess) != 5:
        return jsonify(error="Guess must be 5 letters."), 400

    state = get_state()

    if state['game_over']:
        return jsonify(error="Game already finished."), 400

    # validate
    if guess not in ALLOWED:
        return jsonify(error="Word not in allowed list."), 400

    # Player's turn: apply guess vs player's target
    p_target = state['player']['target']
    p_feedback = compute_feedback(guess, p_target)
    state['player']['board'].append({"guess": guess, "feedback": p_feedback})
    if all(f == 'correct' for f in p_feedback):
        state['player']['won'] = True
        state['game_over'] = True
        save_state(state)
        return jsonify(result="player_won", state=state)

    # If player hasn't won, AI makes a guess (single step)
    ai_state = state['ai']
    # If AI has no last guess yet, choose CRANE or best initial
    if ai_state['last_guess'] is None:
        ai_guess = "crane" if "crane" in ALLOWED else ai_pick(ai_state['candidates'])
    else:
        # filter candidates using previous feedback
        # already stored in ai_state['candidates']
        ai_guess = ai_pick(ai_state['candidates'])

    ai_state['last_guess'] = ai_guess
    ai_feedback = compute_feedback(ai_guess, ai_state['target'])
    ai_state['board'].append({"guess": ai_guess, "feedback": ai_feedback})

    # Update candidates
    ai_state['candidates'] = filter_candidates(ai_state['candidates'], ai_guess, ai_feedback)

    # Check AI win
    if all(f == 'correct' for f in ai_feedback):
        ai_state['won'] = True
        state['game_over'] = True

    save_state(state)
    return jsonify(result="ok", state=state)

# For debugging: show session state
@app.route("/state")
def show_state():
    return jsonify(session.get('game', {}))

if __name__ == "__main__":
    app.run(debug=True)
