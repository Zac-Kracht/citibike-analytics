# citibike-analytics
E2E New York City Citi Bike tracking platform including data ingestion, storage, retrieval, and hosting.


# prereqs
aws cdk (https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html)

# commands
aws login
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

nvm use 22
npx cdk deploy -c env=dev
npx cdk destroy -c env=dev


# TODO
linter
unit test
integration test
prod stack
github actions/CICD