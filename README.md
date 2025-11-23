# Setify

Check out project here: [INSERT LINK]

## Why Setify?

I love music and going to concerts, but I always found myself wondering: what songs are they actually going to play? There's nothing worse than showing up to a show and realizing you don't know half the setlist. Setify solves this problem by analyzing an artist's recent setlists and predicting what songs are most likely to appear at their next show.

Whether you're preparing for your first concert or your hundredth, Setify helps you study up on the songs you're most likely to hear, complete with probability scores and appearance statistics.

## Technologies

**Frontend:**
- React 19
- Vite
- Tailwind CSS
- Modern ES6+ JavaScript

**Backend:**
- FastAPI
- Python 3
- Uvicorn

## APIs

### Setlist.fm API

Setify uses the [Setlist.fm API](https://www.setlist.fm/help/api) to fetch historical setlist data for artists. This provides the foundation for our predictions by analyzing which songs have been played most frequently and recently across an artist's tour history.

### Spotify API

The [Spotify Web API](https://developer.spotify.com/documentation/web-api) enhances predictions by:
- Matching setlist songs to official Spotify tracks
- Incorporating track popularity metrics
- Identifying new album releases that haven't appeared in setlists yet
- Boosting predictions for top tracks and recent releases

## Prediction Model

Setify currently uses a **recency-weighted frequency model** that combines:

1. **Frequency Analysis**: Songs that appear more often across setlists get higher scores
2. **Recency Weighting**: Recent setlists are weighted more heavily than older ones using exponential decay (half-life of 240 days)
3. **Spotify Integration**: 
   - Top tracks receive popularity-based boosts
   - New album tracks are included even if they haven't appeared in setlists yet
   - Track popularity influences final probability scores

The model calculates a base score from frequency and recency, then applies Spotify-based adjustments to produce final probability predictions. Songs are ranked and the top 28 are returned with their likelihood percentages.

**Note**: We're planning to migrate to a machine learning-based prediction model in the near future to improve accuracy and handle more complex patterns in setlist data.
