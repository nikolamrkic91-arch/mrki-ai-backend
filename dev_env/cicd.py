#!/usr/bin/env python3
"""
Mrki CI/CD Pipeline Generator
Generates CI/CD configurations for various platforms
"""

from pathlib import Path
from typing import Dict, List, Optional
from enum import Enum


class CICDPlatform(Enum):
    """Supported CI/CD platforms"""
    GITHUB_ACTIONS = "github_actions"
    GITLAB_CI = "gitlab_ci"
    AZURE_DEVOPS = "azure_devops"
    JENKINS = "jenkins"
    CIRCLECI = "circleci"
    TRAVIS = "travis"


class CICDGenerator:
    """CI/CD configuration generator"""
    
    def __init__(self, output_path: str = "."):
        self.output_path = Path(output_path)
    
    def generate(self, platform: CICDPlatform, stack_type: str = "mern") -> Path:
        """Generate CI/CD configuration for specified platform"""
        generators = {
            CICDPlatform.GITHUB_ACTIONS: self._generate_github_actions,
            CICDPlatform.GITLAB_CI: self._generate_gitlab_ci,
            CICDPlatform.AZURE_DEVOPS: self._generate_azure_devops,
            CICDPlatform.JENKINS: self._generate_jenkins,
            CICDPlatform.CIRCLECI: self._generate_circleci,
            CICDPlatform.TRAVIS: self._generate_travis,
        }
        
        generator = generators.get(platform)
        if not generator:
            raise ValueError(f"Unsupported platform: {platform}")
        
        return generator(stack_type)
    
    def _generate_github_actions(self, stack_type: str) -> Path:
        """Generate GitHub Actions workflows"""
        workflows_dir = self.output_path / ".github" / "workflows"
        workflows_dir.mkdir(parents=True, exist_ok=True)
        
        # CI workflow
        ci_content = self._get_github_ci_workflow(stack_type)
        ci_file = workflows_dir / "ci.yml"
        ci_file.write_text(ci_content)
        
        # CD workflow
        cd_content = self._get_github_cd_workflow(stack_type)
        cd_file = workflows_dir / "cd.yml"
        cd_file.write_text(cd_content)
        
        # Security scan workflow
        security_content = self._get_github_security_workflow()
        security_file = workflows_dir / "security.yml"
        security_file.write_text(security_content)
        
        return workflows_dir
    
    def _get_github_ci_workflow(self, stack_type: str) -> str:
        """Get GitHub Actions CI workflow"""
        backend_setup = self._get_backend_setup_steps(stack_type)
        backend_test = self._get_backend_test_steps(stack_type)
        
        return f'''name: CI

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  NODE_VERSION: '18'
  PYTHON_VERSION: '3.11'
  GO_VERSION: '1.21'

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: '**/package-lock.json'
      
      - name: Install dependencies (Backend)
        run: |
          cd backend
          npm ci
      
      - name: Install dependencies (Frontend)
        run: |
          cd frontend
          npm ci
      
      - name: Run ESLint (Backend)
        run: |
          cd backend
          npm run lint || true
      
      - name: Run ESLint (Frontend)
        run: |
          cd frontend
          npm run lint || true

  test-backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        ports:
          - 6379:6379
      
      mongodb:
        image: mongo:7
        ports:
          - 27017:27017
    
    steps:
      - uses: actions/checkout@v4
      
      {backend_setup}
      
      {backend_test}

  test-frontend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: frontend/package-lock.json
      
      - name: Install dependencies
        run: |
          cd frontend
          npm ci
      
      - name: Run tests
        run: |
          cd frontend
          npm test -- --watchAll=false --coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          directory: ./frontend/coverage
          flags: frontend

  build:
    runs-on: ubuntu-latest
    needs: [lint, test-backend, test-frontend]
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Build Docker images
        run: |
          docker-compose -f docker-compose.yml build
      
      - name: Test Docker images
        run: |
          docker-compose -f docker-compose.yml up -d
          sleep 10
          curl -f http://localhost:5000/health || exit 1
          docker-compose -f docker-compose.yml down
'''
    
    def _get_github_cd_workflow(self, stack_type: str) -> str:
        """Get GitHub Actions CD workflow"""
        return '''name: CD

on:
  push:
    branches: [main]
    tags: ['v*']

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3
      
      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
      
      - name: Build and push API image
        uses: docker/build-push-action@v5
        with:
          context: ./backend
          push: true
          tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-api:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
      
      - name: Build and push Frontend image
        uses: docker/build-push-action@v5
        with:
          context: ./frontend
          push: true
          tags: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-frontend:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max

  deploy-staging:
    runs-on: ubuntu-latest
    needs: build-and-push
    environment: staging
    if: github.ref == 'refs/heads/develop'
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to Staging
        run: |
          echo "Deploying to staging environment..."
          # Add your staging deployment commands here

  deploy-production:
    runs-on: ubuntu-latest
    needs: build-and-push
    environment: production
    if: startsWith(github.ref, 'refs/tags/v')
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to Production
        run: |
          echo "Deploying to production environment..."
          # Add your production deployment commands here
      
      - name: Create Release
        uses: actions/create-release@v1
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          tag_name: ${{ github.ref }}
          release_name: Release ${{ github.ref }}
          draft: false
          prerelease: false
'''
    
    def _get_github_security_workflow(self) -> str:
        """Get GitHub Actions security workflow"""
        return '''name: Security Scan

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday

jobs:
  dependency-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Run npm audit (Backend)
        run: |
          cd backend
          npm audit --audit-level=moderate || true
      
      - name: Run npm audit (Frontend)
        run: |
          cd frontend
          npm audit --audit-level=moderate || true
      
      - name: Run Snyk to check for vulnerabilities
        uses: snyk/actions/node@master
        continue-on-error: true
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}

  code-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Initialize CodeQL
        uses: github/codeql-action/init@v2
        with:
          languages: javascript, python
      
      - name: Autobuild
        uses: github/codeql-action/autobuild@v2
      
      - name: Perform CodeQL Analysis
        uses: github/codeql-action/analyze@v2

  secret-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        with:
          fetch-depth: 0
      
      - name: TruffleHog OSS
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base: main
          head: HEAD
          extra_args: --debug --only-verified
'''
    
    def _get_backend_setup_steps(self, stack_type: str) -> str:
        """Get backend setup steps based on stack type"""
        if "python" in stack_type.lower() or "django" in stack_type.lower() or "fastapi" in stack_type.lower():
            return '''- name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: ${{ env.PYTHON_VERSION }}
      
      - name: Install dependencies
        run: |
          cd backend
          pip install -r requirements.txt
          pip install pytest pytest-cov
      
      - name: Setup test database
        run: |
          cd backend
          alembic upgrade head || true'''
        
        elif "go" in stack_type.lower():
            return '''- name: Setup Go
        uses: actions/setup-go@v4
        with:
          go-version: ${{ env.GO_VERSION }}
      
      - name: Install dependencies
        run: |
          cd backend
          go mod download
      
      - name: Run migrations
        run: |
          cd backend
          go run cmd/migrate/main.go || true'''
        
        else:  # Node.js default
            return '''- name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: ${{ env.NODE_VERSION }}
          cache: 'npm'
          cache-dependency-path: backend/package-lock.json
      
      - name: Install dependencies
        run: |
          cd backend
          npm ci
      
      - name: Setup test database
        run: |
          cd backend
          npm run db:migrate || true'''
    
    def _get_backend_test_steps(self, stack_type: str) -> str:
        """Get backend test steps based on stack type"""
        if "python" in stack_type.lower() or "django" in stack_type.lower() or "fastapi" in stack_type.lower():
            return '''- name: Run tests
        run: |
          cd backend
          pytest --cov=app --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml
          flags: backend'''
        
        elif "go" in stack_type.lower():
            return '''- name: Run tests
        run: |
          cd backend
          go test -v -race -coverprofile=coverage.out ./...
          go tool cover -html=coverage.out -o coverage.html
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.out
          flags: backend'''
        
        else:  # Node.js default
            return '''- name: Run tests
        run: |
          cd backend
          npm test -- --coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          directory: ./backend/coverage
          flags: backend'''
    
    def _generate_gitlab_ci(self, stack_type: str) -> Path:
        """Generate GitLab CI configuration"""
        content = f'''stages:
  - build
  - test
  - security
  - deploy

variables:
  NODE_VERSION: "18"
  DOCKER_DRIVER: overlay2
  DOCKER_TLS_CERTDIR: ""

# Cache configuration
cache:
  paths:
    - node_modules/
    - .npm/

# Build stage
build:backend:
  stage: build
  image: node:${{NODE_VERSION}}
  script:
    - cd backend
    - npm ci
    - npm run build
  artifacts:
    paths:
      - backend/dist/

build:frontend:
  stage: build
  image: node:${{NODE_VERSION}}
  script:
    - cd frontend
    - npm ci
    - npm run build
  artifacts:
    paths:
      - frontend/build/

# Test stage
test:backend:
  stage: test
  image: node:${{NODE_VERSION}}
  services:
    - postgres:15
    - redis:7
  variables:
    POSTGRES_DB: test
    POSTGRES_USER: postgres
    POSTGRES_PASSWORD: postgres
    DATABASE_URL: postgres://postgres:postgres@postgres:5432/test
  script:
    - cd backend
    - npm ci
    - npm test -- --coverage
  coverage: '/All files[^|]*\\|[^|]*\\s+([\\d\\.]+)/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: backend/coverage/cobertura-coverage.xml

test:frontend:
  stage: test
  image: node:${{NODE_VERSION}}
  script:
    - cd frontend
    - npm ci
    - npm test -- --watchAll=false --coverage
  coverage: '/All files[^|]*\\|[^|]*\\s+([\\d\\.]+)/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: frontend/coverage/cobertura-coverage.xml

# Security stage
security:dependency-check:
  stage: security
  image: node:${{NODE_VERSION}}
  script:
    - cd backend && npm audit --audit-level=moderate || true
    - cd ../frontend && npm audit --audit-level=moderate || true
  allow_failure: true

security:sast:
  stage: security
  image: returntocorp/semgrep
  script:
    - semgrep --config=auto --error --json .
  allow_failure: true

# Deploy stage
deploy:staging:
  stage: deploy
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker build -t $CI_REGISTRY_IMAGE/api:$CI_COMMIT_SHA ./backend
    - docker build -t $CI_REGISTRY_IMAGE/frontend:$CI_COMMIT_SHA ./frontend
    - docker push $CI_REGISTRY_IMAGE/api:$CI_COMMIT_SHA
    - docker push $CI_REGISTRY_IMAGE/frontend:$CI_COMMIT_SHA
  only:
    - develop

deploy:production:
  stage: deploy
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker login -u $CI_REGISTRY_USER -p $CI_REGISTRY_PASSWORD $CI_REGISTRY
    - docker build -t $CI_REGISTRY_IMAGE/api:latest ./backend
    - docker build -t $CI_REGISTRY_IMAGE/frontend:latest ./frontend
    - docker push $CI_REGISTRY_IMAGE/api:latest
    - docker push $CI_REGISTRY_IMAGE/frontend:latest
  only:
    - tags
  when: manual
'''
        
        gitlab_file = self.output_path / ".gitlab-ci.yml"
        gitlab_file.write_text(content)
        return gitlab_file
    
    def _generate_azure_devops(self, stack_type: str) -> Path:
        """Generate Azure DevOps pipeline"""
        azure_dir = self.output_path / "azure-pipelines"
        azure_dir.mkdir(parents=True, exist_ok=True)
        
        content = '''trigger:
  branches:
    include:
      - main
      - develop

pr:
  branches:
    include:
      - main

variables:
  nodeVersion: '18.x'
  vmImageName: 'ubuntu-latest'

stages:
- stage: Build
  displayName: 'Build Stage'
  jobs:
  - job: BuildBackend
    displayName: 'Build Backend'
    pool:
      vmImage: $(vmImageName)
    steps:
    - task: NodeTool@0
      inputs:
        versionSpec: $(nodeVersion)
      displayName: 'Install Node.js'
    
    - script: |
        cd backend
        npm ci
        npm run build
      displayName: 'Build Backend'
    
    - task: PublishBuildArtifacts@1
      inputs:
        PathtoPublish: 'backend/dist'
        ArtifactName: 'backend'

  - job: BuildFrontend
    displayName: 'Build Frontend'
    pool:
      vmImage: $(vmImageName)
    steps:
    - task: NodeTool@0
      inputs:
        versionSpec: $(nodeVersion)
      displayName: 'Install Node.js'
    
    - script: |
        cd frontend
        npm ci
        npm run build
      displayName: 'Build Frontend'
    
    - task: PublishBuildArtifacts@1
      inputs:
        PathtoPublish: 'frontend/build'
        ArtifactName: 'frontend'

- stage: Test
  displayName: 'Test Stage'
  dependsOn: Build
  jobs:
  - job: TestBackend
    displayName: 'Test Backend'
    pool:
      vmImage: $(vmImageName)
    steps:
    - task: NodeTool@0
      inputs:
        versionSpec: $(nodeVersion)
      displayName: 'Install Node.js'
    
    - script: |
        cd backend
        npm ci
        npm test -- --coverage
      displayName: 'Run Backend Tests'
    
    - task: PublishTestResults@2
      inputs:
        testResultsFormat: 'JUnit'
        testResultsFiles: '**/junit.xml'
        mergeTestResults: true
    
    - task: PublishCodeCoverageResults@1
      inputs:
        codeCoverageTool: 'Cobertura'
        summaryFileLocation: '**/coverage/cobertura-coverage.xml'

  - job: TestFrontend
    displayName: 'Test Frontend'
    pool:
      vmImage: $(vmImageName)
    steps:
    - task: NodeTool@0
      inputs:
        versionSpec: $(nodeVersion)
      displayName: 'Install Node.js'
    
    - script: |
        cd frontend
        npm ci
        npm test -- --watchAll=false --coverage
      displayName: 'Run Frontend Tests'

- stage: Deploy
  displayName: 'Deploy Stage'
  dependsOn: Test
  condition: and(succeeded(), eq(variables['Build.SourceBranch'], 'refs/heads/main'))
  jobs:
  - deployment: DeployProduction
    displayName: 'Deploy to Production'
    pool:
      vmImage: $(vmImageName)
    environment: 'production'
    strategy:
      runOnce:
        deploy:
          steps:
          - download: current
            artifact: backend
          
          - download: current
            artifact: frontend
          
          - script: |
              echo "Deploying to production..."
              # Add deployment commands here
            displayName: 'Deploy Application'
'''
        
        pipeline_file = azure_dir / "azure-pipelines.yml"
        pipeline_file.write_text(content)
        return azure_dir
    
    def _generate_jenkins(self, stack_type: str) -> Path:
        """Generate Jenkins pipeline"""
        content = '''pipeline {
    agent any
    
    environment {
        NODE_VERSION = '18'
        DOCKER_REGISTRY = 'registry.example.com'
    }
    
    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }
        
        stage('Install Dependencies') {
            parallel {
                stage('Backend') {
                    steps {
                        dir('backend') {
                            sh 'npm ci'
                        }
                    }
                }
                stage('Frontend') {
                    steps {
                        dir('frontend') {
                            sh 'npm ci'
                        }
                    }
                }
            }
        }
        
        stage('Lint') {
            parallel {
                stage('Backend') {
                    steps {
                        dir('backend') {
                            sh 'npm run lint || true'
                        }
                    }
                }
                stage('Frontend') {
                    steps {
                        dir('frontend') {
                            sh 'npm run lint || true'
                        }
                    }
                }
            }
        }
        
        stage('Test') {
            parallel {
                stage('Backend') {
                    steps {
                        dir('backend') {
                            sh 'npm test -- --coverage'
                        }
                    }
                    post {
                        always {
                            publishHTML([
                                allowMissing: false,
                                alwaysLinkToLastBuild: true,
                                keepAll: true,
                                reportDir: 'backend/coverage',
                                reportFiles: 'index.html',
                                reportName: 'Backend Coverage Report'
                            ])
                        }
                    }
                }
                stage('Frontend') {
                    steps {
                        dir('frontend') {
                            sh 'npm test -- --watchAll=false --coverage'
                        }
                    }
                    post {
                        always {
                            publishHTML([
                                allowMissing: false,
                                alwaysLinkToLastBuild: true,
                                keepAll: true,
                                reportDir: 'frontend/coverage',
                                reportFiles: 'index.html',
                                reportName: 'Frontend Coverage Report'
                            ])
                        }
                    }
                }
            }
        }
        
        stage('Build') {
            parallel {
                stage('Backend') {
                    steps {
                        dir('backend') {
                            sh 'npm run build'
                        }
                    }
                }
                stage('Frontend') {
                    steps {
                        dir('frontend') {
                            sh 'npm run build'
                        }
                    }
                }
            }
        }
        
        stage('Security Scan') {
            steps {
                sh '''
                    cd backend && npm audit --audit-level=moderate || true
                    cd ../frontend && npm audit --audit-level=moderate || true
                '''
            }
        }
        
        stage('Deploy') {
            when {
                branch 'main'
            }
            steps {
                sh '''
                    echo "Deploying to production..."
                    # Add deployment commands here
                '''
            }
        }
    }
    
    post {
        always {
            cleanWs()
        }
        success {
            echo 'Pipeline completed successfully!'
        }
        failure {
            echo 'Pipeline failed!'
        }
    }
}
'''
        
        jenkins_file = self.output_path / "Jenkinsfile"
        jenkins_file.write_text(content)
        return jenkins_file
    
    def _generate_circleci(self, stack_type: str) -> Path:
        """Generate CircleCI configuration"""
        circleci_dir = self.output_path / ".circleci"
        circleci_dir.mkdir(parents=True, exist_ok=True)
        
        content = '''version: 2.1

orbs:
  node: circleci/node@5.1.0
  docker: circleci/docker@2.4.0

executors:
  node-executor:
    docker:
      - image: cimg/node:18.0
      - image: cimg/postgres:15.0
        environment:
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: test
      - image: cimg/redis:7.0
    working_directory: ~/project

jobs:
  lint:
    executor: node-executor
    steps:
      - checkout
      - node/install-packages:
          pkg-manager: npm
          app-dir: backend
      - node/install-packages:
          pkg-manager: npm
          app-dir: frontend
      - run:
          name: Lint Backend
          command: cd backend && npm run lint || true
      - run:
          name: Lint Frontend
          command: cd frontend && npm run lint || true

  test-backend:
    executor: node-executor
    steps:
      - checkout
      - node/install-packages:
          pkg-manager: npm
          app-dir: backend
      - run:
          name: Run Backend Tests
          command: cd backend && npm test -- --coverage
      - store_test_results:
          path: backend/coverage
      - store_artifacts:
          path: backend/coverage

  test-frontend:
    executor: node-executor
    steps:
      - checkout
      - node/install-packages:
          pkg-manager: npm
          app-dir: frontend
      - run:
          name: Run Frontend Tests
          command: cd frontend && npm test -- --watchAll=false --coverage
      - store_test_results:
          path: frontend/coverage
      - store_artifacts:
          path: frontend/coverage

  build:
    executor: node-executor
    steps:
      - checkout
      - setup_remote_docker
      - run:
          name: Build Docker Images
          command: docker-compose build

  deploy:
    docker:
      - image: cimg/base:stable
    steps:
      - checkout
      - run:
          name: Deploy to Production
          command: |
            echo "Deploying to production..."
            # Add deployment commands here

workflows:
  version: 2
  ci-cd:
    jobs:
      - lint
      - test-backend:
          requires:
            - lint
      - test-frontend:
          requires:
            - lint
      - build:
          requires:
            - test-backend
            - test-frontend
      - deploy:
          requires:
            - build
          filters:
            branches:
              only: main
'''
        
        config_file = circleci_dir / "config.yml"
        config_file.write_text(content)
        return circleci_dir
    
    def _generate_travis(self, stack_type: str) -> Path:
        """Generate Travis CI configuration"""
        content = '''language: node_js
node_js:
  - "18"

cache:
  directories:
    - node_modules
    - backend/node_modules
    - frontend/node_modules

services:
  - postgresql
  - redis-server

env:
  - NODE_ENV=test DATABASE_URL=postgres://postgres@localhost/test

before_script:
  - psql -c 'create database test;' -U postgres

jobs:
  include:
    - stage: lint
      script:
        - cd backend && npm run lint || true
        - cd ../frontend && npm run lint || true
    
    - stage: test
      script:
        - cd backend && npm test -- --coverage
        - cd ../frontend && npm test -- --watchAll=false --coverage
      after_success:
        - bash <(curl -s https://codecov.io/bash)
    
    - stage: build
      script:
        - docker-compose build
    
    - stage: deploy
      if: branch = main
      script:
        - echo "Deploying to production..."
        # Add deployment commands here

stages:
  - lint
  - test
  - build
  - deploy
'''
        
        travis_file = self.output_path / ".travis.yml"
        travis_file.write_text(content)
        return travis_file


if __name__ == "__main__":
    generator = CICDGenerator()
    
    # Generate GitHub Actions workflow
    generator.generate(CICDPlatform.GITHUB_ACTIONS, "mern")
    print("GitHub Actions workflow generated!")
