pipeline {
    agent any

    environment {
        DOCKER_HUB_CREDS = credentials('dockerhub-creds')
        DOCKER_HUB_USER = "${DOCKER_HUB_CREDS_USR}"
        DOCKER_HUB_PASSWORD = "${DOCKER_HUB_CREDS_PSW}"
        GIT_BRANCH = "${GIT_BRANCH ?: 'main'}"
        HELM_NAMESPACE = 'default'
        HELM_VALUES_FILE = 'infra/kubernetes/helm/values.yaml'
        IMAGE_TAG = "${BUILD_NUMBER}"
        PRESENTATION_IMAGE = "${DOCKER_HUB_USER}/ecommerce-presentation:${IMAGE_TAG}"
        APPLICATION_IMAGE = "${DOCKER_HUB_USER}/ecommerce-application:${IMAGE_TAG}"
        TRIVY_SEVERITY = 'HIGH,CRITICAL'
    }

    stages {
        stage('Checkout') {
            steps {
                echo "📦 Checking out code..."
                checkout scm
            }
        }

        stage('Build Docker Images') {
            parallel {
                stage('Build Presentation') {
                    steps {
                        sh 'docker build -t ${PRESENTATION_IMAGE} -f presentation/Dockerfile presentation/'
                    }
                }
                stage('Build Application') {
                    steps {
                        sh 'docker build -t ${APPLICATION_IMAGE} -f application/Dockerfile application/'
                    }
                }
            }
        }

        stage('Security Scan') {
            steps {
                sh '''
                    echo "🔍 Scanning images with Trivy..."
                    trivy image --severity ${TRIVY_SEVERITY} --no-progress ${PRESENTATION_IMAGE} | tee trivy-presentation.txt
                    trivy image --severity ${TRIVY_SEVERITY} --no-progress ${APPLICATION_IMAGE} | tee trivy-application.txt
                '''
            }
        }

        stage('Push to Docker Hub') {
            steps {
                sh '''
                    echo "${DOCKER_HUB_PASSWORD}" | docker login -u "${DOCKER_HUB_USER}" --password-stdin
                    docker push ${PRESENTATION_IMAGE}
                    docker push ${APPLICATION_IMAGE}
                    docker tag ${PRESENTATION_IMAGE} ${DOCKER_HUB_USER}/ecommerce-presentation:latest
                    docker tag ${APPLICATION_IMAGE} ${DOCKER_HUB_USER}/ecommerce-application:latest
                    docker push ${DOCKER_HUB_USER}/ecommerce-presentation:latest
                    docker push ${DOCKER_HUB_USER}/ecommerce-application:latest
                    docker logout
                    echo "✅ Images pushed to Docker Hub"
                '''
            }
        }

        stage('Update Helm Values') {
            steps {
                sh '''
                    cp ${HELM_VALUES_FILE} ${HELM_VALUES_FILE}.backup
                    sed -i "s|repository: .*ecommerce-presentation|repository: ${DOCKER_HUB_USER}/ecommerce-presentation|g" ${HELM_VALUES_FILE}
                    sed -i "s|tag: .*|tag: \"${IMAGE_TAG}\"|g" ${HELM_VALUES_FILE}
                    helm lint ./infra/kubernetes/helm || true
                    echo "📝 Helm values updated with image tag ${IMAGE_TAG}"
                '''
            }
        }

        stage('Commit & Push to Git') {
            steps {
                sh '''
                    git config user.email "jenkins@example.com"
                    git config user.name "Jenkins Pipeline"
                    if git diff --quiet ${HELM_VALUES_FILE}; then
                        echo "ℹ️ No changes to commit"
                    else
                        git add ${HELM_VALUES_FILE}
                        git commit -m "🔄 Update image tags to ${IMAGE_TAG} [skip ci]"
                        git push origin ${GIT_BRANCH}
                        echo "✅ Pushed to Git repository"
                    fi
                '''
            }
        }

        stage('Wait for ArgoCD Sync') {
            steps {
                sh '''
                    echo "🔄 ArgoCD will auto-sync within 3 minutes..."
                    sleep 10
                    echo "Monitor at: kubectl get application -n argocd"
                '''
            }
        }

        stage('Verify Deployment') {
            steps {
                sh '''
                    echo "✅ Verifying deployment..."
                    kubectl rollout status deployment/ecommerce-presentation -n ${HELM_NAMESPACE} --timeout=3m || true
                    kubectl get deployments,pods,svc -n ${HELM_NAMESPACE}
                    kubectl logs -n ${HELM_NAMESPACE} -l app=ecommerce-application --tail=15 || echo "No logs yet"
                '''
            }
        }
    }

    post {
        always {
            sh 'docker rmi ${PRESENTATION_IMAGE} ${APPLICATION_IMAGE} 2>/dev/null || true'
        }
        success {
            echo "✅ Pipeline succeeded! Images: ${IMAGE_TAG}"
        }
        failure {
            echo "❌ Pipeline failed. Check console logs for details."
        }
    }
}
