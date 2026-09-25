# MATHutrice

MATHutrice is an educational tutor powered by an LLM designed to support first-year students in learning mathematical tools. 

To provide an optimal learning experience, the application offers a clear and intuitive interface where students can:
- Benefit from simple and structured navigation.
- Gain visibility on their progression (both globally and by specific subthemes).
- Quickly access practice sessions (e.g., via the "M'entraîner" button on module pages like Trigonometry).
- Track evaluated skills based on EPF/Moodle standards.

*Visual mockup for the home page:*
<img width="934" height="522" alt="image" src="https://github.com/user-attachments/assets/faa9c372-129c-4414-9160-f5f263b10f12" />

---

## Running Locally

Follow these steps to run the application on your machine.

### 1. Prerequisites
- **Python 3.10+**

### 2. Install Dependencies
Clone the repository and install the required Python packages:

```bash
pip install -r requirements.txt
```

### 3. Environment Variables
Create a .env file in the root directory. You will need to define your environment variables here (see the Development Sign-in section below for authentication variables).

### 4. Start the Application
Start the server locally using uvicorn:

```bash
uvicorn main:app --reload
```

### Verification
To ensure your local clone is running and configured correctly, please run through the checks outlined in docs/smoke-test.md.

## sDevelopment Sign-in (Forks & Non-Entra Environments)
For local development or when working on forks outside of the production Entra ID environment, you can use the development authentication mode.

### Configuration
Set the following variables in your .env file:
```
AUTH_MODE=dev (Note: This defaults to entra in production).

DEV_LOGIN_KEY: A custom secret key you choose to authenticate locally.

REDIRECT_URL: The URL to redirect to after a successful login (e.g., http://localhost:8000).

POST_LOGOUT_REDIRECT_URL: The URL to redirect to after logging out.

SESSION_SECRET: The secret string used to sign session cookies.
```

⚠️ SESSION_SECRET Caveat:
If SESSION_SECRET uses a predictable placeholder value (which is common in development), anyone can forge a session cookie and completely bypass the DEV_LOGIN_KEY requirement. Never use a placeholder for SESSION_SECRET in a public-facing or production environment.

### Scripted Sign-in (cURL)
If you are testing APIs or scripting interactions, you can authenticate via POST /dev/login and store the session cookie to maintain state across requests:

```bash
# 1. Log in and save the session cookie to 'cookie.txt'
curl -X POST http://localhost:8000/dev/login \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "key=YOUR_DEV_LOGIN_KEY" \
     -c cookie.txt

# 2. Use the saved cookie for subsequent authenticated requests
curl -X GET http://localhost:8000/api/some-protected-route \
     -b cookie.txt
```