
# Flight Detail Scraping and Alert Project

This project scrapes flight details and sends alerts based on specific criteria. It uses **Celery** for task scheduling and **Uvicorn** to run the FastAPI server.

## Project Setup

1. **Clone the repository:**

   \`\`\`bash
   git clone <repository-url>
   cd flight-detail-scraping-alert
   \`\`\`

2. **Set up a virtual environment:**

   \`\`\`bash
   python -m venv env
   \`\`\`

3. **Activate the virtual environment:**

   - For Linux/macOS:

     \`\`\`bash
     source env/bin/activate
     \`\`\`

   - For Windows:

     \`\`\`bash
     .\env\Scripts\activate
     \`\`\`

4. **Install dependencies:**

   \`\`\`bash
   pip install -r requirements.txt
   \`\`\`

## Database Setup

1. **Create a PostgreSQL database** (or any other database you're using):

   \`\`\`sql
   CREATE DATABASE flight_alert;
   \`\`\`

2. **Run database migrations:**

   Apply the database migrations:

   \`\`\`bash
   alembic upgrade head
   \`\`\`

## Running the Application

1. **Run Celery Worker:**

   \`\`\`bash
   celery -A app.routes worker --loglevel=info
   \`\`\`

2. **Run the FastAPI server:**

   \`\`\`bash
   uvicorn app.routes:app --reload
   \`\`\`

## Environment Variables

Before running the application, update the environment variables.

1. **Copy .env.example to .env and add the values there:**

   \`\`\`bash
   cp .env.example .env
   \`\`\`


That's it! You're now ready to run the project. If you have any questions, feel free to reach out.