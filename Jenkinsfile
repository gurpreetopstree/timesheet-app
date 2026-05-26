pipeline {

    agent any

    options {
        buildDiscarder(logRotator(numToKeepStr: '10'))
        timestamps()
        timeout(time: 20, unit: 'MINUTES')
        disableConcurrentBuilds()
    }

    parameters {

        string(
            name: 'DEPLOY_DIR',
            defaultValue: '/var/www/timesheet',
            description: 'Deployment directory'
        )

        string(
            name: 'APP_USER',
            defaultValue: 'testing',
            description: 'Linux application user'
        )

        string(
            name: 'BRANCH',
            defaultValue: 'main',
            description: 'Git branch'
        )

        booleanParam(
            name: 'SKIP_TESTS',
            defaultValue: false,
            description: 'Skip tests'
        )
    }

    environment {

        SERVICE_NAME = 'timesheet'
        NGINX_SITE   = 'timesheet'
        APP_PORT     = '5000'
    }

    stages {

        // =====================================================
        // CHECKOUT
        // =====================================================

        stage('Checkout') {

            steps {

                echo "Checking out branch: ${params.BRANCH}"

                checkout([
                    $class: 'GitSCM',
                    branches: [[name: "*/${params.BRANCH}"]],
                    userRemoteConfigs: scm.userRemoteConfigs
                ])

                sh 'git log -1 --oneline'
            }
        }

        // =====================================================
        // LINT
        // =====================================================

        stage('Lint') {

            steps {

                echo "Running flake8 lint checks"

                sh '''
                    python3 -m venv .lint-venv

                    . .lint-venv/bin/activate

                    pip install --quiet flake8

                    flake8 app.py chaos_endpoints.py chaos_bot.py \
                        --max-line-length=120 \
                        --ignore=W503 \
                        --statistics \
                        --exit-zero

                    deactivate
                '''
            }
        }

        // =====================================================
        // TEST
        // =====================================================

        stage('Test') {

            when {
                expression { !params.SKIP_TESTS }
            }

            steps {

                echo "Running tests"

                sh '''
                    python3 -m venv .test-venv

                    . .test-venv/bin/activate

                    pip install --quiet -r requirements.txt pytest

                    pytest -v || true

                    deactivate
                '''
            }
        }

        // =====================================================
        // PACKAGE
        // =====================================================

        stage('Package') {

            steps {

                echo "Creating deployment package"

                sh '''
                    set +e

                    rm -f timesheet-app.tar.gz

                    tar \
                        --exclude=.git \
                        --exclude=.lint-venv \
                        --exclude=.test-venv \
                        --exclude=.pytest_cache \
                        --exclude=.coverage \
                        --exclude=htmlcov \
                        --exclude=venv \
                        --exclude=__pycache__ \
                        --exclude=*.pyc \
                        --exclude=logs \
                        --exclude=database.db \
                        --exclude=timesheet-app.tar.gz \
                        --warning=no-file-changed \
                        -czf timesheet-app.tar.gz .

                    TAR_EXIT=$?

                    set -e

                    if [ $TAR_EXIT -gt 1 ]; then
                        echo "Tar packaging failed"
                        exit $TAR_EXIT
                    fi

                    echo "Package Created Successfully"

                    du -sh timesheet-app.tar.gz
                '''
            }
        }

        // =====================================================
        // DEPLOY
        // =====================================================

        stage('Deploy') {

            steps {

                echo "Deploying application"

                sh """
                    set -eu

                    DEPLOY_DIR="${params.DEPLOY_DIR}"
                    APP_USER="${params.APP_USER}"

                    echo "[1/7] Creating directories"

                    sudo mkdir -p \$DEPLOY_DIR
                    sudo mkdir -p \$DEPLOY_DIR/persistent_data

                    echo "[2/7] Stopping application"

                    sudo systemctl stop ${env.SERVICE_NAME} || true

                    echo "[3/7] Extracting package"

                    sudo tar -xzf timesheet-app.tar.gz \
                        -C \$DEPLOY_DIR \
                        --exclude='persistent_data' \
                        --exclude='.env'

                    echo "[4/7] Installing dependencies"

                    if [ ! -d "\$DEPLOY_DIR/venv" ]; then
                        sudo python3 -m venv \$DEPLOY_DIR/venv
                    fi

                    sudo \$DEPLOY_DIR/venv/bin/pip install \
                        --quiet \
                        --upgrade pip

                    sudo \$DEPLOY_DIR/venv/bin/pip install \
                        --quiet \
                        -r \$DEPLOY_DIR/requirements.txt

                    echo "[5/7] Setting permissions"

                    sudo chown -R \$APP_USER:www-data \$DEPLOY_DIR

                    sudo chmod -R 750 \$DEPLOY_DIR

                    sudo chmod -R 770 \$DEPLOY_DIR/persistent_data

                    echo "[6/7] Restarting service"

                    sudo systemctl daemon-reload

                    sudo systemctl enable ${env.SERVICE_NAME}

                    sudo systemctl restart ${env.SERVICE_NAME}

                    sleep 5

                    sudo systemctl status ${env.SERVICE_NAME} --no-pager

                    echo "[7/7] Reloading Nginx"

                    sudo cp \$DEPLOY_DIR/DEPLOY_NGINX.conf \
                        /etc/nginx/sites-available/${env.NGINX_SITE}

                    sudo ln -sf \
                        /etc/nginx/sites-available/${env.NGINX_SITE} \
                        /etc/nginx/sites-enabled/${env.NGINX_SITE}

                    sudo nginx -t

                    sudo systemctl reload nginx

                    echo "Deployment completed successfully"
                """
            }
        }

        // =====================================================
        // HEALTH CHECK
        // =====================================================

        stage('Health Check') {

            steps {

                echo "Running health check"

                sh '''
                    for i in 1 2 3 4 5 6
                    do

                        STATUS=$(curl -s \
                            -o /dev/null \
                            -w "%{http_code}" \
                            http://localhost || true)

                        echo "Attempt $i -> HTTP $STATUS"

                        if [ "$STATUS" = "200" ] || [ "$STATUS" = "302" ]; then

                            echo "Application is healthy"

                            exit 0
                        fi

                        sleep 5

                    done

                    echo "Health check failed"

                    sudo systemctl status timesheet --no-pager || true

                    sudo journalctl -u timesheet -n 50 --no-pager || true

                    exit 1
                '''
            }
        }
    }

    // =========================================================
    // POST ACTIONS
    // =========================================================

    post {

        success {

            echo "Timesheet deployment completed successfully"
        }

        failure {

            echo "Deployment failed"
        }

        always {

            sh 'rm -f timesheet-app.tar.gz || true'

            cleanWs()
        }
    }
}
