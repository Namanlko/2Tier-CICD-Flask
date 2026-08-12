// Define Jenkins pipeline
pipeline{

    // Run pipeline on any available Jenkins agent
    agent any

    // Define different stages of CI/CD pipeline
    stages{

        // Stage to clone the project code from GitHub
        stage ('Code Clone'){
            steps{
                // Clone the main branch from GitHub repository
                git branch: 'main', url: 'https://github.com/Namanlko/2Tier-CICD-Flask.git'
            }
        }

        // Stage to build Docker image for the application
        stage ('Build Docker Image'){
            steps{
                // Build Docker image with name flask-app
                sh 'docker build -t flask-app:latest .'
            }
        }

        // Stage to deploy the application using Docker Compose
        stage ('Deploy with Docker Compose'){
            steps{
                // Stop existing containers if running
                sh 'docker compose down || true'

                // Build and start containers in detached mode
                sh 'docker compose up --build -d'
            }
        }
    }
}
