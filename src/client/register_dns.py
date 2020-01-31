import requests

headers = {
    'Authorization': 'ZGJjN2ZkYjYwNWQ3ODJiOGUyMDEyMTQ2YmQ0YTJjZDcwY2ViNGUyZGRjNDZiMTRjZTBmMTc0MWZkNWU2M2Q0NTY5YmU0NTg2OGUxZjgzYzllNTBhMTllM2RiOTVlNzIxYWU2YzA0ZTYzZDViYWI2OWE0MzRlMjRiYmYyZWY3ODk='
}

resp = requests.get('https://localhost:8000', headers=headers, verify=False)

print(resp.json())
