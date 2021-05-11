def gcTag

//Fucntion for deploying the applciation in non-prod env
def dockerDeployNonProd(instance_ip,image_tag) {
sh ("""
ssh -tt centos@$instance_ip <<-EOF
    set -ex && \
    docker login ${DOCKER_REGISTRY} -u ${SVC_ACC} -p ${ARTIFACTORY_API_TOKEN} && \
    docker image pull ${DOCKER_REGISTRY}/gc:$image_tag && \
    docker stop ${GC_CONTAINER_NAME} && \
    docker rm -f ${GC_CONTAINER_NAME} && \
    sudo docker run -d -v /opt/ml/model/:/opt/ml/model/ -p 8080:8080 -e MODEL_SERVER_WORKERS=1 -e MODEL_SERVER_TIMEOUT=600 --name ${GC_CONTAINER_NAME} ${DOCKER_REGISTRY}/gc:$image_tag serve && \
    exit && \
EOF""")
}

//Fucnrtion for deploying the application in prod env
def dockerDeployProd(instance_ip,image_tag) {
sh """
set -o pipefail
eval `ssh-agent -s`
KEYFILE=`mktemp`
chmod 600 \${KEYFILE}
aws ssm get-parameter --name /gc/prod/gc_prod_keypair --with-decryption --region us-east-1 \
    --query Parameter.Value --output text >  \${KEYFILE}
ssh-add \${KEYFILE}
rm \${KEYFILE}
IP=`aws ssm get-parameter --name $instance_ip --with-decryption --region us-east-1 --query Parameter.Value --output text`
ssh -o StrictHostKeyChecking=no centos@\${IP} '''
    set -ex;
    docker login ${DOCKER_REGISTRY} -u ${SVC_ACC} -p ${ARTIFACTORY_API_TOKEN};
    docker image pull ${DOCKER_REGISTRY}/gc:$image_tag;
    docker stop ${GC_CONTAINER_NAME};
    docker rm -f ${GC_CONTAINER_NAME};
    sudo docker run -d -v /opt/ml/model/:/opt/ml/model/ -p 8080:8080 -e MODEL_SERVER_WORKERS=1 -e MODEL_SERVER_TIMEOUT=600 --name ${GC_CONTAINER_NAME} ${DOCKER_REGISTRY}/gc:$image_tag serve;
'''
eval `ssh-agent -k`
"""
}

// Fucntion for updating the AWS SSM paramter store
def updateSSM(name,value) {
  sh """
  aws ssm put-parameter --name $name --value $value --type SecureString --overwrite --region us-east-1
  """
}

// Fucntion to login, pull , tag and pushing of the docker image
def dockerTagAndPush(pullFrom,pushTo) {
  script {
  docker.withRegistry("https://${DOCKER_REGISTRY}/", "${ARTIFACTORY_CREDENTIAL}") {
                        gcTag = docker.image("${IMAGE_NAME}:$pullFrom")
                        gcTag.pull()
                        gcTag.push("$pushTo")
                        }
  }
}

// Fucntion to run integration tests
def integrationTest(testFile,testType,environment) {
  sh """
    cd test
    bash $testFile $testType $environment
    """
}

