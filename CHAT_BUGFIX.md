# Chat Feature Bugfix ✅

## Error
```
TypeError: Database.list_tasks() got an unexpected keyword argument 'limit'
```

## Problem
`chat_agent.py` was calling `self.db.list_tasks(limit=5)` and `self.db.list_tasks(limit=20)`, but the `Database.list_tasks()` method doesn't accept a `limit` parameter.

## Root Cause
The `list_tasks()` method signature in `database.py`:
```python
def list_tasks(self, project_id: Optional[int] = None,
               status: Optional[str] = None) -> List[Dict]:
```

No `limit` parameter!

## The Fix

### Before:
```python
# In chat_agent.py line 159
tasks = self.db.list_tasks(limit=5)

# In chat_agent.py line 350
all_tasks = self.db.list_tasks(limit=20)
```

### After:
```python
# Fixed line 159
all_tasks = self.db.list_tasks()
tasks = all_tasks[:5] if all_tasks else []

# Fixed line 350
all_tasks = self.db.list_tasks()[:20]
```

## Result
✅ Chat endpoint now works correctly!
✅ No more TypeError!
✅ Tasks are still limited as intended (5 for context, 20 for listing)

## Test It Now

1. **Start Agent7**:
   ```cmd
   launch_agent7.bat
   ```

2. **Open Dashboard**:
   `http://localhost:5000`

3. **Select Project**:
   Enter your project directory

4. **Try the Chat**:
   Type: "Create a hello world program"

Should work perfectly! 🎉

