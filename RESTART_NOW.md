# 🚨 RESTART AGENT7 NOW! 🚨

## Critical Fix Applied

I've made the file output instructions **IMPOSSIBLE to miss**:

### What Was Added

```
⚠️⚠️⚠️ CRITICAL FOR CODING TASKS ⚠️⚠️⚠️
You MUST output files in this format:

File: filename.py
```python
complete file content here
```

DO NOT just say "update line X" - OUTPUT THE COMPLETE FILE!
Without File: blocks, your code changes will NOT be saved!
```

This is now shown **directly** in every coding task prompt!

---

## You MUST Restart

```cmd
# Close Agent7 if running
# Then restart:
launch_agent7.bat
```

**Why restart?** The new prompts are only loaded at startup!

---

## Then Try Task #9 Again

After restarting:

1. Go to http://localhost:5000
2. Select project: `C:\Repos\A7Pong`
3. Find Task #9 in the list
4. Click [▶️ Execute]

**This time it should**:
- ✅ Explore project
- ✅ Read files
- ✅ **OUTPUT File: main.py with fixes**
- ✅ Show "Modified: 🔄 main.py"
- ✅ Status: COMPLETED

---

## If It STILL Doesn't Work

Check your LM Studio settings:

### Model Requirements
- **Minimum**: 6-7B parameters coding model
- **Recommended**: DeepSeek Coder 6.7B, CodeLlama 13B+, or better
- **Not recommended**: General chat models, small models (<3B)

### Settings
```
Context Length: 4096+
Max Output Tokens: 2048+
Temperature: 0.3-0.5
Top P: 0.9
Stop Sequences: (check none interfere with ```)
```

### Alternative: Try Different Model

If current model doesn't work, try:
1. DeepSeek Coder 6.7B Instruct
2. CodeLlama 13B Instruct
3. Phind CodeLlama 34B
4. DeepSeek Coder 33B (if you have VRAM)

---

## Quick Test After Restart

```
Chat: "Create a test file called hello.py that prints Hello World"
```

**Expect**:
```
File: hello.py
```python
print("Hello World")
```

Created: ✅ hello.py
```

If this works, your Pong fix will work too!

---

## Status

- ✅ Code updated
- ✅ Prompts enhanced
- ✅ No errors
- ⚠️ **YOU MUST RESTART** to apply
- 🎯 Then execute task #9

---

**CLOSE AGENT7 AND RESTART NOW!** 🔄

