# Cyron — Cybersecurity Reconnaissance & Security Analysis Platform

> **A unified cybersecurity platform that brings reconnaissance, security analysis, and results visualization into a structured workflow.**

![Cyron Banner](docs/images/Cyron-banner.png)

## 📌 Overview

**Cyron** is a cybersecurity-focused web application designed to simplify and organize security reconnaissance and analysis workflows.

Instead of manually running multiple command-line security tools one by one and reviewing their output separately, Cyron provides a centralized interface where a user can submit a target and coordinate security utilities through a backend workflow.

The goal is to make reconnaissance results easier to collect, understand, document, and review while keeping the project modular and extensible.

> **Important:** Cyron is intended for authorized security testing, lab environments, CTFs, and systems for which you have explicit permission to assess.

---

## 🎯 Project Motivation

During cybersecurity learning, security professionals often use several tools for different stages of reconnaissance and analysis.

This can create challenges such as:

- Running multiple tools manually
- Switching between terminal sessions
- Reviewing different output formats
- Keeping reconnaissance results organized
- Repeating the same workflow for different authorized targets
- Connecting tool output to a single analysis workflow

Cyron was created as an attempt to solve this workflow problem through a single web-based interface.

---

## 🚀 Key Features

### 🔎 Reconnaissance Workflow

Cyron provides a centralized workflow for security reconnaissance and analysis.

Depending on the configured environment and installed tools, the backend can coordinate command-line utilities and collect their output.

### 🖥️ Web-Based Interface

A browser-based frontend provides a simpler way to interact with the backend instead of manually entering every command.

### ⚙️ Backend Orchestration

The backend acts as the central layer between the frontend and security utilities.

It is responsible for:

- Receiving requests
- Validating input
- Starting authorized security workflows
- Managing tool execution
- Collecting output
- Returning structured results

### 📊 Consolidated Results

Security-tool output can be organized into a unified result workflow, making it easier to identify areas that may require further manual security review.

### 🐳 Docker Support

Cyron is designed with containerized deployment in mind so that the frontend, backend, and supporting services can be deployed consistently.

### 🔌 Modular Architecture

The project is structured so additional security tools and analysis components can be integrated without redesigning the entire application.

---

## 🏗️ Architecture

```text
                         ┌─────────────────────┐
                         │       User          │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │   Cyron Frontend    │
                         │       React         │
                         └──────────┬──────────┘
                                    │
                              HTTP / REST API
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │    Cyron Backend    │
                         │       FastAPI       │
                         └──────────┬──────────┘
                                    │
                    ┌───────────────┼────────────────┐
                    │               │                │
                    ▼               ▼                ▼
             ┌────────────┐  ┌────────────┐  ┌────────────┐
             │ Recon Tool │  │ Recon Tool │  │ Analysis   │
             │     1      │  │     2      │  │ Components │
             └─────┬──────┘  └─────┬──────┘  └─────┬──────┘
                   │               │                │
                   └───────────────┼────────────────┘
                                   ▼
                         ┌─────────────────────┐
                         │ Result Processing   │
                         │ & Normalization     │
                         └──────────┬──────────┘
                                    │
                                    ▼
                         ┌─────────────────────┐
                         │ Consolidated Results │
                         │    / Dashboard       │
                         └─────────────────────┘
```

---

## 🧰 Technology Stack

### Frontend

- React
- JavaScript / TypeScript *(update according to the final implementation)*
- HTML
- CSS

### Backend

- Python
- FastAPI
- REST APIs

### Security / Networking

- Linux
- HTTP / HTTPS
- Network reconnaissance concepts
- Command-line security utilities
- Security assessment workflows

### Deployment

- Docker
- Docker Compose *(if enabled in the final deployment configuration)*

---

## 📁 Project Structure

The exact structure may vary depending on the current implementation.

A typical Cyron layout is:

```text
Cyron/
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── ...
│
├── backend/
│   ├── app/
│   ├── main.py
│   ├── requirements.txt
│   └── ...
│
├── tools/
│   └── security-tool integrations/
│
├── docker/
│   └── ...
│
├── docker-compose.yml
├── README.md
└── .gitignore
```

> Update this section to exactly match the final repository structure before publishing.

---

## ⚡ Getting Started

### Prerequisites

Before running Cyron locally, make sure the following are installed:

- Linux environment recommended
- Python 3.x
- Node.js and npm
- Git
- Docker
- Docker Compose
- Required security utilities used by your configured workflow

Verify the main dependencies:

```bash
python3 --version
node --version
npm --version
docker --version
docker compose version
git --version
```

---

# 🖥️ Local Development

## 1. Clone the Repository

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd Cyron
```

---

## 2. Backend Setup

Move into the backend directory:

```bash
cd backend
```

Create a virtual environment:

```bash
python3 -m venv venv
```

Activate it:

```bash
source venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Start the FastAPI server:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The backend should then be available at:

```text
http://localhost:8000
```

FastAPI documentation is normally available at:

```text
http://localhost:8000/docs
```

> If your backend entry point or port differs, update these commands to match the final implementation.

---

# 🌐 Frontend Setup

Open a second terminal.

From the frontend directory:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Start the development server:

```bash
npm run dev
```

The frontend will normally be available at:

```text
http://localhost:5173
```

> The exact port depends on the frontend configuration.

---

# 🐳 Docker Deployment

Cyron can be deployed using Docker to provide a reproducible environment.

Build the containers:

```bash
docker compose build
```

Start the services:

```bash
docker compose up
```

Run in detached mode:

```bash
docker compose up -d
```

View running containers:

