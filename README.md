# MedScope: AI-Powered Medical Information API

MedScope is a Python-based backend service built with FastAPI. It provides a suite of tools for medical information, including ML-powered drug risk prediction, a drug alternatives finder, and an intelligent chatbot powered by Google's Gemini AI. User management and data storage are handled by Firebase.


## Data Sources

The machine learning models were trained on data derived from the following public datasets. The processing and training steps can be reviewed in the `notebooks/` directory.

* **FDA Adverse Event Reporting System (FAERS)**:
    * [FAERS on Kaggle (2020 Data)](https://www.kaggle.com/datasets/stpeteishii/faers2020/data)
    * [FDA FAERS Public Dashboard](https://fis.fda.gov/extensions/FPD-QDE-FAERS/FPD-QDE-FAERS.html)
* **Medicine Usage and Substitutes**:
    * [250k+ Medicines on Kaggle](https://www.kaggle.com/datasets/shudhanshusingh/250k-medicines-usage-side-effects-and-substitutes)

## Core Features

* **ML Side Effect Prediction**: Utilizes pre-trained `scikit-learn` models to predict potential drug risk profiles and side effects based on a user's demographic and drug details.
* **Drug Alternatives Engine**:
    * Finds alternative medications for a given indication, with the ability to filter out drugs that have specific side effects.
    * Searches for drugs or indications to find related medications from a JSON-based database.
* **AI Medical Assistant ("MediAware Bot")**:
    * A conversational chatbot endpoint (`/chat`) that uses Google's Generative AI (Gemini).
    * Intelligently determines when to call internal tools (like `predict_side_effects` or `find_alternatives`) to fetch data.
    * Formats the raw data from its tools into a helpful, conversational, and HTML-formatted response.
* **User Authentication & Database**:
    * Secure user creation (with email verification) and login using Firebase Authentication.
    * Session management using HTTP-only cookies.
    * Saves user data (e.g., search history) to a Cloud Firestore database.

## Tech Stack

The project relies on the following key technologies and libraries:

* **Backend**: FastAPI & Uvicorn
* **Machine Learning**: Scikit-learn, Pandas, Joblib
* **Generative AI**: `google-generativeai` (Gemini)
* **Database & Auth**: `firebase-admin` (Firebase Authentication & Firestore)
* **Templating**: Jinja2
* **Data Validation**: Pydantic
* **Configuration**: `python-dotenv`
* **HTTP Client**: `requests`

## Project Structure
```
/
├── main.py                 # Main FastAPI app initialization and routing
├── requirements.txt        # Python dependencies
├── .env                    # (Required, not included) For API keys
├── serviceAccountKey.json  # (Required, not included) Firebase admin credentials
|
├── models/                 # (Required, not included) ML models and data
│   ├── risk_model_3.joblib
│   ├── reactions_model_3.joblib
│   ├── risk_binarizer_3.joblib
│   ├── reactions_binarizer_3.joblib
│   └── alternative_medicine.json
|
├── routes/
│   ├── auth.py             # User authentication routes (login, signup)
│   ├── user.py             # User profile routes
│   ├── ml_models.py        # API endpoints for predictions and alternatives
│   └── chat.py             # API endpoint for the AI chatbot
|
├── schemas/
│   ├── model.py            # Pydantic models for API request bodies
│   └── user.py             # Pydantic models for user data
|
├── service/
│   └── firebase_service.py # Logic for Firebase auth and database
|
├── static/                 # CSS, JS, and JSON files for frontend
│   ├── css/
│   │   ├── alternativesStyle.css
│   │   ├── chatStyle.css
│   │   ├── homeStyle.css
│   │   ├── loginStyle.css
│   │   └── signupStyle.css
│   └── js/
│       ├── active_chemicals.json
│       ├── alternatives.js
│       ├── alternatives_drugs.json
│       ├── alternatives_indications.json
│       ├── chat.js
│       ├── countries.json
│       ├── home.js
│       ├── indications.json
│       └── routes.json
|
├── templates/              # Jinja2 HTML templates
│   ├── 404.html
│   ├── alternatives.html
│   ├── chat.html
│   ├── home.html
│   ├── login.html
│   ├── profile.html
│   └── signup.html
|
├── notebooks/              # Jupyter notebooks for data processing and model training
│   ├── Alternate_Medicine.ipynb
│   ├── Data-to-Json.ipynb
│   ├── Data_Cleaning_faers.ipynb
│   ├── Data_Visualization.ipynb
|   ├── Model_Training.ipynb
│   ├── Model_Training_2.ipynb
│   └── Model_Training_3.ipynb
|
├── .gitattributes
└── .gitignore
```

## Setup and Installation

1.  **Clone the Repository**
    ```sh
    git clone <your-repository-url>
    cd medscope
    ```

2.  **Create a Virtual Environment**
    ```sh
    python -m venv venv
    source venv/bin/activate  # On Windows: .\venv\Scripts\activate
    ```

3.  **Install Dependencies**
    Install all required Python packages from `requirements.txt`:
    ```sh
    pip install -r requirements.txt
    ```

## Configuration

This project requires external API keys, credentials, and model files to run.

1.  **Environment Variables**
    Create a `.env` file in the root directory and add the following keys:
    ```ini
    # For Google Generative AI (chat.py)
    GEMINI_API_KEY="YOUR_GEMINI_API_KEY"

    # For Firebase Authentication (firebase_service.py)
    FIREBASE_API_KEY="YOUR_FIREBASE_WEB_API_KEY"
    GOOGLE_CLIENT_ID="YOUR_GOOGLE_CLIENT_ID"
    ```

2.  **Firebase Service Account**
    * Download your `serviceAccountKey.json` file from the Firebase Admin console.
    * Place it in the root directory or update the path in `service/firebase_service.py`:
        ```python
        # In service/firebase_service.py
        cred = credentials.Certificate("path/to/your/serviceAccountKey.json")
        ```

3.  **Machine Learning Models**
    This project requires pre-trained models and a data file. As specified in `routes/ml_models.py`, create a `models/` directory and place the following files inside it:
    * `risk_model_3.joblib`
    * `reactions_model_3.joblib`
    * `risk_binarizer_3.joblib`
    * `reactions_binarizer_3.joblib`
    * `alternative_medicine.json`

## How to Run

Once all dependencies are installed and configuration files are in place, run the application using Uvicorn:

```sh
# The app object is in main.py
uvicorn main:app --reload
