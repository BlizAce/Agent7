"""
Test complete flow: LM Studio response → File parsing → File creation
"""
import os
import tempfile
import shutil
from file_operations import FileOperations
from database import Database


def test_actual_lm_studio_output():
    """Test with actual LM Studio output format from user's log."""
    
    # This is the EXACT format from the user's output
    lm_studio_response = """### Creating Necessary Files

Based on the project structure and requirements identified earlier, let's create the required files in the proper format.

**File: src/main.py**
```python
import pygame
from paddle import Paddle
from ball import Ball
from constants import SCREEN_WIDTH, SCREEN_HEIGHT, WHITE, BLACK

# Initialize Pygame
pygame.init()

# Set up the display
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Pong")

# Create paddles and ball
left_paddle = Paddle(10, 50, WHITE)
right_paddle = Paddle(SCREEN_WIDTH - 20, 50, WHITE)
ball = Ball(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2, WHITE)

# Game loop
running = True
clock = pygame.time.Clock()

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    # Update and draw
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
```

**File: src/paddle.py**
```python
import pygame

class Paddle:
    WIDTH = 10
    HEIGHT = 75
    
    def __init__(self, x, y, color):
        self.rect = pygame.Rect(x, y, self.WIDTH, self.HEIGHT)
        self.color = color
```

**File: src/ball.py**
```python
import pygame

class Ball:
    def __init__(self, x, y, color):
        self.rect = pygame.Rect(x, y, 10, 10)
        self.color = color
        self.speed_x = 3
        self.speed_y = 3
```

**File: src/constants.py**
```python
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
```

### Summary
These files form the basic structure of a Pong game."""
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix="test_pong_")
    temp_db = tempfile.mktemp(suffix=".db")
    
    try:
        print("="*60)
        print("Testing Complete Flow with Actual LM Studio Output")
        print("="*60)
        
        # Initialize
        db = Database(temp_db)
        file_ops = FileOperations(db)
        
        # Create a task
        task_id = db.create_task(
            project_id=1,
            title="Test Pong",
            description="Create Pong game",
            task_type="coding"
        )
        
        print(f"\n1. Created task: {task_id}")
        
        # Parse and execute
        print("\n2. Parsing LM Studio output...")
        operations = file_ops.parse_and_execute(
            lm_studio_response,
            temp_dir,
            task_id=task_id
        )
        
        print(f"\n3. Found {len(operations)} file operations:")
        for op in operations:
            status = "✅" if op['success'] else "❌"
            print(f"   {status} {op['filepath']}")
            if not op['success']:
                print(f"      Error: {op.get('error', 'Unknown')}")
        
        # Check files actually exist
        print("\n4. Verifying files on disk:")
        expected_files = [
            'src/main.py',
            'src/paddle.py',
            'src/ball.py',
            'src/constants.py'
        ]
        
        for filepath in expected_files:
            full_path = os.path.join(temp_dir, filepath)
            exists = os.path.exists(full_path)
            status = "✅" if exists else "❌"
            print(f"   {status} {filepath}")
            
            if exists:
                size = os.path.getsize(full_path)
                print(f"      Size: {size} bytes")
                
                # Show first few lines
                with open(full_path, 'r') as f:
                    first_line = f.readline().strip()
                    print(f"      First line: {first_line}")
        
        # Summary
        successful = len([op for op in operations if op['success']])
        print(f"\n5. Summary:")
        print(f"   Files parsed: {len(operations)}")
        print(f"   Files created successfully: {successful}")
        print(f"   Files expected: {len(expected_files)}")
        
        if successful == len(expected_files):
            print("\n✅ ALL TESTS PASSED!")
            print("   The complete flow works correctly!")
            return True
        else:
            print(f"\n❌ TEST FAILED!")
            print(f"   Expected {len(expected_files)} files, created {successful}")
            return False
            
    finally:
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
        if os.path.exists(temp_db):
            os.remove(temp_db)


if __name__ == '__main__':
    success = test_actual_lm_studio_output()
    exit(0 if success else 1)