```bash
docker compose ps
```

View logs:

```bash
docker compose logs -f
```

Stop the services:

```bash
docker compose down
```

> Ensure the final `docker-compose.yml` reflects the actual frontend, backend, networking, volumes, environment variables, and security-tool dependencies used by your project.

---

# 🔐 Security and Authorization

Cyron is a security testing and learning project.

It should only be used against:

- Systems you own
- Systems where you have explicit authorization
- Dedicated cybersecurity laboratories
- CTF environments
- Test infrastructure

Do **not** use Cyron to scan or assess systems without permission.

The project is designed to support authorized defensive security research and learning.

---

# 🧪 Testing

Before considering a deployment stable, test the following:

### Frontend

- UI loads correctly
- Input validation works
- API requests reach the backend
- Results are displayed correctly

### Backend

- API starts successfully
- Required endpoints respond correctly
- Invalid input is rejected
- Tool execution errors are handled
- Timeouts and failed commands are handled safely

### Tool Integration

- Required utilities are installed
- Tool paths are correctly configured
- Permissions are sufficient
- Output is captured correctly
- Tool failures do not crash the entire application

### Docker

- All required containers start
- Services can communicate
- Environment variables are correctly configured
- Volumes and permissions work as expected

---

# 📸 Screenshots

Add real screenshots of the working application here.

Recommended screenshots:

1. Cyron landing page
2. Target/input interface
3. Running analysis
4. Reconnaissance results
5. Consolidated findings
6. Docker services running

Example:

```markdown
![Cyron Dashboard](docs/images/dashboard.png)

![Cyron Results](docs/images/results.png)
```

---

# 🧠 What I Learned

Building Cyron helped me understand how cybersecurity tools can be integrated into a larger software system instead of being used independently from the terminal.

Key learning areas include:

- Linux security environments
- Networking fundamentals
- HTTP/HTTPS communication
- REST API development
- FastAPI backend development
- React frontend development
- CLI tool integration
- Process execution
- Error handling
- Docker and containerization
- Frontend-backend communication
- CORS configuration
- Security workflow automation
- Project architecture and deployment

---

# 🛡️ Security Considerations

Because Cyron can interact with security utilities, careful handling is important.

Recommended security controls include:

- Input validation
- Command argument validation
- Avoiding unsafe shell interpolation
- Least-privilege execution
- Process timeouts
- Resource limits
- Secure container configuration
- Restricted network access where appropriate
- Proper logging
- Avoiding exposure of sensitive tool output
- Environment-variable based secret management

Never hard-code API keys, passwords, tokens, or other secrets into the repository.

---

# 🔮 Future Improvements

Planned improvements may include:

- More security-tool integrations
- Improved result normalization
- Advanced vulnerability classification
- Better visualization of findings
- Authentication and authorization
- Background job processing
- Scan/task history
- Report generation
- Exportable security reports
- Improved error handling
- Container security hardening
- Role-based access control
- AI-assisted security analysis
- MITRE ATT&CK mapping
- Additional monitoring and logging capabilities

---

# 📈 Project Roadmap

```text
[✔] Project architecture
        │
        ▼
[✔] Frontend development
        │
        ▼
[✔] Backend development
        │
        ▼
[✔] API integration
        │
        ▼
[✔] Security-tool integration
        │
        ▼
[ ] Complete end-to-end testing
        │
        ▼
[ ] Docker deployment refinement
        │
        ▼
[ ] Security hardening
        │
        ▼
[ ] Advanced reporting
        │
        ▼
[ ] Additional security integrations
```

Update the checkboxes to reflect the actual current project status.

---

# ⚠️ Limitations

Cyron is an educational and portfolio project.

The accuracy and usefulness of the generated results depend on:

- The underlying security tools
- Tool configuration
- Target environment
- Network conditions
- Permissions
- Operating system
- Installed dependencies
- The quality of result parsing and normalization

Results should be manually validated by a qualified security professional before being treated as confirmed vulnerabilities.

---

# 🤝 Contributing

Contributions, suggestions, and improvements are welcome.

A typical contribution workflow:

```bash
git fork <repository>
git clone <your-fork>
git checkout -b feature/your-feature
```

Make your changes, test them, and submit a pull request.

Please ensure that contributions do not introduce unsafe command execution, credential exposure, or unauthorized scanning functionality.

---

# 📄 License

Add your chosen open-source license here.

For example:

```text
MIT License
```

If you choose MIT, add the corresponding `LICENSE` file to the repository.

---

# 👨‍💻 Author

**Ajmalharoon**

Computer Science Engineering Student  
Cybersecurity Enthusiast

### Areas of Interest

- Cybersecurity
- VAPT
- Network Security
- SOC / Blue Team
- Linux
- Python
- Security Automation
- Docker
- Cloud & Infrastructure Security

### Connect

- LinkedIn: `<YOUR_LINKEDIN_URL>`
- GitHub: `<YOUR_GITHUB_URL>`

---

# ⭐ Why Cyron?

Cyron was created as a practical cybersecurity portfolio project to explore the intersection of:

**Cybersecurity + Software Engineering + Automation + DevOps**

The project demonstrates an effort to move beyond individual cybersecurity tools and understand how security capabilities can be integrated into a complete, deployable application.

---

## ⭐ If you find this project useful

Consider giving the repository a ⭐ on GitHub and sharing feedback or suggestions.

---

## Disclaimer

Cyron is provided for authorized security testing, education, research, and laboratory environments only.

The author does not encourage or support unauthorized scanning, exploitation, intrusion, or disruption of systems.

**Always obtain explicit authorization before performing security testing.**
