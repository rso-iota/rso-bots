import math
from typing import Tuple

class BotStrategy:
    def __init__(self):
        pass
        
    def calculate_move(self, game_state, bot_name) -> Tuple[float, float]:
        """Calculate next move based on game state"""
        if not game_state:
            return 0, 0
            
        # Find our bot
        bot = None
        for player in game_state["players"]:
            if player["name"] == bot_name:
                bot = player
                break
                
        if not bot or not bot["alive"]:
            return 0, 0
            
        # Simple strategy: move towards nearest food
        nearest_food = self.find_nearest_food(
            bot["circle"],
            game_state["food"]
        )
        
        if nearest_food:
            return self.calculate_direction(
                bot["circle"],
                nearest_food["circle"]
            )
            
        return 0, 0
        
    def find_nearest_food(self, position, food_list):
        """Find the nearest food item"""
        if not food_list:
            return None
            
        nearest = None
        min_distance = float('inf')
        
        for food in food_list:
            dist = self.calculate_distance(position, food["circle"])
            if dist < min_distance:
                min_distance = dist
                nearest = food
                
        return nearest
        
    def calculate_distance(self, pos1, pos2):
        """Calculate distance between two positions"""
        dx = pos1["x"] - pos2["x"]
        dy = pos1["y"] - pos2["y"]
        return math.sqrt(dx*dx + dy*dy)
        
    def calculate_direction(self, from_pos, to_pos):
        """Calculate direction vector to target"""
        dx = to_pos["x"] - from_pos["x"]
        dy = to_pos["y"] - from_pos["y"]
        length = math.sqrt(dx*dx + dy*dy)
        
        if length == 0:
            return 0, 0
            
        # Normalize the vector
        return dx/length, dy/length