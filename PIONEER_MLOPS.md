https://docs.pioneer.ai/guides/synthetic-data

Read this documentation.

Ask it to generate a sample dataset using the following curl requests.

curl -X POST https://api.pioneer.ai/generate \
  -H "X-API-Key: $PIONEER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "decoder",
    "dataset_name": "negotiation-agent-evals",
    "num_examples": 10,
    "domain_description": "Autonomous procurement negotiation between BuyerAgent and VendorAgent.",
    "prompt": "Generate negotiation scenarios in JSON. Each example must contain scenario_id, vendor_config, buyer_config, and expected_labels. Return only valid JSON."
  }'


Use the below format for checking status
curl https://api.pioneer.ai/generate/jobs/<JOB_ID> \
  -H "X-API-Key: $PIONEER_API_KEY"

Write a script that generates dataset and fine tunes the model when we run the script.

We need visibility into the model training and model registry of existing live models that we have used so far.

Write the data to a log file so we know what are the job ids and model ids and dataset ids.