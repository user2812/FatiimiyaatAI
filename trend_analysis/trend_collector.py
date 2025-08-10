import os
import csv
import tweepy
from pymongo import MongoClient, UpdateOne
from dotenv import load_dotenv

class TrendCollector:
    def __init__(self):
        """
        Initializes the Trend Collector, connects to MongoDB, and authenticates with the Twitter API.
        """
        # Load environment variables from .env file
        load_dotenv()

        # MongoDB Connection
        self.mongo_client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
        self.db = self.mongo_client['trends']
        self.reviews_collection = self.db['reviews']
        self.twitter_collection = self.db['twitter_posts']
        print("Successfully connected to MongoDB.")

        # Twitter API Authentication
        bearer_token = os.getenv("TWITTER_BEARER_TOKEN")
        if not bearer_token:
            raise ValueError("TWITTER_BEARER_TOKEN environment variable not set.")

        self.twitter_client = tweepy.Client(bearer_token)
        print("Successfully authenticated with Twitter API.")

    def collect_reviews_from_csv(self, csv_path):
        """
        Reads customer reviews from a CSV file and stores them in MongoDB.
        Assumes CSV has headers: review_id, product_id, user_id, rating, review_text
        Uses review_id to prevent duplicate entries.
        """
        try:
            with open(csv_path, mode='r', encoding='utf-8') as infile:
                reader = csv.DictReader(infile)
                operations = []
                for row in reader:
                    # Create an operation for each row
                    operations.append(
                        UpdateOne(
                            {'review_id': row['review_id']},
                            {'$set': row},
                            upsert=True
                        )
                    )

                if operations:
                    # Bulk write is more efficient than many single writes
                    self.reviews_collection.bulk_write(operations)
                    print(f"Upserted {len(operations)} reviews from {csv_path}")

        except FileNotFoundError:
            print(f"Error: The file {csv_path} was not found.")
        except Exception as e:
            print(f"An error occurred while processing the CSV file: {e}")

    def collect_tweets(self, query, count=100):
        """
        Collects tweets based on a query and stores them in MongoDB.
        Uses tweet ID to prevent duplicate entries.
        """
        try:
            print(f"Searching for tweets with query: {query}")
            # Use the search_recent_tweets method
            response = self.twitter_client.search_recent_tweets(
                query,
                max_results=count,
                tweet_fields=["created_at", "author_id", "public_metrics", "lang"]
            )

            if not response.data:
                print("No tweets found for the given query.")
                return

            operations = []
            for tweet in response.data:
                tweet_doc = {
                    'tweet_id': tweet.id,
                    'text': tweet.text,
                    'created_at': tweet.created_at,
                    'author_id': tweet.author_id,
                    'lang': tweet.lang,
                    'metrics': tweet.public_metrics
                }
                operations.append(
                    UpdateOne(
                        {'tweet_id': tweet.id},
                        {'$set': tweet_doc},
                        upsert=True
                    )
                )

            if operations:
                self.twitter_collection.bulk_write(operations)
                print(f"Upserted {len(operations)} tweets.")

        except tweepy.errors.TweepyException as e:
            print(f"An error occurred while fetching tweets: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

if __name__ == '__main__':
    try:
        collector = TrendCollector()

        # 1. Collect from CSV
        csv_path = 'data/reviews.csv'
        print(f"--- Starting CSV Collection from {csv_path} ---")
        collector.collect_reviews_from_csv(csv_path)
        print("--- Finished CSV Collection ---")

        # 2. Collect from Twitter
        twitter_query = '#modestfashion OR #abaya -is:retweet'
        print(f"--- Starting Twitter Collection for query: '{twitter_query}' ---")
        collector.collect_tweets(twitter_query, count=100)
        print("--- Finished Twitter Collection ---")

    except ValueError as e:
        # This will catch the error from the constructor if the bearer token is not set.
        print(f"Configuration Error: {e}")
        print("Please ensure your TWITTER_BEARER_TOKEN is set in a .env file or as an environment variable.")
    except Exception as e:
        print(f"An unexpected error occurred during execution: {e}")
