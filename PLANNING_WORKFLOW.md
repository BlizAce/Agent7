# Planning Workflow - Documentation-First Development

## Overview

Agent7 now supports a **documentation-first workflow** where:
1. **Planning tasks** create markdown documentation files
2. **Coding tasks** reference these documents to implement features
3. **Testing tasks** verify implementation against requirements

## How It Works

### Step 1: Create Planning Task

**Task Type**: `planning`

**Description**: 
```
Plan the Pong game project with detailed requirements and architecture
```

**What It Creates**:
- `PLAN.md` - Overall project plan with architecture
- `TODO.md` - Task list with priorities
- `REQUIREMENTS.md` - Detailed requirements and user stories

**Example Output**:

```markdown
File: PLAN.md
# Pong Game Project Plan

## Overview
[Project description]

## Requirements
- [ ] Requirement 1
- [ ] Requirement 2

## Architecture
[Design decisions]

## TODO List
1. [ ] Phase 1: Setup
2. [ ] Phase 2: Core features
3. [ ] Phase 3: Polish

## Files to Create
- src/main.py - Game entry point
- src/paddle.py - Paddle class
- src/ball.py - Ball physics

## Timeline
Phase 1: 2 hours
Phase 2: 4 hours
```

### Step 2: Create Coding Tasks

**Task Type**: `coding`

**Description**: 
```
Implement Phase 1 from PLAN.md - Set up game window and basic structure
```

**What LM Studio Does**:
1. Uses `TOOL: read_file(filepath="PLAN.md")` to read the plan
2. Understands what needs to be implemented
3. Creates the code files specified in the plan
4. Follows the architecture decisions

**Example**:
```
🔧 Executing 1 tool(s)...
📄 PLAN.md (2048 lines):
[Reads the plan]

📝 Creating files based on Phase 1...
File: src/main.py
[Implements according to plan]
```

### Step 3: Update Documentation

As you complete phases:
1. Check off items in `TODO.md`
2. Update `PLAN.md` with learnings
3. Add notes to `REQUIREMENTS.md` if needed

## Planning Task Prompts

### Good Planning Prompts

✅ **Comprehensive**:
```
Plan a Pong game with detailed architecture, requirements, 
and implementation phases
```

✅ **Specific**:
```
Create a technical plan for integrating authentication into 
the existing web app, including security considerations
```

✅ **Problem-focused**:
```
Plan how to refactor the monolithic app into microservices,
including migration strategy and timeline
```

### Bad Planning Prompts

❌ **Too vague**:
```
Plan something
```

❌ **Already coded**:
```
Create the Pong game (use coding task instead!)
```

❌ **No actionable output**:
```
Think about the project (be more specific!)
```

## Coding Task Prompts (Referencing Plans)

### Good Coding Prompts

✅ **References plan**:
```
Implement Phase 1 from PLAN.md - Game window setup
```

✅ **Specific phase**:
```
Create the Paddle class as specified in PLAN.md section 2.1
```

✅ **Builds incrementally**:
```
Implement the next 3 TODO items from TODO.md
```

### Bad Coding Prompts

❌ **No reference**:
```
Create some code (what code? check plan first!)
```

❌ **Too broad**:
```
Implement everything (do it phase by phase!)
```

## Example Workflow

### Complete Project Flow

**1. Planning (5 minutes)**
```
Task: Plan a TODO list web app
Type: planning
→ Creates: PLAN.md, TODO.md, REQUIREMENTS.md
```

**2. Phase 1 - Setup (10 minutes)**
```
Task: Implement Phase 1 from PLAN.md - Project setup
Type: coding
→ Creates: setup.py, requirements.txt, README.md
→ Uses: TOOL: read_file(filepath="PLAN.md")
```

**3. Phase 2 - Backend (20 minutes)**
```
Task: Implement Phase 2 from PLAN.md - Backend API
Type: coding
→ Creates: src/api.py, src/models.py, src/database.py
→ Uses: TOOL: read_file(filepath="PLAN.md")
```

