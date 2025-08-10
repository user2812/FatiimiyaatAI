from flask import Flask, render_template, request, jsonify, redirect, url_for
from pymongo import MongoClient

app = Flask(__name__)

# MongoDB Configuration
client = MongoClient('mongodb://localhost:27017/')
db = client['fashion_app']
users = db['users']
preferences = db['preferences']

@app.route('/')
def index():
    # Redirect to login for now
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        # Mock user validation
        print(f"Login attempt with email: {email}") # For debugging
        # In a real app, you'd validate the password here
        # For now, just redirect to the quiz page
        return redirect(url_for('quiz'))
    return render_template('login.html')

@app.route('/quiz', methods=['GET', 'POST'])
def quiz():
    if request.method == 'POST':
        # For simplicity, we'll use a hardcoded user_id.
        # In a real app, you'd get this from the session after login.
        user_id = "mock_user_123"

        user_preferences = {
            "user_id": user_id,
            "items": request.form.getlist("items"),
            "color": request.form.get("color")
        }

        # Save to MongoDB
        # Use update_one with upsert=True to create or update the user's preferences
        preferences.update_one({'user_id': user_id}, {'$set': user_preferences}, upsert=True)

        print(f"Saved preferences for user {user_id}: {user_preferences}") # For debugging

        return redirect(url_for('recommendations'))
    return render_template('quiz.html')

@app.route('/recommendations')
def recommendations():
    # For simplicity, we'll use a hardcoded user_id.
    user_id = "mock_user_123"

    user_prefs = preferences.find_one({'user_id': user_id})

    recommended_products = []
    if user_prefs:
        # Simple recommendation logic: generate products based on preferences
        pref_items = user_prefs.get('items', [])
        pref_color = user_prefs.get('color', 'any')

        for item in pref_items:
            recommended_products.append({
                "name": f"{pref_color.capitalize()} {item.capitalize()}",
                "type": item,
                "color": pref_color,
                "image_url": "https://via.placeholder.com/200" # Placeholder image
            })

    return render_template('recommendations.html', recommendations=recommended_products)

@app.route('/preferences', methods=['GET', 'POST'])
def user_preferences():
    user_id = "mock_user_123"

    if request.method == 'POST':
        updated_preferences = {
            "user_id": user_id,
            "items": request.form.getlist("items"),
            "color": request.form.get("color")
        }
        preferences.update_one({'user_id': user_id}, {'$set': updated_preferences}, upsert=True)
        return redirect(url_for('recommendations'))

    user_prefs = preferences.find_one({'user_id': user_id})
    if not user_prefs:
        # If user has no prefs yet, redirect to quiz
        return redirect(url_for('quiz'))

    return render_template('preferences.html', prefs=user_prefs)

@app.route('/disable_personalization', methods=['POST'])
def disable_personalization():
    user_id = "mock_user_123"

    # Delete the user's preferences from MongoDB
    result = preferences.delete_one({'user_id': user_id})

    if result.deleted_count > 0:
        print(f"Deleted data for user {user_id}") # For debugging
    else:
        print(f"No data found to delete for user {user_id}") # For debugging

    return render_template('data_deleted.html')

@app.route('/feedback', methods=['POST'])
def feedback():
    feedback_type = request.form.get('feedback_type')
    product_name = request.form.get('product_name')

    print(f"Received feedback: '{feedback_type}' for product '{product_name}'")

    # In a real app, you would use this feedback to adjust recommendations.
    # For now, we just redirect back to the recommendations page.
    return redirect(url_for('recommendations'))

if __name__ == '__main__':
    app.run(debug=True)
