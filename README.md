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
docker run -d -p 8000:8000 amazon/dynamodb-local
./mvnw spring-boot:run


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