**4. Phase 3 - Frontend (20 minutes)**
```
Task: Implement Phase 3 from PLAN.md - Frontend
Type: coding  
→ Creates: static/index.html, static/app.js, static/style.css
→ Uses: TOOL: read_file(filepath="PLAN.md")
```

**5. Testing (10 minutes)**
```
Task: Create tests as specified in PLAN.md
Type: testing
→ Creates: tests/test_api.py, tests/test_models.py
→ Uses: TOOL: read_file(filepath="PLAN.md")
```

**Total**: ~65 minutes for complete project with documentation!

## Benefits

### For Solo Developers
- 📋 Clear roadmap before coding
- ✅ Track progress with TODO.md
- 📝 Document decisions for future reference
- 🎯 Focus on one phase at a time

### For Teams
- 📄 Shared understanding via PLAN.md
- ✅ Distribute TODO items to team members
- 📋 Requirements serve as acceptance criteria
- 🔄 Update docs as project evolves

### For AI Agents
- 🤖 Read PLAN.md to understand context
- ✅ Check TODO.md for what to implement
- 📝 Follow architecture from REQUIREMENTS.md
- 🎯 Implement exactly what's specified

## Document Templates

### PLAN.md Template
```markdown
# [Project Name] Plan

## Overview
[1-2 paragraph description]

## Requirements
- [ ] Core requirement 1
- [ ] Core requirement 2

## Architecture
### Technology Stack
- Language: [Python/JavaScript/etc]
- Framework: [Flask/React/etc]
- Database: [SQLite/PostgreSQL/etc]

### Design Patterns
[Patterns to use]

## TODO List
### Phase 1: [Name]
1. [ ] Task 1
2. [ ] Task 2

### Phase 2: [Name]
3. [ ] Task 3
4. [ ] Task 4

## Files to Create
- `path/file.ext` - Purpose

## Timeline
- Phase 1: X hours
- Phase 2: Y hours
- **Total**: Z hours
```

### TODO.md Template
```markdown
# TODO - [Project Name]

## In Progress
- [ ] Current task

## High Priority
- [ ] Critical task 1
- [ ] Critical task 2

## Medium Priority
- [ ] Important task 1

## Low Priority
- [ ] Nice-to-have 1

## Completed
- [x] Setup project ✅
- [x] Create plan ✅
```

### REQUIREMENTS.md Template
```markdown
# Requirements - [Project Name]

## Functional Requirements
1. **Feature 1**
   - User can do X
   - System does Y
   - Result is Z

## Non-Functional Requirements
- Performance: [Requirements]
- Security: [Requirements]
- Scalability: [Requirements]

## Constraints
- Must use [Technology]
- Cannot exceed [Limit]

## User Stories
As a [role], I want [feature] so that [benefit]
```

## Tips

### Planning Phase
1. **Be Comprehensive**: Include everything you can think of
2. **Prioritize**: Mark what's essential vs nice-to-have
3. **Estimate**: Rough time estimates help with planning
4. **Decide Early**: Make architecture decisions upfront

### Coding Phase
1. **Read Plan First**: Always use `TOOL: read_file("PLAN.md")`
2. **One Phase at a Time**: Don't try to implement everything
3. **Update TODO**: Check off items as you complete them
4. **Follow Architecture**: Stick to decisions in PLAN.md

### Maintenance
1. **Keep Updated**: Adjust plans as you learn
2. **Document Changes**: Note why decisions changed
3. **Version Plans**: Consider `PLAN_v2.md` for major changes

## Status

- **Version**: 2.2.0
- **Feature**: Planning workflow
- **Status**: ✅ Implemented and tested
- **Usage**: Create tasks with type `planning`

---

**Summary**: Planning tasks create markdown documentation that coding tasks reference, enabling documentation-first development with AI agents.

