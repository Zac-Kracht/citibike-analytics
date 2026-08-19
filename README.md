# citibike-analytics
E2E New York City Citi Bike tracking platform including data ingestion, storage, retrieval, and hosting.


# prereqs
aws cdk (https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)

# commands
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

nvm use 22
aws login
export DEV_ALLOWED_CIDR=$(curl -s https://checkip.amazonaws.com)/32
npx cdk deploy -c env=dev
npx cdk destroy -c env=dev

./mvnw clean compile
./mvnw spring-boot:run

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


# TODO
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
Show users where they can return bike if station is full
Show users where that can get a bike if station is full