from flask import Flask, render_template, request, redirect, url_for
from pymongo import MongoClient
import requests # New import
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration for file uploads
UPLOAD_FOLDER = 'app/static/uploads'
RESULT_FOLDER = 'app/static/results'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER


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

from virtual_tryon.tryon_engine import TryOnEngine

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/tryon', methods=['GET', 'POST'])
def tryon():
    item_type = request.args.get('item_type', 'shirt')
    color = request.args.get('color', 'black')

    if request.method == 'POST':
        # check if the post request has the file part
        if 'user_photo' not in request.files:
            return redirect(request.url)
        file = request.files['user_photo']
        if file.filename == '':
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            # Save the uploaded file
            user_image_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(user_image_path)

            # Define clothing and output paths
            clothing_image_path = f'app/static/clothes/{item_type.lower()}.png'
            output_filename = f"result_{filename}"
            output_image_path = os.path.join(app.config['RESULT_FOLDER'], output_filename)

            # Run the try-on engine
            try:
                engine = TryOnEngine()
                engine.apply_tryon(user_image_path, clothing_image_path, output_image_path)
            except Exception as e:
                print(f"Error during try-on process: {e}")
                # Render the page with an error message
                return render_template('tryon.html', item_type=item_type, color=color, error="Failed to process image.")

            # Render the page again, this time with the result image
            return render_template('tryon.html',
                                   item_type=item_type,
                                   color=color,
                                   result_image=f'results/{output_filename}')

    # For the GET request, just show the upload page
    return render_template('tryon.html', item_type=item_type, color=color)

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

@app.route('/my_data', methods=['GET', 'POST'])
def my_data():
    user_id = "mock_user_123"

    if request.method == 'POST':
        updated_items = request.form.getlist("items")
        updated_preferences = {
            "user_id": user_id,
            "items": updated_items,
            "color": request.form.get("color")
        }
        preferences_collection.update_one({'user_id': user_id}, {'$set': updated_preferences}, upsert=True)

        # Re-initialize scores after preferences are updated
        try:
            init_payload = {'user_id': user_id, 'quiz_items': updated_items}
            requests.post(f"{RECOMMENDER_API_URL}/initialize", json=init_payload)
        except requests.exceptions.RequestException as e:
            print(f"Error calling recommender API: {e}")

        return redirect(url_for('recommendations'))

    user_prefs = preferences_collection.find_one({'user_id': user_id})
    if not user_prefs:
        return redirect(url_for('quiz'))

    return render_template('my_data.html', prefs=user_prefs)

@app.route('/disable_personalization', methods=['POST'])
def disable_personalization():
    user_id = "mock_user_123"

    # Delete from the local preferences collection
    preferences_collection.delete_one({'user_id': user_id})

    # NEW: Call the recommender API to delete the user's score history
    try:
        requests.delete(f"{RECOMMENDER_API_URL}/user/{user_id}")
    except requests.exceptions.RequestException as e:
        print(f"Error calling recommender API to delete user history: {e}")
        # Depending on the desired behavior, you might want to inform the user
        # that part of the deletion failed. For now, we just log it.

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

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    item_type = request.form.get('item_type')
    color = request.form.get('color')
    print(f"EVENT: Item added to cart! Type: {item_type}, Color: {color}")
    # In a real application, you would add this item to the user's session/cart in the database.
    return redirect(url_for('recommendations'))

if __name__ == '__main__':
    app.run(debug=True) # Runs on default port 5000
