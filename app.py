from flask import Flask, render_template, request
import pandas as pd
import heapq

app = Flask(__name__)

# Load movie data from the CSV
def load_movies():
    try:
        df = pd.read_csv('imdb_top_1000.csv')
        # Select only necessary columns
        movies = df[['Series_Title', 'Genre', 'IMDB_Rating', 'No_of_Votes']].copy()
        # Convert necessary columns to numeric types
        movies['IMDB_Rating'] = pd.to_numeric(movies['IMDB_Rating'], errors='coerce')
        movies['No_of_Votes'] = pd.to_numeric(movies['No_of_Votes'], errors='coerce')
        return movies
    except Exception as e:
        print(f"Error loading movies: {e}")
        return pd.DataFrame()  # Return an empty DataFrame on error

# A* search to find the best movies based on rating and votes
def a_star_search_best_movies(movies, min_rating=None, max_rating=None, genre1=None, genre2=None):
    def heuristic(movie):
        # Heuristic is a weighted combination of IMDb rating and votes
        rating_weight = 1.0
        votes_weight = 0.3
        
        score = (rating_weight * movie['IMDB_Rating'] + 
                 votes_weight * (movie['No_of_Votes'] / 1e6))  # Normalize votes for scoring
        return -score  # Negate score for max-heap behavior

    # Filter movies by criteria
    if min_rating and min_rating.strip() != "":
        movies = movies[movies['IMDB_Rating'] >= float(min_rating)]
    if max_rating and max_rating.strip() != "":
        movies = movies[movies['IMDB_Rating'] <= float(max_rating)]
    if genre1 and genre1.strip() != "":
        movies = movies[movies['Genre'].str.contains(genre1, case=False, na=False)]
    if genre2 and genre2.strip() != "":
        movies = movies[movies['Genre'].str.contains(genre2, case=False, na=False)]

    # Use a priority queue (max-heap) to get the best movies
    priority_queue = []
    for _, movie in movies.iterrows():
        heapq.heappush(priority_queue, (heuristic(movie), movie))

    # Return the best movies
    best_movies = []
    while priority_queue:
        best_movies.append(heapq.heappop(priority_queue)[1])

    return pd.DataFrame(best_movies)

@app.route('/', methods=['GET', 'POST'])
def index():
    movies = load_movies()  # Always reset to the full dataset at the start of a request
    
    # Initialize filtered_movies as the full dataset
    filtered_movies = movies.copy()
    
    if request.method == 'POST':
        min_rating = request.form.get('min_rating')
        max_rating = request.form.get('max_rating')
        genre1 = request.form.get('genre1')
        genre2 = request.form.get('genre2')

        # Debugging: Print received form data
        print(f"Received data: min_rating={min_rating}, max_rating={max_rating}, genre1={genre1}, genre2={genre2}")

        # Use A* search to filter and rank movies
        filtered_movies = a_star_search_best_movies(filtered_movies, min_rating, max_rating, genre1, genre2)

        # Debugging: Print number of filtered movies
        print(f"Filtered movies count: {len(filtered_movies)}")

    # Render all filtered movies or the whole dataset if no filters are applied
    return render_template('index.html', movies=filtered_movies.to_dict('records'))

if __name__ == '__main__':
    app.run(debug=True)
