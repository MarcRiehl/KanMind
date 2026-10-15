# KanMind – Task Management API

![KanMind Logo](assets/icons/logo_icon.svg)

## About the Project

KanMind is a task management backend built with **Python, Django and Django REST Framework (DRF)**. It provides a REST API for managing boards, tasks and comments, as well as user authentication and authorization.

### Features

- User registration, login and logout with token authentication
- Create, retrieve, update and delete boards
- Manage board members and permissions
- Create, retrieve, update and delete tasks
- Assign users as assignees and reviewers
- Retrieve tasks assigned to the current user or assigned for review
- Create, retrieve and delete comments on tasks
- Validate user email addresses
- Restrict API access based on authentication, board membership and ownership

## Technologies

- Python
- Django
- Django REST Framework
- Token Authentication
- Git

## Requirements

Before installing KanMind, make sure the following tools are installed:

- **Python 3:** [Download Python](https://www.python.org/downloads/)
- **Git:** [Download Git](https://git-scm.com/downloads)
- A terminal, such as Windows PowerShell or the integrated terminal in VS Code
- A code editor, such as [Visual Studio Code](https://code.visualstudio.com/)

## Installation

Follow the instructions for your operating system to set up KanMind locally.

### 1. Install Python

**Windows**

1. Download Python from [python.org](https://www.python.org/downloads/).
2. Run the installer.
3. Enable **Add Python to PATH** during installation.
4. Complete the installation.

Verify the installation in PowerShell:

```powershell
python --version
pip --version
```

If `python` is not recognized, try:

```powershell
py --version
```

**macOS**

1. Download Python from [python.org](https://www.python.org/downloads/macos/).
2. Open the downloaded installer and follow the instructions.
3. Open the Terminal application.

Verify the installation:

```bash
python3 --version
python3 -m pip --version
```

### 2. Install Git

**Windows**

1. Download Git from [git-scm.com](https://git-scm.com/downloads).
2. Run the installer and follow the recommended default settings.
3. Open PowerShell or the VS Code terminal.

Verify the installation:

```powershell
git --version
```

**macOS**

Git can be installed using Apple's Command Line Tools.

Open Terminal and run:

```bash
git --version
```

If Git is not installed, macOS may prompt you to install the Command Line Tools. Follow the instructions.

Alternatively, download Git from [git-scm.com](https://git-scm.com/downloads/mac).

### 3. Clone the Repository

Open your terminal and navigate to the directory where you want to store the project.

Clone the repository:

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
```

Navigate into the project directory:

```bash
cd <YOUR_PROJECT_DIRECTORY>
```

Replace the placeholders with your GitHub repository URL and the name of the cloned project directory.

### 4. Create a Virtual Environment

**Windows**

Create the virtual environment:

```powershell
python -m venv venv
```

Activate it:

```powershell
.venv/Scripts/activate
```

If PowerShell blocks script execution, you can activate the environment using Command Prompt instead:

```cmd
.venv\Scripts\activate.bat
```

**macOS**

Create the virtual environment:

```bash
python3 -m venv venv
```

Activate it:

```bash
source venv/bin/activate
```

After activation, the terminal should display `(venv)`.

### 5. Install Dependencies

Make sure the virtual environment is activated.

Upgrade pip:

```bash
python -m pip install --upgrade pip
```

Install the project dependencies:

```bash
python -m pip install -r requirements.txt
```

The `requirements.txt` file must be present in the project root and contain all required Python packages.

### 6. Configure Environment Variables

Before starting the server, create a `.env` file in the project root directory, at the same level as `manage.py`.

The application uses environment variables to configure Django. A valid `SECRET_KEY` must be provided, otherwise the server will raise a `ValueError`.

Create a file named `.env` and add the following variable:

```dotenv
SECRET_KEY='your-secret-key'
```

Replace `your-secret-key` with a secure, randomly generated secret key.

You can generate a new Django secret key using the following command:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the generated key into your `.env` file:

```dotenv
SECRET_KEY='your-generated-secret-key'
```

Make sure the `.env` file is loaded by your Django settings using `load_dotenv()`.

**Important:** Never commit your `.env` file or secret keys to GitHub. Add the following entries to your `.gitignore` file:

```gitignore
.env
venv/
__pycache__/
*.py[cod]
db.sqlite3
```

Each developer must create their own local `.env` file before starting the application.

### 7. Apply Database Migrations

Run the database migrations:

```bash
python manage.py migrate
```

Optionally, create a superuser to access the Django administration interface:

```bash
python manage.py createsuperuser
```

Follow the prompts in the terminal.

### 8. Start the Development Server

Start the Django development server:

```bash
python manage.py runserver
```

The API is available at:

**http://127.0.0.1:8000/**

To stop the server, press `Ctrl + C` in the terminal.

### 9. Additional Information

- Activate the virtual environment whenever you open a new terminal to work on the project.
- On macOS, use `python3` to create the virtual environment if `python` is not available.
- On Windows, use `python` or `py` to create the virtual environment.
- Make sure `requirements.txt` is up to date before sharing the project.
- Never commit virtual environments, secret keys or sensitive credentials to GitHub.


## API Endpoints

All API endpoints are available under the `/api/` prefix. Most endpoints require a valid authentication token.

### Authentication

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/api/registration/` | Register a new user |
| POST | `/api/login/` | Authenticate a user and obtain a token |

### Boards

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/boards/` | Retrieve boards accessible to the current user |
| POST | `/api/boards/` | Create a new board |
| GET | `/api/boards/{board_id}/` | Retrieve a specific board |
| PATCH | `/api/boards/{board_id}/` | Update a board and its members |
| DELETE | `/api/boards/{board_id}/` | Delete a board (owner only) |
| GET | `/api/email-check/` | Check whether an email address is registered |

### Tasks

| Method | Endpoint | Description |
| --- | --- | --- |
| POST | `/api/tasks/` | Create a new task |
| GET | `/api/tasks/{task_id}/` | Retrieve a specific task |
| PATCH | `/api/tasks/{task_id}/` | Update a task |
| DELETE | `/api/tasks/{task_id}/` | Delete a task (subject to permission rules) |
| GET | `/api/tasks/assigned-to-me/` | Retrieve tasks assigned to the current user |
| GET | `/api/tasks/reviewing/` | Retrieve tasks assigned to the current user for review |

### Comments

| Method | Endpoint | Description |
| --- | --- | --- |
| GET | `/api/tasks/{task_id}/comments/` | Retrieve comments for a task |
| POST | `/api/tasks/{task_id}/comments/` | Create a comment on a task |
| GET | `/api/tasks/{task_id}/comments/{id}/` | Retrieve a specific comment |
| DELETE | `/api/tasks/{task_id}/comments/{id}/` | Delete a comment (author only) |

**Placeholders:**

The API endpoints use the following placeholders:

- `{board_id}` – The ID of the board.
- `{task_id}` – The ID of the task.
- `{id}` – The ID of a specific resource, such as a comment.

## Authentication

KanMind uses Django REST Framework's token authentication.

### 1. Obtain a Token

Send a `POST` request to:

```text
http://127.0.0.1:8000/api/login/
```

Provide the required login credentials in the request body. A successful login returns an authentication token.

### 2. Authenticate API Requests

Include the token in the `Authorization` header of protected requests:

```http
Authorization: Token YOUR_AUTH_TOKEN
```

Replace `YOUR_AUTH_TOKEN` with the token returned by the login endpoint.

## HTTP Status Codes

| Status Code | Meaning |
| --- | --- |
| 200 OK | Request successful |
| 201 Created | Resource created successfully |
| 204 No Content | Request successful, no response body |
| 400 Bad Request | Invalid request data |
| 401 Unauthorized | Authentication missing or invalid |
| 403 Forbidden | Insufficient permissions |
| 404 Not Found | Resource not found |
| 500 Internal Server Error | Unexpected server error |

## Permissions

Access to KanMind resources is controlled by authentication and permission rules.

- **Authentication:** Protected endpoints require a valid token.
- **Boards:** Users can access boards they own or are members of. Only the board owner can delete a board.
- **Tasks:** Task access depends on board membership and the applicable task permissions. Creating and deleting tasks is subject to additional authorization rules.
- **Comments:** Users must be members of the associated board to access its comments. Only the author can delete a comment.

## Development Notes

- Activate the virtual environment before installing dependencies or running Django commands.
- Run database migrations after pulling changes that introduce new migrations.
- Keep credentials and secret keys out of version control.
- Do not commit the local virtual environment or local database files.

## License

This project was created exclusively as part of the Developer Akademie training program. It is intended for educational and demonstration purposes only and is not licensed for free use, distribution, modification, or redistribution without prior permission from the author.
