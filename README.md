# PiggyFinance
MajorAssignment_DSA

# Personal Expense Management

This is a web app project for personal expense management using Flask, supporting statistics, expense categorization, and AI Q&A (Gemini API integration).

## Main Features
- Add, delete, and view expenses
- Statistics by week, month, year, and category
- Ask AI about your spending (Gemini API integration)
- Simple and user-friendly interface

## Technologies Used
- Python 3.10+
- Flask >= 3.0.3
- Gunicorn (production server)c
- Google Generative AI (Gemini)
- Railway (cloud deployment)

## Local Setup & Run
```bash
# Clone the repo
https://github.com/DATKINGKHUNG/demo.git
cd demo

# Create a virtual environment
python3 -m venv demo-env
source demo-env/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the app
python app.py
# or use gunicorn
# gunicorn app:app
```
Visit: https://demo-production-4164.up.railway.app/expenses

## Deploy on Railway
1. Push your code to GitHub
2. Connect Railway to your repo, Railway will auto build and deploy
3. Railway uses `nixpacks.toml` to run: `gunicorn app:app`
4. Your app will have a public URL after successful deployment

## Project Structure
```
├── app.py               # Main Flask app code
├── requirements.txt     # Python dependencies
├── nixpacks.toml        # Railway config
├── expense_data.json    # Local expense data
├── templates/           # HTML templates
└── README.md            # Documentation
```

## Notes
- To use Gemini AI, you need a valid API key (edit in app.py or use environment variable)
- Data is stored locally as JSON; you can extend to use a database if needed

## Author
- DATKINGKHUNG
- Personal project, all contributions are welcome! 

