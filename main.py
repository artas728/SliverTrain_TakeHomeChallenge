from fastapi import FastAPI, Query, HTTPException
from typing import List, Optional, Dict, Any
import pandas as pd
import math
from collections import defaultdict

app = FastAPI()


class TrieNode:
    def __init__(self):
        self.children = defaultdict(TrieNode)
        self.is_end_of_word = False
        self.cities = []


class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str, city: Dict[str, Any]):
        node = self.root
        for char in word:
            node = node.children[char]
        node.is_end_of_word = True
        node.cities.append(city)

    def search(self, prefix: str):
        node = self.root
        for char in prefix:
            if char in node.children:
                node = node.children[char]
            else:
                return []
        return self._collect_all_words(node)

    def _collect_all_words(self, node: TrieNode):
        results = []
        if node.is_end_of_word:
            results.extend(node.cities)
        for child in node.children.values():
            results.extend(self._collect_all_words(child))
        return results


def load_data(filepath: str):
    return pd.read_csv(filepath, delimiter='\t')


def preprocess_data(cities_df: pd.DataFrame):
    trie = Trie()
    for _, row in cities_df.iterrows():
        city = {
            "name": row['name'],
            "latitude": row['lat'],
            "longitude": row['long']
        }
        trie.insert(row['name'].lower(), city)
        if pd.notna(row['alt_name']):
            for alt_name in row['alt_name'].split(','):
                trie.insert(alt_name.lower(), city)
    return trie


def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Radius of the Earth in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = R * c
    return distance


# Load and preprocess the data
cities_df = load_data('cities_canada-usa.tsv')
trie = preprocess_data(cities_df)


@app.get("/")
def read_root():
    return {"message": "Welcome to the City Suggestions API"}


@app.get("/suggestions")
def get_suggestions(q: str = Query(..., min_length=1), latitude: Optional[float] = None,
                    longitude: Optional[float] = None):
    results = trie.search(q.lower())
    suggestions = []

    for city in results:
        score = 1.0  # Base score for a name match
        if latitude is not None and longitude is not None:
            distance = haversine(latitude, longitude, city['latitude'], city['longitude'])
            proximity_score = max(0, 1 - distance / 100)
            score = (score + proximity_score) / 2

        suggestions.append({
            "name": city['name'],
            "latitude": city['latitude'],
            "longitude": city['longitude'],
            "score": score
        })

    suggestions = sorted(suggestions, key=lambda x: x['score'], reverse=True)
    return {"suggestions": suggestions}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
