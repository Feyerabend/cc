# PROTOTYPE: Recipe recommendation app
# Status: Early concept - testing core matching logic

# TODO: Add real database, user auth, better algorithm

# Mock data for prototyping (would come from DB later)
RECIPES = [
    {"name": "Spaghetti Carbonara", "ingredients": ["pasta", "eggs", "bacon", "cheese"], "time": 20},
    {"name": "Chicken Stir Fry", "ingredients": ["chicken", "rice", "soy_sauce", "vegetables"], "time": 25},
    {"name": "Veggie Omelette", "ingredients": ["eggs", "cheese", "vegetables", "butter"], "time": 10},
    {"name": "Grilled Cheese", "ingredients": ["bread", "cheese", "butter"], "time": 5},
    {"name": "Fried Rice", "ingredients": ["rice", "eggs", "soy_sauce", "vegetables"], "time": 15},
]

# User's available ingredients (hardcoded for prototype)
USER_PANTRY = ["eggs", "cheese", "rice", "vegetables"]

def find_recipes(pantry, max_time=30):
    """
    PROTOTYPE FUNCTION: Find recipes user can make
    NOTE: Using simple matching - production would use ML/better scoring
    """
    matches = []
    
    for recipe in RECIPES:
        # Count how many ingredients user has
        matching_ingredients = [ing for ing in recipe["ingredients"] if ing in pantry]
        match_percent = len(matching_ingredients) / len(recipe["ingredients"]) * 100
        
        # PLACEHOLDER: Just checking if we can make it at all
        # TODO: Add partial match suggestions, substitutions
        if match_percent >= 75 and recipe["time"] <= max_time:  # Arbitrary threshold
            matches.append({
                "recipe": recipe["name"],
                "match": f"{match_percent:.0f}%",
                "missing": [ing for ing in recipe["ingredients"] if ing not in pantry],
                "time": recipe["time"]
            })
    
    return matches

def show_recommendations():
    """Quick UI simulation - would be real GUI/web interface later"""
    print("\nRECIPE FINDER PROTOTYPE\n")
    print(f"\nYour pantry: {', '.join(USER_PANTRY)}")
    print("\nWhat can you make?\n")
    
    results = find_recipes(USER_PANTRY)
    
    if results:
        for i, match in enumerate(results, 1):
            print(f"{i}. {match['recipe']}")
            print(f"   Match: {match['match']} | Time: {match['time']} min")
            if match['missing']:
                print(f"   Missing: {', '.join(match['missing'])}")
            print()
    else:
        print("No recipes found. (Prototype note: Algorithm too strict?)")
    
    # PROTOTYPE: Fake user interaction
    print("\n[In real app: user would click recipe for details]")
    print("[PLACEHOLDER: Would show cooking instructions here]")

# Test the prototype
show_recommendations()

print("\nPROTOTYPE NOTES FOR REVIEW:\n")
print("+ Core matching logic works")
print("+ Can test with different pantry items")
print("- Need better algorithm (too many false negatives)")
print("- Add ingredient substitutions (butter->oil)")
print("- Connect to real recipe API")
print("- Build actual UI (web or mobile)")
print("? Should we add dietary restrictions filter?")
print("? User feedback on match quality?")
