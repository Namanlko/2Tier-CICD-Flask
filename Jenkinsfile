pipeline {
    agent any

    options {
        disableConcurrentBuilds()
        timeout(time: 15, unit: 'MINUTES')
    }

    // Fallback if the GitHub webhook is not configured.
    // With a webhook, replace this with: githubPush()
    triggers {
        pollSCM('H/5 * * * *')
    }

    stages {
        // Source checkout happens automatically ("Pipeline script from SCM").

        stage('Prepare Environment') {
            steps {
                // Jenkins credential of type "Secret file" containing the contents of .env
                withCredentials([file(credentialsId: 'two-tier-env', variable: 'ENV_FILE')]) {
                    sh 'cp "$ENV_FILE" .env'
                }
            }
        }

        stage('Build & Deploy') {
            steps {
                sh 'docker compose down || true'
                sh 'docker compose up --build -d'
            }
        }

        stage('Verify') {
            steps {
                sh '''
                    for i in $(seq 1 20); do
                        if curl -fsS http://localhost:5000/ready; then
                            echo "Application is healthy"
                            exit 0
                        fi
                        echo "Waiting for application... ($i/20)"
                        sleep 6
                    done
                    echo "Application did not become healthy"
                    exit 1
                '''
            }
        }
    }

    post {
        failure {
            sh 'docker compose ps || true'
            sh 'docker compose logs --tail=50 || true'
        }
        always {
            sh 'rm -f .env'
        }
    }
}
