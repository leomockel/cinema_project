📽️ Leo Cinema Project

Python project to maintain a cinema database updated with new movies released, annotate the movies seen and data analysis on your list.

🚀 Features

🔍 Look for new release every month on allocine.fr, retrieval of IMDb IDs for each movies
⚡ Optimized scraping with multithreading
🗄️ PostgreSQL database integration
📊 Data Analysis on PowerBI (directly linked to the database)
🎬 Update your list of watched movies using a Streamlit app
🔐 Secure environment variable management using .env

🛠️ Tech Stack

Python 3.10+
Pandas
BeautifulSoup
SQLAlchemy
PostgreSQL
Jupyter Notebook
Streamlit

📦 Installation
1️⃣ Clone the repository
git clone git@github.com:your-username/leo-cinema.git
cd leo-cinema

2️⃣ Create a virtual environment
python -m venv venv
source venv/bin/activate   # Linux / Mac
venv\Scripts\activate      # Windows

3️⃣ Install dependencies
pip install -r requirements.txt

🔐 Environment Configuration

Create a .env file at the root of the project:
Put your DATABASE_URL

⚠️ Never commit your .env file to GitHub
Add .env to your .gitignore

▶️ Usage
Launch Jupyter Notebook
jupyter notebook

Launch a Streamlit app
streamlit run app.py


🧠 Future Improvements

Convert the notebooks in Streamlit apps
Add detailed description for each file

👤 Author

Lionel Mockel
📫 Contact: lionel.mockel@gmail.com
🌐 GitHub: @leomockel/cinema_project
