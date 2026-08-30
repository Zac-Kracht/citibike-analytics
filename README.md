# citibike-analytics
E2E New York City Citi Bike tracking platform including data ingestion, storage, retrieval, and hosting.


# prereqs
aws cdk (https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)

# commands

# Python env
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# CDK Deploy
nvm use 22
aws login
npx cdk deploy -c env=dev
npx cdk destroy -c env=dev

for docker error:
sudo usermod -aG docker $USER
newgrp docker

for loggroup error:
aws logs delete-log-group --log-group-name /aws/lambda/citibike-ingestion-lambda-dev

# Local run/test API
./mvnw clean compile
./mvnw spring-boot:run
./mvnw clean test

docker rm -f dynamodb-local

docker run -d \
  --name dynamodb-local \
  -p 8000:8000 \
  amazon/dynamodb-local \
  -jar DynamoDBLocal.jar -inMemory -sharedDb

aws dynamodb create-table \
    --table-name citibike-station-status-local \
    --attribute-definitions AttributeName=station_id,AttributeType=S \
    --key-schema AttributeName=station_id,KeyType=HASH \
    --billing-mode PAY_PER_REQUEST \
    --endpoint-url http://localhost:8000 \
    --region us-east-1

aws dynamodb list-tables \
    --endpoint-url http://localhost:8000 \
    --region us-east-1

aws dynamodb put-item \
    --table-name citibike-station-status-local \
    --item '{
        "station_id": {"S": "66dbf21d-0e22-4a0f-90e6-123456789abc"},
        "station_name": {"S": "W 21 St & 6 Ave"},
        "short_name": {"S": "6140.05"},
        "num_bikes_available": {"N": "14"},
        "num_ebikes_available": {"N": "3"},
        "num_docks_available": {"N": "22"},
        "is_installed": {"BOOL": true},
        "is_renting": {"BOOL": true},
        "is_returning": {"BOOL": true},
        "latitude": {"N": "40.741721"},
        "longitude": {"N": "-73.994156"},
        "capacity": {"N": "39"},
        "info_last_updated": {"N": "1724095349"},
        "status_last_updated": {"N": "1724095349"}
    }' \
    --endpoint-url http://localhost:8000 \
    --region us-east-1

# Ping dev API locally:
export BASTION_INSTANCE_ID=$(aws ec2 describe-instances \
  --filters "Name=instance-state-name,Values=running" \
  --query "Reservations[*].Instances[?contains(Tags[?Key=='Name'].Value | [0], 'Bastion') || contains(Tags[?Key=='Name'].Value | [0], 'bastion')].InstanceId" \
  --output text | awk '{print $1}')

export INTERNAL_ALB_DNS_NAME=$(aws elbv2 describe-load-balancers \
  --query "LoadBalancers[?Scheme=='internal'].DNSName" \
  --output text | awk '{print $1}')

aws ssm start-session \
  --target "$BASTION_INSTANCE_ID" \
  --document-name AWS-StartPortForwardingSessionToRemoteHost \
  --parameters '{"host":["'$INTERNAL_ALB_DNS_NAME'"],"portNumber":["80"],"localPortNumber":["8080"]}'

curl http://localhost:8080/api/v1/stations

# Push prod docker image
prod docker:
aws ecr get-login-password --region <YOUR_REGION> | docker login --username AWS --password-stdin <YOUR_ACCOUNT_ID>.dkr.ecr.<YOUR_REGION>.amazonaws.com
docker build -t citibike-backend-api .
docker tag citibike-backend-api:latest <YOUR_ACCOUNT_ID>.dkr.ecr.<YOUR_REGION>.amazonaws.com/citibike-backend-api:latest
docker push <YOUR_ACCOUNT_ID>.dkr.ecr.<YOUR_REGION>.amazonaws.com/citibike-backend-api:latest

# Run frontend
nvm use 22
nvm alias default 22
npm install
npm run dev

# TODO
disabled docks/bikes (caution icon)
dynamoV2 migration
Make sure S3 lifecycle rules minimize cost
create origin secret in prod
linter
unit test
integration test
prod stack
github actions/CICD
claude file?
documentations/readme's
code comments
alerts about failed jobs
alarms
check for cyber threats
vulnerability management
makefiles
multi language support
front end accessibility
monetize/ads
