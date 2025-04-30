#!/bin/bash
# Deployment script template

# Configuration
PROJECT_NAME="{{project_name}}"
DEPLOY_ENV="{{environment}}"  # staging or production
DEPLOY_USER="{{deploy_user}}"
DEPLOY_HOST="{{deploy_host}}"
DEPLOY_PATH="/var/www/${PROJECT_NAME}"

# Deployment steps
echo "Starting deployment of ${PROJECT_NAME} to ${DEPLOY_ENV}..."

# 1. Build application
echo "Building application..."
docker-compose -f docker-compose.${DEPLOY_ENV}.yml build

# 2. Run tests
echo "Running tests..."
docker-compose -f docker-compose.test.yml up --abort-on-container-exit

# 3. Push to deployment server
echo "Pushing to deployment server..."
rsync -avz --exclude "node_modules" --exclude ".git" \
    ./ ${DEPLOY_USER}@${DEPLOY_HOST}:${DEPLOY_PATH}/

# 4. Deploy on server
echo "Deploying on server..."
ssh ${DEPLOY_USER}@${DEPLOY_HOST} "cd ${DEPLOY_PATH} && \
    docker-compose -f docker-compose.${DEPLOY_ENV}.yml down && \
    docker-compose -f docker-compose.${DEPLOY_ENV}.yml up -d"

echo "Deployment completed!"
