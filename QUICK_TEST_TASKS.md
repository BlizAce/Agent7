# Quick Test Tasks 🧪

## Agent7 is Working - Let's Test Your Model

Agent7 code is perfect (iteration 4 works!). The issue is the LM Studio model not outputting files.

---

## Test 1: Simple File Creation

**Via Chat**:
```
Create a file called hello.py with this code:
print("Hello World")

Format:
File: hello.py
```python
print("Hello World")
```
```

**Expected**: File created  
**If fails**: Model can't do basic file output

---

## Test 2: Read and Modify

**Via Chat**:
```
Read main.py. Then output the COMPLETE modified main.py where you change line 22 from:
player_paddle = Paddle(BLACK, paddle_width, paddle_height)

To:
player_paddle = Paddle(20, height // 2, paddle_width, paddle_height, 5)

Output format:
File: main.py
```python
[complete file]
```
```

**Expected**: File modified  
**If fails**: Model can't do file modifications

---

## Test 3: Check Your Model

```cmd
curl http://localhost:1234/v1/models
```

**Look for**:
- Model name
- Parameter count (6B, 7B, 13B, etc.)

**Good models**:
- DeepSeek-Coder-*-Instruct
- CodeLlama-*-Instruct
- Phind-CodeLlama-*

**Bad models**:
- General chat models
- Models < 6B
- Non-coding models

---

## Check Settings

In LM Studio, check:
- ✅ Context: 4096+
- ✅ Max Tokens: 3000+
- ✅ Temperature: 0.3-0.5
- ✅ Model type: Coding/Instruct

---

## If All Tests Fail

**Try**:
1. Load DeepSeek Coder 6.7B Instruct
2. Set Max Tokens to 4000
3. Set Temperature to 0.4
4. Try test 1 again

**DeepSeek Coder 6.7B** is known to work well with Agent7!

---

Let me know what happens with these tests! 🔬

