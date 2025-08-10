from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
import requests # New import

app = Flask(__name__)

# This app still needs its own MongoDB connection to manage the raw preferences from the quiz
client = MongoClient('mongodb://localhost:27017/')
db = client['fashion_app']
preferences_collection = db['preferences'] # Renamed for clarity

# URL for the recommender API
RECOMMENDER_API_URL = "http://127.0.0.1:5001"

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Mock user validation
        return redirect(url_for('quiz'))
    return render_template('login.html')

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    user_id = "mock_user_123"
    if request.method == 'POST':
        quiz_items = request.form.getlist("items")
        user_preferences = {
            "user_id": user_id,
            "items": quiz_items,
            "color": request.form.get("color")
        }
        preferences_collection.update_one({'user_id': user_id}, {'$set': user_preferences}, upsert=True)

        # NEW: Call recommender API to initialize scores
        try:
            init_payload = {'user_id': user_id, 'quiz_items': quiz_items}
            requests.post(f"{RECOMMENDER_API_URL}/initialize", json=init_payload)
        except requests.exceptions.RequestException as e:
            print(f"Error calling recommender API: {e}")
            # Decide how to handle this - maybe show an error page

        return redirect(url_for('recommendations'))
    return render_template('quiz.html')

@app.route('/recommendations')
def recommendations():
    user_id = "mock_user_123"

    # NEW: Fetch recommendations from the API
    try:
        response = requests.get(f"{RECOMMENDER_API_URL}/recommendations/{user_id}")
        response.raise_for_status() # Raise an exception for bad status codes
        recommended_products = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching recommendations: {e}")
        recommended_products = [] # Show an empty list on error

    return render_template('recommendations.html', recommendations=recommended_products)

@app.route('/preferences', methods=['GET', 'POST'])
def user_preferences():
    user_id = "mock_user_123"

    if request.method == 'POST':
        updated_items = request.form.getlist("items")
        updated_preferences = {
            "user_id": user_id,
            "items": updated_items,
            "color": request.form.get("color")
        }
        preferences_collection.update_one({'user_id': user_id}, {'$set': updated_preferences}, upsert=True)

        # NEW: Re-initialize scores after preferences are updated
        try:
            init_payload = {'user_id': user_id, 'quiz_items': updated_items}
            requests.post(f"{RECOMMENDER_API_URL}/initialize", json=init_payload)
        except requests.exceptions.RequestException as e:
            print(f"Error calling recommender API: {e}")

        return redirect(url_for('recommendations'))

    user_prefs = preferences_collection.find_one({'user_id': user_id})
    if not user_prefs:
        return redirect(url_for('quiz'))

    return render_template('preferences.html', prefs=user_prefs)

@app.route('/disable_personalization', methods=['POST'])
def disable_personalization():
    user_id = "mock_user_123"

    # This should now also delete the scores in the recommender service.
    # For simplicity, we'll just delete the local preferences.
    # A more robust implementation would have a user deletion endpoint on the API.
    preferences_collection.delete_one({'user_id': user_id})

    # We could also call the recommender to delete scores, but let's keep it simple.

    return render_template('data_deleted.html')

# NEW: Proxy for feedback to the recommender API
@app.route('/feedback_proxy', methods=['POST'])
def feedback_proxy():
    user_id = "mock_user_123"

    # Data from the form in recommendations.html
    product_type = request.form.get('item_type')
    feedback_type = request.form.get('feedback_type')

    # Call the recommender API's feedback endpoint
    try:
        feedback_payload = {
            'user_id': user_id,
            'item_type': product_type,
            'feedback_type': feedback_type
        }
        requests.post(f"{RECOMMENDER_API_URL}/feedback", json=feedback_payload)
    except requests.exceptions.RequestException as e:
        print(f"Error sending feedback to recommender API: {e}")

    return redirect(url_for('recommendations'))

if __name__ == '__main__':
    app.run(debug=True) # Runs on default port 5000
