# 🐛 Chatbot Debugging Guide

## ✅ Latest Fix Deployed

**Commit:** `654dbd1` - Frontend debugging and error handling improvements

---

## 🔍 How to Debug Chatbot Issues

### Step 1: Open Browser Console

1. Open your website (https://bloodis-life.online)
2. Press **F12** or **Ctrl+Shift+I** to open Developer Tools
3. Click on **Console** tab
4. Clear console (click 🚫 icon)

---

### Step 2: Check Initialization Messages

When page loads, you should see:

```
🤖 ========== CHATBOT INITIALIZATION ==========
✅ AOS initialized
🟡 Testing chatbot API connectivity...
✅ Chatbot API is working correctly
✅ API responded with: Valid response
🤖 Chatbot widget loaded successfully
🤖 ========== CHATBOT INITIALIZATION COMPLETE ==========
```

**If you see errors:**
- 🔴 `Chatbot API test failed` → Backend API issue
- 🔴 `Chatbot API returned status: 404` → URL not configured
- 🔴 `Chatbot API returned status: 500` → Server error

---

### Step 3: Test Sending a Message

1. Click the chatbot icon (bottom-right)
2. Type: "Hello"
3. Press Enter
4. Watch the console

**Expected Console Output:**

```
🟢 ========== CHATBOT MESSAGE START ==========
🟢 User message: Hello
🟢 Sending POST request to: /api/requests/chatbot/
🟢 Request payload: {message: "Hello", session_id: "xyz..."}
🟢 Response status: 200
🟢 Response OK: true
🟢 Response data: {success: true, response: "Hello! I'm your...", ...}
✅ Chatbot response received successfully
✅ Confidence: high
✅ Response length: 156
✅ Updating suggestions: [...]
🟢 ========== CHATBOT MESSAGE END ==========
```

---

## 🚨 Common Issues & Solutions

### Issue 1: Chatbot Icon Not Visible

**Check:**
```javascript
// Run in console:
document.getElementById('chat-widget')
```

**Expected:** Should return the DOM element

**If null:**
- Widget not included in page
- Check if `{% include 'partials/chat_widget.html' %}` is in base.html

---

### Issue 2: Chat Window Doesn't Open

**Check:**
```javascript
// Run in console after clicking:
document.getElementById('chat-window').style.display
```

**Expected:** Should be "flex" when open

**If still "none":**
- JavaScript error preventing toggle
- Check console for errors

---

### Issue 3: Message Sends But No Response

**Check Console for:**

**Scenario A - API Error:**
```
🔴 Server returned error status: 500
🔴 Error response: {...}
```
**Solution:** Backend error, check Render logs

**Scenario B - Network Error:**
```
🔴 ========== CHATBOT ERROR ==========
🔴 Error type: TypeError
🔴 Error message: Failed to fetch
```
**Solution:** 
- Server not running
- Wrong API URL
- CORS issue

**Scenario C - Bad Response:**
```
🔴 Response missing success flag or response text
🔴 Data received: {success: false, error: "..."}
```
**Solution:** Backend returned error, check logs

---

### Issue 4: Response Shows But Not Formatted

**Problem:** Response shows as raw text with `**bold**` and `•` bullets

**Check:**
```javascript
// Run in console:
typeof formatMessage
```

**Expected:** "function"

**If undefined:**
- formatMessage() function not loaded
- Script order issue

---

### Issue 5: API Returns 404

**Problem:**
```
🔴 Chatbot API returned status: 404
```

**Solution:**

Check URL configuration in [urls.py](file:///c:/Users/mypc0/OneDrive/Desktop/New%20folder/blood-donation-help/blood_requests_app/urls.py):

```python
path("chatbot/", views_api.ChatbotView.as_view(), name='chatbot'),
```

Should be at line ~91.

---

### Issue 6: CSRF Token Error (403)

**Problem:**
```
🔴 Server returned error status: 403
```

**Solution:**

Check if CSRF token is being sent:
```javascript
// Run in console:
getCSRFToken()
```

**Expected:** Long string like "abc123..."

**If empty string:**
- CSRF cookie not set
- Check Django settings

---

## 🧪 Quick Test Commands

Run these in browser console to test:

### Test 1: Check Widget Exists
```javascript
console.log('Widget:', document.getElementById('chat-widget'));
console.log('Window:', document.getElementById('chat-window'));
console.log('Input:', document.getElementById('chat-input'));
console.log('Messages:', document.getElementById('chat-messages'));
```

**All should show DOM elements, not null**

---

### Test 2: Manually Send Message
```javascript
// Test with hardcoded message
fetch('/api/requests/chatbot/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': getCSRFToken()
    },
    body: JSON.stringify({
        message: 'Hello',
        session_id: 'test-123'
    })
})
.then(r => r.json())
.then(d => console.log('Response:', d))
.catch(e => console.error('Error:', e));
```

---

### Test 3: Check Functions Exist
```javascript
console.log('toggleChatWidget:', typeof toggleChatWidget);
console.log('sendChatMessage:', typeof sendChatMessage);
console.log('addMessageToChat:', typeof addMessageToChat);
console.log('getCSRFToken:', typeof getCSRFToken);
console.log('formatMessage:', typeof formatMessage);
```

**All should show "function"**

---

## 📊 What to Report

If chatbot still doesn't work, please provide:

### 1. Console Output
Screenshot of entire console from page load to message send

### 2. Network Tab
1. Open Network tab in DevTools
2. Send a message
3. Find the `chatbot` request
4. Click on it
5. Screenshot:
   - **Headers** tab (showing Request URL, Status Code)
   - **Response** tab (showing what server returned)

### 3. Specific Questions
- Does chatbot icon appear? ✅/❌
- Can you click and open it? ✅/❌
- Can you type a message? ✅/❌
- Does typing indicator show? ✅/❌
- Do you see ANY response? ✅/❌
- What error message do you see? (exact text)

---

## 🎯 Expected Behavior After Fix

### Page Load:
1. ✅ Chatbot icon visible (bottom-right, red circle)
2. ✅ Console shows "CHATBOT INITIALIZATION COMPLETE"
3. ✅ Console shows "Chatbot API is working correctly"

### Click Icon:
1. ✅ Chat window opens with animation
2. ✅ Welcome message visible
3. ✅ Input field focused

### Send Message:
1. ✅ User message appears (blue, right side)
2. ✅ Typing indicator shows (3 dots)
3. ✅ Bot response appears (white, left side)
4. ✅ Suggestions update below input

### Error Cases:
1. ✅ Network error → Shows friendly message + fallback
2. ✅ Server error (500) → Shows error code + fallback  
3. ✅ Bad response → Shows "could not process" message

---

## 🔧 Files Modified

1. ✅ [chat_widget.html](file:///c:/Users/mypc0/OneDrive/Desktop/New%20folder/blood-donation-help/templates/partials/chat_widget.html)
   - Enhanced `sendChatMessage()` with detailed logging
   - Added `testChatbotAPI()` for startup testing
   - Better error handling and user messages
   - Validates every step of the process

---

## 📝 Next Steps

1. **Wait for deployment** (3-5 minutes)
2. **Hard refresh** browser (Ctrl+Shift+R)
3. **Open console** (F12)
4. **Test chatbot**
5. **Share console output** if still not working

The new logging will tell us EXACTLY where the problem is! 🎯
