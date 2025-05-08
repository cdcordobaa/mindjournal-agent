import boto3

# Create a client
s3 = boto3.client('s3')

# List your buckets
response = s3.list_buckets()

# Print bucket names
print('Existing buckets:')
for bucket in response['Buckets']:
    print(f'  {bucket["Name"]}')