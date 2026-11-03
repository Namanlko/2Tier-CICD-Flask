# 🚀 Two-Tier Flask App: DevOps CI/CD Pipeline on AWS

## 📌 Project Overview

This project demonstrates a complete **CI/CD pipeline for a two-tier web application** using modern DevOps tools. 

The application is built using **Flask (Python) and MySQL**, deployed using **Docker containers**. Jenkins automates the build and deployment process whenever new code is pushed to GitHub (via a webhook or SCM polling). The entire setup runs on an **AWS EC2 instance**.

![UI](diagram/1.jpg)

## 🏗️ Architecture Diagram

```
+-----------------+      +----------------------+      +-----------------------------+
|   Developer     |----->|     GitHub Repo      |----->|        Jenkins Server       |
| (pushes code)   |      | (Source Code Mgmt)   |      |  (on AWS EC2)               |
+-----------------+      +----------------------+      |                             |
                                                       | 1. Checks out repo (SCM)    |
                                                       | 2. Builds & runs Compose    |
                                                       | 3. Verifies /ready endpoint |
                                                       +--------------+--------------+
                                                                      |
                                                                      | Deploys
                                                                      v
                                                       +-----------------------------+
                                                       |      Application Server     |
                                                       |      (Same AWS EC2)         |
                                                       |                             |
                                                       | +-------------------------+ |
                                                       | | Docker Container: Flask | |
                                                       | +-------------------------+ |
                                                       |              |              |
                                                       |              v              |
                                                       | +-------------------------+ |
                                                       | | Docker Container: MySQL | |
                                                       | +-------------------------+ |
                                                       +-----------------------------+
```

## 🛠️ DevOps Tools Used

| Tool | Purpose |
|------|---------|
| AWS EC2 | Cloud infrastructure |
| Git & GitHub | Source code management |
| Jenkins | CI/CD automation |
| Docker | Containerization |
| Docker Compose | Multi-container orchestration |
| Flask | Backend application |
| MySQL | Database |

## 💻 Run Locally

```bash
git clone https://github.com/Namanlko/2Tier-CICD-Flask.git
cd 2Tier-CICD-Flask
cp .env.example .env      # then edit .env and set your own passwords
docker compose up -d --build
```

Open `http://localhost:5000`. Health endpoints: `/health` (app is up) and `/ready` (app can reach MySQL).

## Step 1: Launch AWS EC2 Instance

1. Go to AWS EC2 console
2. Launch a new instance
3. Select **Ubuntu 24.04 LTS**
4. Instance type: **t3.small** (2 GB RAM) or larger. Jenkins, MySQL 8 and Flask together will not fit comfortably in 1 GB (t2.micro)
5. Create a key pair for SSH access

![EC2 Instance](diagram/2.jpg)

## Step 2: Configure Security Group

Allow the following inbound ports:

| Port | Purpose | Source |
|------|---------|--------|
| 22 | SSH | Your IP only |
| 5000 | Flask app | Anywhere (or your IP) |
| 8080 | Jenkins UI | Your IP only |

MySQL (3306) is **not** exposed; it is reachable only inside the Docker network.

![Security Group](diagram/3.jpg)

## Step 3: Connect to EC2

```bash
ssh -i your-key.pem ubuntu@your-ec2-public-ip
```

## Step 4: Install Required Dependencies

```bash
# Update packages
sudo apt update && sudo apt upgrade -y

# Install Git, Docker, Docker Compose
sudo apt install git docker.io docker-compose-v2 curl -y

# Start Docker
sudo systemctl start docker
sudo systemctl enable docker

# Allow current user to run Docker (log out and back in afterwards)
sudo usermod -aG docker $USER
```

## Step 5: Install Jenkins

```bash
# Install Java
sudo apt install openjdk-17-jdk -y

# Add Jenkins repository
# NOTE: Jenkins rotates its signing key. If apt reports a signature error,
# check https://www.jenkins.io/doc/book/installing/linux/ for the current key file name.
sudo wget -O /usr/share/keyrings/jenkins-keyring.asc \
  https://pkg.jenkins.io/debian-stable/jenkins.io-2026.key

echo "deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] https://pkg.jenkins.io/debian-stable binary/" \
  | sudo tee /etc/apt/sources.list.d/jenkins.list

# Install Jenkins
sudo apt update
sudo apt install jenkins -y

# Start Jenkins
sudo systemctl start jenkins
sudo systemctl enable jenkins
```

