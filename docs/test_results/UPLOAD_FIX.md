# File Upload Fix - Troubleshooting Guide

## Issues Fixed

1. **JavaScript File Location**: The `script.js` file was in `frontend/` but the template expected it in `static/`. Fixed by copying to `static/`.

2. **DOM Element Access**: Script was trying to access DOM elements before they were loaded. Fixed by initializing elements in `DOMContentLoaded` event.

3. **Error Handling**: Added better error handling and console logging for debugging.

4. **CORS Support**: Added CORS support for API endpoints.

## How to Test

1. **Install Dependencies** (if not already installed):
   ```bash
   pip install flask-cors
   ```
   Or install all requirements:
   ```bash
   pip install -r requirements_agentic.txt
   ```

2. **Start the Server**:
   ```bash
   python app.py
   ```

3. **Open Browser**:
   - Navigate to: `http://localhost:5000/labeling`
   - Open browser console (F12) to see any errors

4. **Test Upload**:
   - Select a file (PDF, image, or audio)
   - Click "Process File"
   - Check console for any errors

## Common Issues & Solutions

### Issue: "Required DOM elements not found"
**Solution**: Make sure you're accessing `/labeling` route, not `/` or `/frontend/index.html`

### Issue: "Failed to fetch" or CORS errors
**Solution**: 
- Install flask-cors: `pip install flask-cors`
- Or the app will use manual CORS headers as fallback

### Issue: "No file provided" error
**Solution**: 
- Check browser console for JavaScript errors
- Make sure file input is working (try clicking the drop zone)
- Check that form submission is not being prevented

### Issue: Rate limit errors
**Solution**: 
- Default is 10 requests per minute
- Wait 60 seconds or restart the server
- Can be configured in `app.py` or via environment variables

## Debugging Steps

1. **Check Browser Console**:
   - Open DevTools (F12)
   - Go to Console tab
   - Look for JavaScript errors

2. **Check Network Tab**:
   - Open DevTools (F12)
   - Go to Network tab
   - Try uploading a file
   - Check the `/api/upload` request:
     - Status code (should be 200 or 202)
     - Response body
     - Request payload

3. **Check Server Logs**:
   - Look at terminal where `app.py` is running
   - Check for error messages
   - Verify API keys are configured

4. **Verify File Types**:
   - Supported: PDF, TXT, DOCX, images (JPG, PNG, etc.), audio (MP3, WAV, etc.)
   - Check file extension is in allowed list

## Testing Checklist

- [ ] Server starts without errors
- [ ] Can access `/labeling` page
- [ ] JavaScript console shows no errors
- [ ] File input works (can select file)
- [ ] Drag & drop works
- [ ] Form submission works
- [ ] Upload request appears in Network tab
- [ ] Server logs show upload attempt
- [ ] Response is received (success or error)

## Still Having Issues?

1. Check that `static/script.js` exists and has content
2. Verify Flask is serving static files correctly
3. Check browser console for specific error messages
4. Verify API keys are set in environment or config.py
5. Check server logs for backend errors



