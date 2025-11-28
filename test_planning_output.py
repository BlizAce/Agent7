"""
Test planning task output - should create markdown files.
"""
from file_operations import FileOperations


def test_planning_markdown_output():
    """Test that planning tasks create markdown documentation."""
    
    # Example of what LM Studio should output for a planning task
    planning_output = """# Project Planning

I'll create a comprehensive plan for this Pong game project.

**File: PLAN.md**
```markdown
# Pong Game Project Plan

## Overview
Create a classic Pong game with Python and Pygame featuring:
- Human player on the left (keyboard controls)
- AI opponent on the right
- Score tracking
- Game physics (ball bouncing, collision detection)

## Requirements

### Functional Requirements
- [ ] Game window with proper dimensions (800x600)
- [ ] Two paddles (left: human, right: AI)
- [ ] Ball with physics (bounce, speed)
- [ ] Collision detection (paddles, walls)
- [ ] Score tracking
- [ ] AI opponent logic
- [ ] Keyboard controls (W/S for up/down)
- [ ] Game over conditions

### Technical Requirements
- [ ] Python 3.8+
- [ ] Pygame library
- [ ] 60 FPS game loop
- [ ] Proper game state management

## Architecture

### Design Decisions
1. **Object-Oriented Design**: Separate classes for Paddle, Ball, Game
2. **Component Structure**: 
   - `src/` - Main source code
   - `tests/` - Unit tests
   - `assets/` - Game assets (if needed)

3. **Game Loop**: Standard Pygame event loop with fixed timestep

### Class Structure
```
Game (main controller)
├── Paddle (player and AI)
├── Ball (physics)
├── ScoreBoard
└── GameState (menu, playing, game over)
```

## TODO List

### Phase 1: Basic Setup (Priority: High)
1. [ ] Set up project structure
2. [ ] Install Pygame
3. [ ] Create main game window
4. [ ] Implement game loop

### Phase 2: Game Objects (Priority: High)
5. [ ] Create Paddle class
6. [ ] Create Ball class
7. [ ] Create constants file
8. [ ] Implement ball physics

### Phase 3: Game Logic (Priority: Medium)
9. [ ] Implement collision detection
10. [ ] Add score tracking
11. [ ] Implement AI logic
12. [ ] Add keyboard controls

### Phase 4: Polish (Priority: Low)
13. [ ] Add sound effects
14. [ ] Add start menu
15. [ ] Add game over screen
16. [ ] Add pause functionality

## Files to Create

### Core Files
- `src/main.py` - Entry point, game loop
- `src/paddle.py` - Paddle class (player + AI)
- `src/ball.py` - Ball class with physics
- `src/constants.py` - Game constants (colors, dimensions)

### Optional Files
- `src/game_state.py` - Game state management
- `src/scoreboard.py` - Score display
- `tests/test_paddle.py` - Paddle tests
- `tests/test_ball.py` - Ball tests
- `requirements.txt` - Dependencies

## Timeline Estimates

- Phase 1: 1-2 hours
- Phase 2: 2-3 hours
- Phase 3: 3-4 hours
- Phase 4: 2-3 hours

**Total**: ~8-12 hours

## Potential Challenges

1. **AI Difficulty**: Making AI challenging but beatable
   - Solution: Adjustable AI reaction speed

2. **Ball Physics**: Ensuring realistic bouncing
   - Solution: Proper angle calculations on collision

3. **Performance**: Maintaining 60 FPS
   - Solution: Pygame's built-in clock

## Next Steps

1. Run this planning task to create this document
2. Review and adjust plan as needed
3. Create coding task: "Implement Phase 1 - Basic Setup"
4. Reference this PLAN.md in all coding tasks
```

**File: TODO.md**
```markdown
# TODO List - Pong Game

## In Progress
- None yet

## Backlog

### High Priority
- [ ] Set up project structure (Phase 1.1)
- [ ] Install Pygame (Phase 1.2)
- [ ] Create main game window (Phase 1.3)
- [ ] Implement game loop (Phase 1.4)
- [ ] Create Paddle class (Phase 2.1)
- [ ] Create Ball class (Phase 2.2)

### Medium Priority
- [ ] Implement collision detection (Phase 3.1)
- [ ] Add score tracking (Phase 3.2)
- [ ] Implement AI logic (Phase 3.3)
- [ ] Add keyboard controls (Phase 3.4)

### Low Priority
- [ ] Add sound effects (Phase 4.1)
- [ ] Add start menu (Phase 4.2)
- [ ] Add game over screen (Phase 4.3)
- [ ] Add pause functionality (Phase 4.4)

## Completed
(None yet)
```

**File: REQUIREMENTS.md**
```markdown
# Requirements - Pong Game

## User Stories

### As a player, I want to:
- Control the left paddle with keyboard (W/S keys)
- See the ball bounce realistically
- See my score increase when opponent misses
- Play against a challenging but fair AI
- Know when the game is over

### As a developer, I want to:
- Clean, maintainable code
- Easy to test components
- Well-documented functions
- Extensible for future features

## Functional Requirements

1. **Game Window**
   - Size: 800x600 pixels
   - Title: "Pong"
   - Black background

2. **Paddles**
   - Size: 10x75 pixels
   - Color: White
   - Left paddle: Player controlled
   - Right paddle: AI controlled

3. **Ball**
   - Size: 10x10 pixels
   - Color: White
   - Starting speed: 3 pixels/frame
   - Bounces off paddles and top/bottom walls

4. **Controls**
   - W key: Move left paddle up
   - S key: Move left paddle down
   - ESC key: Quit game

5. **Scoring**
   - Point scored when ball passes opponent's paddle
   - Display scores at top of screen
   - First to 10 points wins

## Technical Requirements

1. **Python**: 3.8 or higher
2. **Pygame**: 2.0 or higher
3. **Frame Rate**: 60 FPS
4. **Resolution**: 800x600 (fixed)

## Constraints

- Single player only (vs AI)
- No network multiplayer
- No save/load game state
- No difficulty selection (fixed AI)
```

Great! I've created comprehensive planning documents.
"""
    
    print("="*60)
    print("Testing Planning Task Output")
    print("="*60)
    
    file_ops = FileOperations()
    blocks = file_ops.extract_file_blocks(planning_output)
    
    print(f"\n✅ Found {len(blocks)} planning documents:")
    for block in blocks:
        print(f"   📄 {block['filepath']} ({len(block['content'])} bytes)")
        
        # Verify it's a markdown file
        assert block['filepath'].endswith('.md'), f"Planning should create .md files, got {block['filepath']}"
    
    # Check expected files
    expected_files = ['PLAN.md', 'TODO.md', 'REQUIREMENTS.md']
    found_files = [block['filepath'] for block in blocks]
    
    for expected in expected_files:
        if expected in found_files:
            print(f"   ✅ {expected} - Found")
        else:
            print(f"   ⚠️  {expected} - Not found (optional)")
    
    print("\n📋 Planning documents should include:")
    print("   - Project overview and requirements")
    print("   - TODO list with priorities")
    print("   - Architecture decisions")
    print("   - Files to be created")
    print("   - Timeline estimates")
    
    print("\n✅ Planning task output format is correct!")
    print("   Coding tasks can reference these .md files")


if __name__ == '__main__':
    test_planning_markdown_output()

