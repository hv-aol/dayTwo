# AOL Trust: Data Roadster

An advanced reporting and analytics platform built for **AOL Trust** to streamline data visibility, simplify retrieval via natural language, and democratize report generation.

## 🚀 Core Components

* **Dynamic Dashboards:** Features out-of-the-box system dashboards, private custom dashboards, and collaborative team-shared workspaces.
* **NLP-Based Querying:** Enables non-technical users to input natural language questions, which the system automatically translates into optimized backend queries.
* **Template-Based SQL:** Provides pre-configured SQL templates where users input parameters (e.g., `teacher_code`, date ranges) to instantly generate charts and graphs.

## 🛠️ Tech Stack

* **Core Engine:** Streamlit
* **Environment Manager:** [Astral uv](https://docs.astral.sh/uv/ "uv - Astral Docs")
* **NLP Engine:** Brainwrapper [https://github.com/hv-aol/brainWrapper]
* **Database:** PostgreSQL

## 📦 Setup & Run (via uv)

### 1. Clone & Navigate
```bash
git clone the repo.
cd dayTwo.
```

### 2. Configure Environment
Following files are needed to run:
* Create a .secrets directory under the project root directory.
* Get the DB credentials from Admin. Create a master key for yourself using bcrypt, and encrypt the password and put it in the DB_USR_PWD. The current checked in version will not work for you
* Put the above generated master key in .secrets/.master_key file. Chmod 600 it.

This is all one need to configure. Rest uv will take care.

### 3. Start the Server
`uv run` automatically resolves dependencies, configures the virtual environment, and executes the application:
```bash
uv run streamlit run app.py
```

## 💡 Quick Start: Template Query
1. Go to **Template Queries** in the UI.
2. Select a report type and fill in the required fields (`teacher_code`, `dates`).
3. Click **Run Query** to view the auto-generated graph.

## 🔒 Security
* Restricted strictly to **AOL Trust** internal infrastructure.
* Enforces Role-Based Access Control (RBAC) on all data views and query executions.
