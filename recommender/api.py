from flask import Flask, request, jsonify
from recommender_engine import RecommenderEngine

app = Flask(__name__)
engine = RecommenderEngine()

@app.route('/initialize', methods=['POST'])
def initialize_user():
    """
    Initializes a user's scores based on their quiz results.
    Expects JSON data with: {'user_id', 'quiz_items'}
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    user_id = data.get('user_id')
    quiz_items = data.get('quiz_items')

    if not all([user_id, quiz_items]):
        return jsonify({"error": "Missing data"}), 400

    engine.initialize_scores_from_quiz(user_id, quiz_items)
    return jsonify({"status": "success", "message": f"User {user_id} initialized."}), 200

@app.route('/recommendations/<user_id>', methods=['GET'])
def get_recommendations(user_id):
    """
    Generates and returns recommendations for a given user.
    """
    recommendations = engine.generate_recommendations(user_id)
    return jsonify(recommendations)

@app.route('/feedback', methods=['POST'])
def handle_feedback():
    """
    Receives feedback from the user and updates their scores.
    Expects JSON data with: {'user_id', 'item_type', 'feedback_type'}
    'feedback_type' can be 'see_more', 'less_of_this_type', or 'delete'.
    """
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    user_id = data.get('user_id')
    item_type = data.get('item_type')
    feedback_type = data.get('feedback_type')

    if not all([user_id, item_type, feedback_type]):
        return jsonify({"error": "Missing data"}), 400

    # Define the score change based on feedback
    if feedback_type == 'see_more':
        score_change = 1
    elif feedback_type == 'less_of_this_type':
        score_change = -1
    elif feedback_type == 'delete':
        score_change = -2 # 'delete' is a strong negative signal
    else:
        score_change = 0

    if score_change != 0:
        engine.update_score(user_id, item_type, score_change)

    return jsonify({"status": "success", "message": "Feedback received"}), 200

@app.route('/user/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    """
    Deletes all data associated with a user.
    """
    deleted_count = engine.delete_user_history(user_id)
    return jsonify({"status": "success", "message": f"Deleted {deleted_count} score entries for user {user_id}."}), 200

if __name__ == '__main__':
    # Run on a different port to avoid conflict with the main UI app
    app.run(port=5001, debug=True)
