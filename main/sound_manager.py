import pygame
import os
import sys

# Get the project root directory for asset paths
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)

class SoundManager:
    """Handles all sound effects for the game."""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SoundManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize sound manager (singleton pattern)."""
        if SoundManager._initialized:
            return
        
        try:
            # Initialize pygame mixer
            pygame.mixer.init()
            SoundManager._initialized = True
            # Global mute flag
            self.muted = False
            
            # Load sound files
            self.button_sound_path = os.path.join(PROJECT_ROOT, "assets", "buttonclicksound.mp3")
            self.pop_sound_path = os.path.join(PROJECT_ROOT, "assets", "bubblepopsound.mp3")
            
            # Verify sound files exist
            self.button_sound = None
            self.pop_sound = None
            
            if os.path.exists(self.button_sound_path):
                try:
                    self.button_sound = pygame.mixer.Sound(self.button_sound_path)
                    self.button_sound.set_volume(0.7)
                except Exception as e:
                    print(f"Warning: Could not load button sound: {e}")
            else:
                print(f"Warning: Button sound file not found at {self.button_sound_path}")
            
            if os.path.exists(self.pop_sound_path):
                try:
                    self.pop_sound = pygame.mixer.Sound(self.pop_sound_path)
                    self.pop_sound.set_volume(0.7)
                except Exception as e:
                    print(f"Warning: Could not load pop sound: {e}")
            else:
                print(f"Warning: Pop sound file not found at {self.pop_sound_path}")
                
        except Exception as e:
            print(f"Warning: Failed to initialize sound manager: {e}")
            SoundManager._initialized = True  # Mark as initialized to avoid repeated attempts
    
    def set_muted(self, muted: bool):
        """Enable or disable all sound effects globally."""
        self.muted = bool(muted)

    def toggle_mute(self) -> bool:
        """Toggle mute state and return the new state."""
        self.muted = not getattr(self, "muted", False)
        return self.muted

    def play_button_sound(self):
        """Play button click sound effect (always plays; mute icon only controls burst sounds)."""
        try:
            if self.button_sound:
                self.button_sound.play()
        except Exception as e:
            print(f"Error playing button sound: {e}")
    
    def play_pop_sound(self):
        """Play bubble pop sound effect (respects mute)."""
        if getattr(self, "muted", False):
            return
        try:
            if self.pop_sound:
                self.pop_sound.play()
        except Exception as e:
            print(f"Error playing pop sound: {e}")


# Create a global singleton instance
sound_manager = SoundManager()