## Step 6: Jenkins Initial Setup

```bash
# Get admin password
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

Open in browser: `http://<EC2-PUBLIC-IP>:8080`

Paste the password and install suggested plugins.

## Step 7: Give Jenkins Docker Permission

```bash
sudo usermod -aG docker jenkins
sudo systemctl restart jenkins
```

![Jenkins](diagram/4.jpg)

## Step 8: Repository Structure

```
2Tier-CICD-Flask/
├── diagram/
├── templates/
│   └── index.html
├── .dockerignore
├── .env.example
├── .gitignore
├── Dockerfile
├── Jenkinsfile
├── README.md
├── app.py
├── docker-compose.yml
├── message.sql
└── requirements.txt
```

## 🔐 Step 9: Add Secrets to Jenkins

Passwords are **not** stored in the repository. The `.env` file is git-ignored, so Jenkins needs it as a credential:

1. Create a local `.env` from `.env.example` with strong passwords
2. Jenkins → **Manage Jenkins → Credentials → Add Credentials**
3. Kind: **Secret file**, upload your `.env`
4. ID: `two-tier-env`

The Jenkinsfile copies this file into the workspace as `.env` for the build and deletes it afterwards.

## 🐳 Dockerfile

See [`Dockerfile`](Dockerfile): Python 3.12 slim, dependencies installed from `requirements.txt`, app runs as a non-root user under **gunicorn**.

## 🐙 Docker Compose File

See [`docker-compose.yml`](docker-compose.yml). Key points:

- `mysql:8.0` with a named volume (`mysql-data`) and a healthcheck
- Credentials come from `.env` (see `.env.example`)
- `message.sql` is mounted into MySQL's init directory to create the table on first start
- Flask waits for MySQL to be **healthy** (`depends_on: condition: service_healthy`)
- Both services share the custom network `two-tier`; MySQL has no published port

## 🔁 Jenkins Pipeline (Jenkinsfile)

See [`Jenkinsfile`](Jenkinsfile). Stages:

1. **Prepare Environment** – loads `.env` from the `two-tier-env` Jenkins credential
2. **Build & Deploy** – `docker compose down` then `docker compose up --build -d`
3. **Verify** – polls `http://localhost:5000/ready` until the app and database respond

On failure it prints container status and logs. Source checkout is done by Jenkins itself (Pipeline script from SCM), so there is no separate clone stage.

## Step 10: Create Jenkins Pipeline

1. Go to Jenkins dashboard
2. Click **New Item** → Select **Pipeline**
3. Choose **Pipeline script from SCM**
4. Select **Git**
5. Enter `https://github.com/Namanlko/2Tier-CICD-Flask.git`, branch `main`
6. Script path: `Jenkinsfile`

Optional: add a GitHub webhook (`http://<JENKINS-IP>:8080/github-webhook/`) and change the trigger in the Jenkinsfile to `githubPush()` for instant builds. Without it, the pipeline polls GitHub every ~5 minutes.

![Pipeline Config](diagram/5.jpg)

## Step 11: Run the Pipeline

Click **Build Now** in Jenkins. The pipeline will:

1. Check out the GitHub repository
2. Build the image and deploy using Docker Compose
3. Verify the app is healthy

![Pipeline Run](diagram/6.jpg)

## ✅ Verify Deployment

```bash
# Check running containers (both should be "healthy")
docker ps

# Open app in browser
http://<EC2-PUBLIC-IP>:5000
```

![UI](diagram/1.jpg)

## 🌐 Infrastructure Diagram

![Infrastructure](diagram/8.png)

## 🔄 DevOps Workflow

![Workflow](diagram/9.png)

## 🏁 Conclusion

This project demonstrates a real-world DevOps workflow where deployment is fully automated. By integrating **GitHub, Jenkins, Docker, and AWS**, the process becomes faster, repeatable, and reliable.

*Built with ❤️ by **Naman Pandey** - DevOps | Cloud Engineer*
