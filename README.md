# Zarqand Confectionery Job Application Bot

This is a Telegram bot built with `aiogram` that automates the initial screening process for job applicants at the "Zarqand" confectionery factory.

## Features

-   Collects applicant's name, age, and gender through a conversation.
-   Asks a qualifying question about their sense of responsibility.
-   Automatically filters candidates based on predefined criteria (age: 18-38, gender: female, responsible: yes).
-   Forwards qualified applications to an admin for review.
-   Provides the admin with "Accept" and "Reject" buttons for a quick decision.
-   Notifies the applicant of the admin's final decision.
-   Uses `Tortoise-ORM` to store application data in an SQLite database.

## Setup and Installation

### 1. Prerequisites

-   Python 3.7+

### 2. Clone the Repository

```bash
git clone <your-repo-url>
cd assignment_bot
```

### 3. Install Dependencies

Create a virtual environment (recommended) and install the required packages:

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

The bot requires a Telegram Bot Token and your admin chat ID.

1.  **Get a Bot Token:** Talk to [@BotFather](https://t.me/BotFather) on Telegram to create a new bot and get its token.
2.  **Get your Chat ID:** Talk to [@userinfobot](https://t.me/userinfobot) to find your numeric user ID.

3.  Create a `.env` file in the project root by copying the example file:

    ```bash
    cp .env.example .env
    ```

4.  Open the `.env` file and add your credentials:

    ```
    BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11
    ADMIN_ID=123456789
    ```

### 5. Run the Bot

Once the setup is complete, run the main script:

```bash
python main.py
```

The bot will start up, connect to the database, and begin listening for messages.
