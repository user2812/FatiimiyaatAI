from pymongo import MongoClient

class RecommenderEngine:
    def __init__(self, mongo_uri='mongodb://localhost:27017/'):
        """
        Initializes the recommendation engine and connects to MongoDB.
        """
        self.client = MongoClient(mongo_uri)
        self.db = self.client['fashion_app']
        self.preferences = self.db['preferences']
        # A new collection to store user scores for item types
        self.user_scores = self.db['user_scores']
        print("RecommenderEngine initialized.")

    def initialize_scores_from_quiz(self, user_id, quiz_items):
        """
        Sets the initial scores for a user based on their quiz answers.
        This gives a starting score of 1 to each preferred item type.
        """
        for item_type in quiz_items:
            # Using update_one with upsert ensures that we don't create duplicate scores
            # if this is ever called multiple times. It sets the initial score to 1.
            self.user_scores.update_one(
                {'user_id': user_id, 'item_type': item_type},
                {'$set': {'score': 1}},
                upsert=True
            )
        print(f"Initialized scores for user {user_id} with items: {quiz_items}")

    def update_score(self, user_id, item_type, score_change):
        """
        Updates the score for a given item type for a specific user.
        A positive score_change indicates a positive interaction (e.g., 'see more').
        A negative score_change indicates a negative interaction (e.g., 'less of this type').
        """
        self.user_scores.update_one(
            {'user_id': user_id, 'item_type': item_type},
            {'$inc': {'score': score_change}},
            upsert=True
        )
        print(f"Updated score for user {user_id}, item_type {item_type} by {score_change}")

    def generate_recommendations(self, user_id):
        """
        Generates product recommendations for a given user based on their scores.

        This is a simplified hybrid model:
        - Content-Based: It recommends items based on the user's highest-scored item types.
        - Collaborative (Placeholder): In a real system, we would also find users with similar
          taste profiles (scores) and recommend items they liked. This part is not implemented
          due to the need for a larger user-item interaction dataset.
        """
        # Fetch user's scores and sort by score descending
        user_scores_cursor = self.user_scores.find({'user_id': user_id, 'score': {'$gt': 0}}).sort('score', -1)

        top_item_types = [doc['item_type'] for doc in user_scores_cursor]

        if not top_item_types:
            print(f"No positive scores found for user {user_id}. Cannot generate recommendations.")
            return []

        # Fetch the user's general color preference from the quiz data
        user_prefs = self.preferences.find_one({'user_id': user_id})
        pref_color = user_prefs.get('color', 'black') if user_prefs else 'black'

        # --- Collaborative Filtering Placeholder ---
        # In a real system, you would do something like this:
        # 1. Find a set of 'similar_users' to the current user based on their score vectors.
        # 2. Get the items liked by these similar users.
        # 3. Filter out items the current user has already interacted with.
        # 4. Combine these collaboratively-filtered items with the content-based items below.
        # For now, we will stick to the content-based approach.

        # --- Content-Based Recommendation Generation ---
        recommended_products = []
        for item_type in top_item_types:
            # For simplicity, we create mock product data. In a real system, this would
            # query a product catalog for available items of this type and color.
            recommended_products.append({
                "name": f"{pref_color.capitalize()} {item_type.capitalize()}",
                "type": item_type,
                "color": pref_color,
                "image_url": "https://via.placeholder.com/200" # Placeholder image
            })

        print(f"Generated {len(recommended_products)} recommendations for user {user_id}")
        return recommended_products

    def delete_user_history(self, user_id):
        """
        Deletes all score history for a given user.
        """
        result = self.user_scores.delete_many({'user_id': user_id})
        print(f"Deleted {result.deleted_count} score entries for user {user_id}")
        return result.deleted_count

if __name__ == '__main__':
    # Example usage (for testing purposes)
    engine = RecommenderEngine()
    # This is where we could add test calls to the engine's methods.
