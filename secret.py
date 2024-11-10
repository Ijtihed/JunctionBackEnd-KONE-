from google.cloud import secretmanager

PROJECT_ID = "phonic-ceremony-440214-h9"

def create_secret(secret_id):
    client = secretmanager.SecretManagerServiceClient()
    parent = f"projects/{PROJECT_ID}"
    secret = {'replication': {'automatic': {}}}
    response = client.create_secret(secret_id=secret_id, parent=parent, secret=secret)
    print(f'Created secret: {response.name}') 
    return secret_id

def add_secret_version(secret_id, payload):
    client = secretmanager.SecretManagerServiceClient()
    parent = f"projects/{PROJECT_ID}/secrets/{secret_id}"
    payload = payload.encode('UTF-8')
    response = client.add_secret_version(parent=parent, payload={'data': payload})
    print(f'Added secret version: {response.name}')   

def access_secret_version(secret_id, version_id="latest"):
    client = secretmanager.SecretManagerServiceClient()
    name = f"projects/{PROJECT_ID}/secrets/{secret_id}/versions/{version_id}"
    response = client.access_secret_version(name=name)
    return response.payload.data.decode('UTF-8')

if __name__ == "__main__":
    print("starting the process to create a new secret:\n")
    secret_id = create_secret(input("secret name: "))
    add_secret_version(secret_id, input("secret contents: "))