// Parity global library for shared groovy fucntions
@Library('parityGlobalLibrary@1.8.0') _
pipeline {
    agent {
        label 'gc-packer-agent'
    }

  environment {
    MAJOR                     = '3'
    MINOR                     = '0'
    VERSION                   = "v${MAJOR}.${MINOR}.${BUILD_NUMBER}"
    WORKSPACE                 = "${env.WORKSPACE}"
    BUILD_TS                  = "${GIT_COMMIT}"
    SVC_ACC                   = credentials('svc_account_name')
    ARTIFACTORY_API_TOKEN     = credentials('artifactory_api_token')
    SONAR_SCANNER_TOKEN       = credentials('sonar_api_token')
    DOCKER_REGISTRY           = "docker-genericlass-parity-local.rt.artifactory.tio.systems"
    IMAGE_ID                  = "gc"
    IMAGE_NAME                = "${DOCKER_REGISTRY}/${IMAGE_ID}"
    IMAGE_TAG_DEV             = "${VERSION}-${BUILD_TS}-dev"
    IMAGE_TAG_UAT             = "${VERSION}-${BUILD_TS}-uat"
    IMAGE_TAG_UAT_GOLDEN      = "${VERSION}-${BUILD_TS}-uat-golden"
    IMAGE_TAG_PROD            = "${VERSION}-${BUILD_TS}-prod"
    IMAGE_TAG_PROD_GOLDEN     = "${VERSION}-${BUILD_TS}-prod-golden"
    ARTIFACTORY_CREDENTIAL    = "artifactory_svc_credential"
    GC_CONTAINER_NAME         = "gc"
    DOCKER_TAG                = "${VERSION}.${GIT_BRANCH}.${GIT_COMMIT}"
    SSM_STORE_DEV             = '/gc/dev/gc_latest_dockerTag'
    SSM_STORE_UAT             = '/gc/uat/gc_latest_dockerTag'
    SSM_STORE_UAT_GOLDEN      = '/gc/uat/gc_golden_dockerTag'
    SSM_STORE_PROD            = '/gc/prod/gc_latest_dockerTag'
    SSM_STORE_PROD_GOLDEN     = '/gc/prod/gc_golden_dockerTag'
    PROD_ACCOUNT_ID           = '723926235764'
    PROD_CROSS_ACCOUNT_ROLE   = 'mhub-platform-prod-ip-build-agent-role'
    PROD_ROLE_ARN             = "arn:aws:iam::${PROD_ACCOUNT_ID}:role/${PROD_CROSS_ACCOUNT_ROLE}"
    PROD_ROLE_SESSION         = "jenkins"
}

  stages {

    stage('Lint'){
        steps {
            script {
                try {
                    slackSend (color: "#FFFF00", channel: '#electron_gc_squad_ci', message: "STARTED Lint. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                    sh '''
                    cd ${WORKSPACE}
                    pylint-fail-under --fail_under 7 classifyGenericModified.py \
                    container/predictor.py \
                    container/serve \
                    container/wsgi.py \
                    model.py \
                    test/config.py \
                    test/conftest.py \
                    test/pytest.ini \
                    test/settings.py \
                    test/integration/tests_gc/base_test.py \
                    test/integration/tests_gc/tests_batches.py  \
                    test/integration/tests_gc/tests_end_points.py  \
                    test/integration/tests_gc/tests_functionality.py  \
                    test/integration/tests_gc/tests_lb_asyncio.py  \
                    test/integration/tests_gc/tests_lb_threads.py  \
                    test/integration/tests_gc/tests_recurring.py  > ${WORKSPACE}/report-task.txt
                    '''
                } catch (e)     {
                    slackSend (color: "danger", channel: '#electron_gc_squad_ci', message: "FAILED Lint. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                    throw e
                } 
                slackSend (color: "good", channel: '#electron_gc_squad_ci', message: "COMPLETED Lint. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
            }
        }        
    }

    stage('Performing Unit Testing'){
      steps {
          script {
                try {
             slackSend (color: "#FFFF00",channel: '#electron_gc_squad_ci', message: "STARTED Unit Testing. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
            sh '''
            export PYTHONPATH=\${WORKSPACE}/container:$PYTHONPATH
            cd ${WORKSPACE}/unit_tests
            coverage run -a --source=../.. -m pytest -v -m unit_tests
            coverage xml -o coverage.xml
            coverage xml -i
            cp coverage.xml ../
            cd ../
            '''} catch (e)     {
                    slackSend (color: "danger",channel: '#electron_gc_squad_ci', message: "FAILED Unit Testing. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                    throw e 
                }
             slackSend (color: "good",channel: '#electron_gc_squad_ci', message: "COMPLETED Unit Testing. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")   
        }
      }
    }

    stage('Performing Sonar Analysis'){
      steps {
          script {
                try {
        slackSend (color: "#FFFF00", channel: '#electron_gc_squad_ci', message: "STARTED Sonar Analysis. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
        def scannerHome = tool 'sonarScannerElsevier';
        withSonarQubeEnv('sonarqube') {
        sh """
        ${scannerHome}/bin/sonar-scanner \
        -Dsonar.projectKey=gc \
        -Dsonar.projectName=gc \
        -Dsonar.language=py \
        -Dsonar.branch.name=$BRANCH_NAME \
        -Dsonar.login=$SONAR_SCANNER_TOKEN \
        -Dsonar.projectVersion=1.0 \
        -Dsonar.scm.disabled=true \
        -Dsonar.verbose=false \
        -Dsonar.log.level=INFO \
        -Dsonar.projectBaseDir="${WORKSPACE}" \
        -Dsonar.sources=classifyGenericModified.py,model.py,container,test,unit_tests \
        -Dsonar.host.url=https://sq.prod.tio.elsevier.systems \
        -Dsonar.sourceEncoding=UTF-8 \
        -Dsonar.exclusions=data/**,dicts/**,model/**,notebooks/**,scripts/**,test/**,unit_tests/** \
        -Dsonar.python.pylint.reportPath="${WORKSPACE}/report-task.txt" \
        -Dsonar.python.coverage.reportPaths="${WORKSPACE}/coverage.xml"
        """
         }
            } catch (e)     {
                slackSend (color: "danger",channel: '#electron_gc_squad_ci', message: "FAILED Sonar Analysis. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                throw e 
            }
        slackSend (color: "good",channel: '#electron_gc_squad_ci', message: "COMPLETED Sonar Analysis. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
          }
        }
     }

     stage('Docker build'){
        steps {
            script {
                try {
                    slackSend (color: "#FFFF00", channel: '#electron_gc_squad_ci', message: "STARTED Docker build. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                    script {
                        gcTag = docker.build("${IMAGE_NAME}:build-${BUILD_NUMBER}")
                        }
                } catch (e)     {
                    slackSend (color: "danger",channel: '#electron_gc_squad_ci', message: "FAILED Docker build. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                    throw e
                } 
                slackSend (color: "good", channel: '#electron_gc_squad_ci', message: "COMPLETED Docker build. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
            }
        }        
    }

    stage('Docker tag and push in master branch') {
        when {
            branch 'master'
        }
       steps {
         script {
                try {
                    slackSend (color: "#FFFF00", channel: '#electron_gc_squad_ci', message: "STARTED Docker push. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                    docker.withRegistry("https://${DOCKER_REGISTRY}/", "${ARTIFACTORY_CREDENTIAL}") {
                        gcTag.push("${IMAGE_TAG_DEV}")
                    }
                    echo "Updating tag value in SSM parameter store"
                    updateSSM('${SSM_STORE_DEV}','${IMAGE_TAG_DEV}')
                } catch (e)     {
                   slackSend (color: "danger",channel: '#electron_gc_squad_ci', message: "FAILED Docker push. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                   throw e
                }
                slackSend (color: "good", channel: '#electron_gc_squad_ci', message: "COMPLETED Docker push. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                }
            }
    }
    
    
    stage('Cleanup') {
      steps {
        echo "Cleanup: Cleaning up the dangling docker images"
        sh '''
          docker image rm -f $(docker images --filter=reference="${IMAGE_NAME}:build-${BUILD_NUMBER}" --format "{{.ID}}" | head -1)
        '''
      }
    }

    stage('Deploy to Pre-UAT 1') {
      options {
        timeout(time: 30, unit: 'MINUTES')
      }
      when {
            branch 'master'
        }
      steps {
        script {
            try {
                input message: 'Deploy to Dev environment 1?'
                echo 'Deploying to Dev environment...'
                slackSend (color: "#FFFF00", channel: '#electron_gc_squad_ci', message: "STARTED Deploy to Pre-UAT 1. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                 script {
                     String ip = pemKeyPushForSsh('id_rsa', '/gc/dev/gc_dev_keypair', '/gc/dev/gc_1a_ip', 'us-east-1', 'centos')
                     dockerDeployNonProd(ip,'${IMAGE_TAG_DEV}')
                 }
            } catch (e)     {
                   slackSend (color: "danger",channel: '#electron_gc_squad_ci', message: "FAILED Deploy to Pre-UAT 1. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                   throw e
            }
            slackSend (color: "good", channel: '#electron_gc_squad_ci', message: "COMPLETED Deploy to Pre-UAT 1. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")            
        }
      }     
    }

      stage('Deploy to Pre-UAT 2') {
      options {
        timeout(time: 30, unit: 'MINUTES')
      }
      when {
            branch 'master'
        }
      steps {
        script {
            try {
                slackSend (color: "#FFFF00", channel: '#electron_gc_squad_ci', message: "STARTED Deploy to Pre-UAT 2. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                script {
                    String ip = pemKeyPushForSsh('id_rsa', '/gc/dev/gc_dev_keypair', '/gc/dev/gc_1b_ip', 'us-east-1', 'centos')
                    dockerDeployNonProd(ip,'${IMAGE_TAG_DEV}')
                }
            } catch (e)     {
                   slackSend (color: "danger",channel: '#electron_gc_squad_ci', message: "FAILED Deploy to Pre-UAT 2. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                   throw e
            }
            slackSend (color: "good", channel: '#electron_gc_squad_ci', message: "COMPLETED Deploy to Pre-UAT 2. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")            
        }
      }     
    }
  
    stage('Perform Smoke Testing after deploy to Dev') {
      when {
            branch 'master'
      }
      steps {
        retry(3) {
          script {
            try {
                slackSend (color: "#FFFF00", channel: '#electron_gc_squad_ci', message: "STARTED Smoke Testing. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                script {
                    sh 'sleep 60'
                    integrationTest('./run_tests_jenkins.sh','smoke_tests','dev')
                }
            } catch (e)     {
                   slackSend (color: "danger",channel: '#electron_gc_squad_ci', message: "FAILED Smoke Testing. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                   throw e
            }
            slackSend (color: "good", channel: '#electron_gc_squad_ci', message: "COMPLETED Smoke Testing. Job '${env.JOB_NAME} ${env.BUILD_NUMBER} ${env.BUILD_URL}'")            
          }
        } 
      }
    }
    
    stage('Perform Regression Testing after deploy to Dev') {
      when {
         branch 'master'
      }
      steps {
        script {
            try {
                slackSend (color: "#FFFF00", channel: '#electron_gc_squad_ci', message: "STARTED Regression Testing. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                script {
                    integrationTest('./run_tests_jenkins.sh','regression','dev')
                }
            } catch (e)     {
                   slackSend (color: "danger",channel: '#electron_gc_squad_ci', message: "FAILED Regression Testing. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                   throw e
            }
            slackSend (color: "good", channel: '#electron_gc_squad_ci', message: "COMPLETED Regression Testing. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")            
        }
      }
      post {
        always {
          junit 'test/*dev_reports.xml'
          script {
            sh '''
              cd test
              for i in *;do if [[ $i == *.txt || $i == *.csv ]]; then curl -u ${SVC_ACC}:${ARTIFACTORY_API_TOKEN} -X PUT "https://rt.artifactory.tio.systems/artifactory/docker-genericlass-parity-local/gc_reports/dev/${BUILD_NUMBER}/" -T $i;fi;done;
              rm ${WORKSPACE}/test/*.csv || true
              rm ${WORKSPACE}/test/*.log || true
            '''
          }
        }
      }     
    }

    stage('Docker re-tag and push image before UAT') {
        when {
            branch 'master'
        }
       steps {
         script {
                try {
                  slackSend (color: "#FFFF00", channel: '#electron_gc_squad_ci', message: "STARTED Docker push. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                    dockerTagAndPush("${IMAGE_TAG_DEV}","${IMAGE_TAG_UAT}")
                    echo "Updating UAT tag value in SSM parameter store"
                    updateSSM('${SSM_STORE_UAT}','${IMAGE_TAG_UAT}')
                } catch (e)     {
                   slackSend (color: "danger",channel: '#electron_gc_squad_ci', message: "FAILED Docker push. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                   throw e
                }
                slackSend (color: "good", channel: '#electron_gc_squad_ci', message: "COMPLETED Docker push. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                }
            }
    }

    stage('Deploy to UAT 1') {
      options {
        timeout(time: 30, unit: 'MINUTES')
      }
      when {
            branch 'master'
        }
      steps {
        script {
            try {
                input message: 'Deploy to UAT environment 1?'
                echo 'Deploying to UAT environment...'
                slackSend (color: "#FFFF00", channel: '#electron_gc_squad_ci', message: "STARTED Deploy to UAT 1. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                script {
                    String ip = pemKeyPushForSsh('id_rsa', '/gc/uat/gc_uat_keypair', '/gc/uat/gc_1a_ip', 'us-east-1', 'centos')
                    dockerDeployNonProd(ip,'${IMAGE_TAG_UAT}')
                }
            } catch (e)     {
                   slackSend (color: "danger",channel: '#electron_gc_squad_ci', message: "FAILED Deploy to UAT 1. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                   throw e
            }
            slackSend (color: "good", channel: '#electron_gc_squad_ci', message: "COMPLETED Deploy to UAT 1. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")            
        }
      }     
    }

      stage('Deploy to UAT 2') {
      options {
        timeout(time: 30, unit: 'MINUTES')
      }
      when {
            branch 'master'
        }
      steps {
        script {
            try {
                slackSend (color: "#FFFF00", channel: '#electron_gc_squad_ci', message: "STARTED Deploy to UAT 2. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                script {
                    String ip = pemKeyPushForSsh('id_rsa', '/gc/uat/gc_uat_keypair', '/gc/uat/gc_1b_ip', 'us-east-1', 'centos')
                    dockerDeployNonProd(ip,'${IMAGE_TAG_UAT}')
                }
            } catch (e)     {
                   slackSend (color: "danger",channel: '#electron_gc_squad_ci', message: "FAILED Deploy to UAT 2. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                   throw e
            }
            slackSend (color: "good", channel: '#electron_gc_squad_ci', message: "COMPLETED Deploy to UAT 2. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")            
        }
      }     
    }

    stage('Perform Smoke Testing after deploy to UAT') {
      when {
            branch 'master'
      }
      steps {
        retry(3) {
          script {
            try {
                slackSend (color: "#FFFF00", channel: '#electron_gc_squad_ci', message: "STARTED Smoke Testing. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                script {
                   sh 'sleep 60'
                   integrationTest('./run_tests_jenkins.sh','smoke_tests','uat')
                }
            } catch (e)     {
                   slackSend (color: "danger",channel: '#electron_gc_squad_ci', message: "FAILED Smoke Testing. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                   throw e
            }
            slackSend (color: "good", channel: '#electron_gc_squad_ci', message: "COMPLETED Smoke Testing. Job '${env.JOB_NAME} ${env.BUILD_NUMBER} ${env.BUILD_URL}'")            
          }
        } 
      }
    }
    
    stage('Perform Regression Testing after deploy to UAT') {
      when {
         branch 'master'
      }
      steps {
        script {
            try {
                slackSend (color: "#FFFF00", channel: '#electron_gc_squad_ci', message: "STARTED Regression Testing. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                script {
                   integrationTest('./run_tests_jenkins.sh','regression','uat')
                }
            } catch (e)     {
                   slackSend (color: "danger",channel: '#electron_gc_squad_ci', message: "FAILED Regression Testing. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                   throw e
            }
            slackSend (color: "good", channel: '#electron_gc_squad_ci', message: "COMPLETED Regression Testing. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")            
        }
      }
      post {
        always {
          junit 'test/*uat_reports.xml'
          script {
            sh '''
              cd test
              for i in *;do if [[ $i == *.txt || $i == *.csv ]]; then curl -u ${SVC_ACC}:${ARTIFACTORY_API_TOKEN} -X PUT "https://rt.artifactory.tio.systems/artifactory/docker-genericlass-parity-local/gc_reports/uat/${BUILD_NUMBER}/" -T $i;fi;done;
              rm ${WORKSPACE}/test/*.csv || true
              rm ${WORKSPACE}/test/*.log || true
            '''
          }
        }
      }     
    }

    stage('Tag as Golden UAT Image') {
      options {
        timeout(time: 3, unit: 'DAYS')
      }
      when {
            branch 'master'
      }
      steps {
        script {
            try {
                input message: 'Tag as Golden UAT Image?'
                echo 'Tagging as Golden UAT Image...'
                slackSend (color: "#FFFF00", channel: '#electron_gc_squad_ci', message: "STARTED Tag as Golden UAT Image. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                dockerTagAndPush("${IMAGE_TAG_UAT}","${IMAGE_TAG_UAT_GOLDEN}")
                updateSSM('${SSM_STORE_UAT_GOLDEN}','${IMAGE_TAG_UAT_GOLDEN}')
            } catch (e)     {
                   slackSend (color: "danger",channel: '#electron_gc_squad_ci', message: "FAILED Tag as Golden UAT Image. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                   throw e
            }
            slackSend (color: "good", channel: '#electron_gc_squad_ci', message: "COMPLETED Tag as Golden UAT Image. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")            
        }
      }     
    }

  stage('Deploy to PROD 1') {
      options {
        timeout(time: 30, unit: 'MINUTES')
      }
      when {
            branch 'master'
      }
      steps {
        script {
            try {
                input message: 'Deploy to PROD environment 1?'
                echo 'Deploying to PROD environment...'
                slackSend (color: "#FFFF00", channel: '#electron_gc_squad_ci', message: "STARTED Deploy to PROD 1. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                    dockerTagAndPush("${IMAGE_TAG_UAT_GOLDEN}","${IMAGE_TAG_PROD}")
                    withAWS(roleAccount: "$PROD_ACCOUNT_ID", role:"$PROD_CROSS_ACCOUNT_ROLE") {
                        dockerDeployProd("/gc/prod/gc_1a_ip","${IMAGE_TAG_PROD}")
                        updateSSM('${SSM_STORE_PROD}','${IMAGE_TAG_PROD}')
                    }
            } catch (e)     {
                   slackSend (color: "danger",channel: '#electron_gc_squad_ci', message: "FAILED Deploy to PROD 1. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                   throw e
            }
            slackSend (color: "good", channel: '#electron_gc_squad_ci', message: "COMPLETED Deploy to PROD 1. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")            
        }
      }     
    }

    stage('Deploy to PROD 2') {
      options {
        timeout(time: 30, unit: 'MINUTES')
      }
      when {
            branch 'master'
      }
      steps {
        script {
            try {
                slackSend (color: "#FFFF00", channel: '#electron_gc_squad_ci', message: "STARTED Deploy to PROD 2. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")                    
                    withAWS(roleAccount: "$PROD_ACCOUNT_ID", role:"$PROD_CROSS_ACCOUNT_ROLE") {
                        dockerDeployProd("/gc/prod/gc_1b_ip","${IMAGE_TAG_PROD}")
                    }
            } catch (e)     {
                   slackSend (color: "danger",channel: '#electron_gc_squad_ci', message: "FAILED Deploy to PROD 2. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                   throw e
            }
            slackSend (color: "good", channel: '#electron_gc_squad_ci', message: "COMPLETED Deploy to PROD 2. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")            
        }
      }     
    }

    stage('Perform Smoke Testing after deploy to PROD') {
      when {
            branch 'master'
      }
      steps {
        retry(3) {
            script {
            try {
                slackSend (color: "#FFFF00", channel: '#electron_gc_squad_ci', message: "STARTED Smoke Testing. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                script {
                    sh 'sleep 60'
                    integrationTest('./run_tests_jenkins.sh','smoke_tests','prod')
                }
            } catch (e)     {
                   slackSend (color: "danger",channel: '#electron_gc_squad_ci', message: "FAILED Smoke Testing. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                   throw e
            }
            slackSend (color: "good", channel: '#electron_gc_squad_ci', message: "COMPLETED Smoke Testing. Job '${env.JOB_NAME} ${env.BUILD_NUMBER} ${env.BUILD_URL}'")            
          }
        }
      }
    }

    stage('Perform Regression Testing after deploy to PROD') {
      when {
            branch 'master'
      }
      steps {
        script {
            try {
                slackSend (color: "#FFFF00", channel: '#electron_gc_squad_ci', message: "STARTED Regression Testing. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                script {
                    integrationTest('./run_tests_jenkins.sh','regression','prod')
                }
            } catch (e)     {
                   slackSend (color: "danger",channel: '#electron_gc_squad_ci', message: "FAILED Regression Testing. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                   throw e
            }
            slackSend (color: "good", channel: '#electron_gc_squad_ci', message: "COMPLETED Regression Testing. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")            
        }
      }
      post {
        always {
          junit 'test/*prod_reports.xml'
          script {
            sh '''
              cd test
              for i in *;do if [[ $i == *.txt || $i == *.csv ]]; then curl -u ${SVC_ACC}:${ARTIFACTORY_API_TOKEN} -X PUT "https://rt.artifactory.tio.systems/artifactory/docker-genericlass-parity-local/gc_reports/prod/${BUILD_NUMBER}/" -T $i;fi;done;
              rm ${WORKSPACE}/test/*.csv || true
              rm ${WORKSPACE}/test/*.log || true
            '''
          }
        }
      }     
    }

    stage('Tag as Golden PROD Image') {
      options {
        timeout(time: 3, unit: 'DAYS')
      }
      when {
            branch 'master'
      }
      steps {
        script {
            try {
                input message: 'Tag as Golden PROD Image?'
                echo 'Tagging as Golden PROD Image...'
                slackSend (color: "#FFFF00", channel: '#electron_gc_squad_ci', message: "STARTED Tag as Golden PROD Image. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                    dockerTagAndPush("${IMAGE_TAG_PROD}","${IMAGE_TAG_PROD_GOLDEN}") 
                withAWS(roleAccount: "$PROD_ACCOUNT_ID", role:"$PROD_CROSS_ACCOUNT_ROLE") {
                    updateSSM('${SSM_STORE_PROD_GOLDEN}','${IMAGE_TAG_PROD_GOLDEN}')
            }
            } catch (e)     {
                   slackSend (color: "danger",channel: '#electron_gc_squad_ci', message: "FAILED Tag as Golden PROD Image. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")
                   throw e
            }
            slackSend (color: "good", channel: '#electron_gc_squad_ci', message: "COMPLETED Tag as Golden PROD Image. Job '${env.JOB_NAME} [${env.BUILD_NUMBER}]' (${env.BUILD_URL}")            
        }
      }     
    }

    }
  }