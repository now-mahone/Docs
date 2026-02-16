#!/usr/bin/env python3
# Created: 2026-02-12
"""Test RunPod API to discover correct endpoints"""

import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("RUNPOD_API_KEY")

print(f"API Key: {API_KEY[:10]}...")

# Test different endpoints
endpoints = [
    ("GET", "https://api.runpod.io/v2/gpu-types", {}),
    ("GET", "https://api.runpod.io/v2/pods", {}),
    ("POST", "https://api.runpod.io/graphql", {"query": "{ gpuTypes { id displayName } }"}),
]

headers_auth = {"Authorization": f"Bearer {API_KEY}"}

for method, url, data in endpoints:
    print(f"\n{'='*60}")
    print(f"Testing: {method} {url}")
    
    if method == "GET":
        # Try with header auth
        resp = requests.get(url, headers=headers_auth)
        print(f"  With Bearer header: {resp.status_code}")
        if resp.status_code == 200:
            print(f"  Response: {resp.text[:500]}")
        
        # Try with query param
        resp = requests.get(f"{url}?api_key={API_KEY}")
        print(f"  With api_key param: {resp.status_code}")
        if resp.status_code == 200:
            print(f"  Response: {resp.text[:500]}")
    else:
        resp = requests.post(url, headers={**headers_auth, "Content-Type": "application/json"}, json=data)
        print(f"  With Bearer header: {resp.status_code}")
        print(f"  Response: {resp.text[:500]}")

print("\n" + "="*60)
print("Testing RunPod REST API v2...")

# Try the pods endpoint with different auth methods
url = "https://api.runpod.io/v2/pods"
resp = requests.get(url, headers={"Authorization": f"Bearer {API_KEY}"})
print(f"GET /pods with Bearer: {resp.status_code} - {resp.text[:200]}")

# Try GraphQL endpoint
print("\nTrying GraphQL endpoint...")
url = "https://api.runpod.io/graphql"
query = {"query": "query { myself { id email } }"}
resp = requests.post(url, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, json=query)
print(f"GraphQL myself: {resp.status_code} - {resp.text[:200]}")

# Try getting pods via GraphQL
query = {"query": "query { pods { id name runtime { status } } }"}
resp = requests.post(url, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, json=query)
print(f"GraphQL pods: {resp.status_code} - {resp.text[:500]}")

# Discover the GraphQL schema
print("\n" + "="*60)
print("Discovering GraphQL schema...")

# Get all mutations
introspection = {
    "query": """
    query IntrospectionQuery {
        __schema {
            mutationType {
                fields {
                    name
                    args {
                        name
                        type {
                            name
                            kind
                        }
                    }
                }
            }
        }
    }
    """
}
resp = requests.post(url, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, json=introspection)
print(f"Mutations: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    mutations = data.get("data", {}).get("__schema", {}).get("mutationType", {}).get("fields", [])
    print("\nAvailable mutations:")
    for m in mutations[:20]:
        print(f"  - {m['name']}")
        if "pod" in m['name'].lower() or "create" in m['name'].lower():
            print(f"    Args: {[a['name'] for a in m.get('args', [])]}")

# Try to find pod-related queries
introspection2 = {
    "query": """
    query {
        __schema {
            queryType {
                fields {
                    name
                }
            }
        }
    }
    """
}
resp = requests.post(url, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, json=introspection2)
if resp.status_code == 200:
    data = resp.json()
    queries = data.get("data", {}).get("__schema", {}).get("queryType", {}).get("fields", [])
    print("\nAvailable queries (pod-related):")
    for q in queries:
        if "pod" in q['name'].lower() or "pool" in q['name'].lower():
            print(f"  - {q['name']}")

# Try pools query
print("\n" + "="*60)
print("Testing pools query...")
query = {"query": "query { pools { id name } }"}
resp = requests.post(url, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, json=query)
print(f"Pools: {resp.status_code} - {resp.text[:500]}")

# Try pod query with specific ID pattern
print("\nTrying pod query...")
query = {"query": "query { pod(id: \"test\") { id name } }"}
resp = requests.post(url, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, json=query)
print(f"Pod: {resp.status_code} - {resp.text[:500]}")

# Try to list all my pods/pools
print("\nTrying to list my resources...")
query = {"query": "query { myself { id email } }"}
resp = requests.post(url, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, json=query)
print(f"Myself: {resp.text}")

# Check for serverless endpoints
print("\n" + "="*60)
print("Checking for serverless endpoint creation...")
# RunPod uses "endpoints" for serverless GPU deployments
query = {"query": "query { endpoints { id name } }"}
resp = requests.post(url, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, json=query)
print(f"Endpoints: {resp.status_code} - {resp.text[:500]}")

# Try to find what queries we CAN access
print("\n" + "="*60)
print("Finding accessible queries...")
query = {"query": "query { __type(name: \"Query\") { fields { name description } } }"}
resp = requests.post(url, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, json=query)
print(f"Query fields: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    fields = data.get("data", {}).get("__type", {}).get("fields", [])
    print("\nAll available queries:")
    for f in fields:
        print(f"  - {f['name']}")

# Try to find what mutations we CAN access
print("\n" + "="*60)
print("Finding accessible mutations...")
query = {"query": "query { __type(name: \"Mutation\") { fields { name description } } }"}
resp = requests.post(url, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, json=query)
print(f"Mutation fields: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    fields = data.get("data", {}).get("__type", {}).get("fields", [])
    print("\nAll available mutations:")
    for f in fields:
        print(f"  - {f['name']}")

# Try creating a template (might work with current permissions)
print("\n" + "="*60)
print("Testing template creation...")
query = {
    "query": """
    mutation {
        saveTemplate(input: {
            name: "kerne-test"
            imageName: "runpod/pytorch:2.1.0-py3.10-cuda12.1.1-devel-ubuntu22.04"
            containerDiskInGb: 100
            volumeInGb: 50
            dockerArgs: ""
            env: []
        }) {
            id
            name
        }
    }
    """
}
resp = requests.post(url, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, json=query)
print(f"Save template: {resp.status_code} - {resp.text[:500]}")

# Try REST API for pod creation
print("\n" + "="*60)
print("Testing REST API for pod creation...")
rest_url = "https://api.runpod.io/v2/pods"
payload = {
    "name": "kerne-test-pod",
    "imageName": "runpod/pytorch:2.1.0-py3.10-cuda12.1.1-devel-ubuntu22.04",
    "gpuTypeId": "NVIDIA GeForce RTX 4090",
    "gpuCount": 1,
    "containerDiskInGb": 100,
    "minMemoryInGb": 24,
    "minVcpuCount": 4,
    "env": [{"key": "HF_TOKEN", "value": os.getenv("HF_TOKEN", "")}],
    "ports": "8000/http",
    "volumeInGb": 50,
    "volumeMountPath": "/models",
}
resp = requests.post(rest_url, headers={"Authorization": f"Bearer {API_KEY}"}, json=payload)
print(f"REST pod create: {resp.status_code} - {resp.text[:500]}")

# Try with api_key in URL
resp = requests.post(f"{rest_url}?api_key={API_KEY}", json=payload)
print(f"REST pod create (api_key param): {resp.status_code} - {resp.text[:500]}")

# Try the v1 endpoint
print("\nTrying v1 endpoint...")
rest_url_v1 = "https://api.runpod.io/v1/pods"
resp = requests.post(f"{rest_url_v1}?api_key={API_KEY}", json=payload)
print(f"REST v1 pod create: {resp.status_code} - {resp.text[:500]}")

# Try serverless endpoint creation
print("\n" + "="*60)
print("Testing serverless endpoint creation...")
serverless_url = "https://api.runpod.io/v2/endpoints"
serverless_payload = {
    "name": "kerne-inference",
    "imageName": "runpod/pytorch:2.1.0-py3.10-cuda12.1.1-devel-ubuntu22.04",
    "gpuTypeId": "NVIDIA GeForce RTX 4090",
    "workersMin": 1,
    "workersMax": 3,
    "env": {"HF_TOKEN": os.getenv("HF_TOKEN", "")},
}
resp = requests.post(f"{serverless_url}?api_key={API_KEY}", json=serverless_payload)
print(f"Serverless endpoint: {resp.status_code} - {resp.text[:500]}")

# Try GraphQL mutations for pod creation using template
print("\n" + "="*60)
print("Testing GraphQL pod creation with template...")
# First, let's try to find the correct mutation
query = {
    "query": """
    mutation {
        podResume(input: {
            templateId: "q46vbbktiy"
            gpuCount: 1
            gpuTypeId: "NVIDIA GeForce RTX 4090"
        }) {
            id
            name
            runtime {
                status
            }
        }
    }
    """
}
resp = requests.post(url, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, json=query)
print(f"podResume: {resp.status_code} - {resp.text[:500]}")

# Try podReset
query = {
    "query": """
    mutation {
        podReset(input: {
            podId: "test"
        }) {
            id
        }
    }
    """
}
resp = requests.post(url, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, json=query)
print(f"podReset: {resp.status_code} - {resp.text[:500]}")

# Try different REST API endpoints
print("\n" + "="*60)
print("Testing alternative REST endpoints...")

# Try the correct REST endpoint format
alt_endpoints = [
    ("POST", "https://api.runpod.io/v2/pod", {"name": "kerne-test", "gpuTypeId": "NVIDIA GeForce RTX 4090"}),
    ("POST", "https://api.runpod.io/rest/pods", {"name": "kerne-test"}),
    ("GET", "https://api.runpod.io/v2/user", {}),
    ("GET", "https://api.runpod.io/v2/templates", {}),
    ("GET", "https://api.runpod.io/v2/balance", {}),
]

for method, ep_url, data in alt_endpoints:
    if method == "GET":
        resp = requests.get(ep_url, headers={"Authorization": f"Bearer {API_KEY}"})
    else:
        resp = requests.post(ep_url, headers={"Authorization": f"Bearer {API_KEY}"}, json=data)
    print(f"{method} {ep_url}: {resp.status_code} - {resp.text[:200]}")

# Try to find the correct GraphQL mutation for creating pods
print("\n" + "="*60)
print("Trying to discover pod creation mutation...")

# Try different mutation names
mutations_to_try = [
    ("createPod", "input: {name: \"kerne-test\", gpuTypeId: \"NVIDIA GeForce RTX 4090\", imageName: \"runpod/pytorch:2.1.0-py3.10-cuda12.1.1-devel-ubuntu22.04\"}"),
    ("podCreate", "input: {name: \"kerne-test\", gpuTypeId: \"NVIDIA GeForce RTX 4090\"}"),
    ("createOnDemandPod", "input: {name: \"kerne-test\", gpuTypeId: \"NVIDIA GeForce RTX 4090\"}"),
    ("startPod", "input: {name: \"kerne-test\", gpuTypeId: \"NVIDIA GeForce RTX 4090\"}"),
    ("launchPod", "input: {name: \"kerne-test\", gpuTypeId: \"NVIDIA GeForce RTX 4090\"}"),
]

for mutation_name, args in mutations_to_try:
    query = {"query": f"mutation {{ {mutation_name}({args}) {{ id name }} }}"}
    resp = requests.post(url, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, json=query)
    print(f"{mutation_name}: {resp.status_code} - {resp.text[:200]}")

# Try to get all available mutations with proper introspection
print("\n" + "="*60)
print("Full GraphQL introspection...")
query = {
    "query": """
    {
        __schema {
            mutationType {
                fields {
                    name
                    args {
                        name
                        type {
                            name
                            kind
                            ofType {
                                name
                                kind
                            }
                        }
                    }
                }
            }
        }
    }
    """
}
resp = requests.post(url, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, json=query)
if resp.status_code == 200:
    try:
        data = resp.json()
        mutations = data.get("data", {}).get("__schema", {}).get("mutationType", {}).get("fields", [])
        print(f"\nFound {len(mutations)} mutations:")
        for m in mutations:
            print(f"  - {m['name']}")
            if "pod" in m['name'].lower() or "create" in m['name'].lower() or "start" in m['name'].lower():
                args = m.get('args', [])
                if args:
                    print(f"    Args: {[a['name'] for a in args]}")
    except Exception as e:
        print(f"Parse error: {e}")
        print(resp.text[:500])
else:
    print(f"Failed: {resp.status_code} - {resp.text[:200]}")

# Try createPool mutation - this is the correct one for GPU provisioning!
print("\n" + "="*60)
print("Testing createPool mutation (the correct one!)...")

# Try different variations of createPool
pool_mutations = [
    """
    mutation {
        createPool(input: {
            name: "kerne-inference-pool"
            gpuTypeId: "NVIDIA GeForce RTX 4090"
            gpuCount: 1
            imageName: "runpod/pytorch:2.1.0-py3.10-cuda12.1.1-devel-ubuntu22.04"
        }) {
            id
            name
        }
    }
    """,
    """
    mutation {
        createPool(input: {
            name: "kerne-inference-pool"
            gpuTypeId: "NVIDIA GeForce RTX 4090"
        }) {
            id
            name
        }
    }
    """,
]

for i, mutation in enumerate(pool_mutations):
    query = {"query": mutation}
    resp = requests.post(url, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, json=query)
    print(f"createPool attempt {i+1}: {resp.status_code} - {resp.text[:500]}")

# Try migratePod mutation
print("\n" + "="*60)
print("Testing migratePod mutation...")
query = {
    "query": """
    mutation {
        migratePod(input: {
            name: "kerne-test-pod"
            gpuTypeId: "NVIDIA GeForce RTX 4090"
            imageName: "runpod/pytorch:2.1.0-py3.10-cuda12.1.1-devel-ubuntu22.04"
        }) {
            id
            name
        }
    }
    """
}
resp = requests.post(url, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, json=query)
print(f"migratePod: {resp.status_code} - {resp.text[:500]}")

# Try Serverless Endpoint creation - this is what we actually need for OpenRouter!
print("\n" + "="*60)
print("Testing SERVERLESS endpoint creation (correct for OpenRouter)...")

# RunPod Serverless API endpoint
serverless_graphql = "https://api.runpod.io/graphql"

# Try createEndpoint mutation
query = {
    "query": """
    mutation {
        createEndpoint(input: {
            name: "kerne-llama-inference"
            imageName: "runpod/pytorch:2.1.0-py3.10-cuda12.1.1-devel-ubuntu22.04"
            gpuTypeId: "NVIDIA GeForce RTX 4090"
            workersMin: 0
            workersMax: 3
            idleTimeout: 300
        }) {
            id
            name
        }
    }
    """
}
resp = requests.post(serverless_graphql, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, json=query)
print(f"createEndpoint: {resp.status_code} - {resp.text[:500]}")

# Try different serverless mutations
serverless_mutations = [
    ("createServerlessEndpoint", "input: {name: \"kerne-test\", imageName: \"runpod/pytorch:2.1.0-py3.10-cuda12.1.1-devel-ubuntu22.04\"}"),
    ("deployEndpoint", "input: {name: \"kerne-test\"}"),
    ("createSls", "input: {name: \"kerne-test\"}"),
]

for mutation_name, args in serverless_mutations:
    query = {"query": f"mutation {{ {mutation_name}({args}) {{ id name }} }}"}
    resp = requests.post(serverless_graphql, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, json=query)
    print(f"{mutation_name}: {resp.status_code} - {resp.text[:200]}")

# Try the RunPod Serverless REST API
print("\n" + "="*60)
print("Testing RunPod Serverless REST API...")
serverless_rest_endpoints = [
    ("GET", "https://api.runpod.io/v2/endpoints", {}),
    ("GET", "https://api.runpod.io/graphql?query={endpoints{id name}}", {}),
    ("POST", "https://api.runpod.io/v2/endpoints", {"name": "kerne-test", "imageName": "runpod/pytorch:2.1.0-py3.10-cuda12.1.1-devel-ubuntu22.04"}),
]

for method, ep_url, data in serverless_rest_endpoints:
    if method == "GET":
        resp = requests.get(ep_url, headers={"Authorization": f"Bearer {API_KEY}"})
    else:
        resp = requests.post(ep_url, headers={"Authorization": f"Bearer {API_KEY}"}, json=data)
    print(f"{method} {ep_url}: {resp.status_code} - {resp.text[:300]}")

# Check what the user account has access to
print("\n" + "="*60)
print("Checking account capabilities...")
query = {"query": "query { myself { id email } }"}
resp = requests.post(url, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, json=query)
print(f"Account: {resp.text}")

# Try to query for available GPU clouds
query = {"query": "query { gpuClouds { id name } }"}
resp = requests.post(url, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, json=query)
print(f"GPU Clouds: {resp.status_code} - {resp.text[:300]}")

# Try to query for reservations (needed for createPool)
query = {"query": "query { reservations { id name status } }"}
resp = requests.post(url, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, json=query)
print(f"Reservations: {resp.status_code} - {resp.text[:300]}")

# Try saveEndpoint - the CORRECT mutation for serverless!
print("\n" + "="*60)
print("Testing saveEndpoint mutation (CORRECT for serverless!)...")

# Try different variations of saveEndpoint
save_endpoint_mutations = [
    """
    mutation {
        saveEndpoint(input: {
            name: "kerne-llama-inference"
            imageName: "runpod/pytorch:2.1.0-py3.10-cuda12.1.1-devel-ubuntu22.04"
            gpuTypeId: "NVIDIA GeForce RTX 4090"
            workersMin: 0
            workersMax: 3
        }) {
            id
            name
        }
    }
    """,
    """
    mutation {
        saveEndpoint(input: {
            name: "kerne-llama-inference"
            imageName: "runpod/pytorch:2.1.0-py3.10-cuda12.1.1-devel-ubuntu22.04"
        }) {
            id
            name
        }
    }
    """,
    """
    mutation {
        saveEndpoint(input: {
            name: "kerne-llama-inference"
        }) {
            id
            name
        }
    }
    """,
]

for i, mutation in enumerate(save_endpoint_mutations):
    query = {"query": mutation}
    resp = requests.post(url, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, json=query)
    print(f"saveEndpoint attempt {i+1}: {resp.status_code} - {resp.text[:500]}")

# Try querying for existing endpoints
print("\n" + "="*60)
print("Querying for existing endpoints...")
query = {"query": "query { endpoints { id name status } }"}
resp = requests.post(url, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, json=query)
print(f"endpoints query: {resp.status_code} - {resp.text[:500]}")

# Try myEndpoints
query = {"query": "query { myEndpoints { id name } }"}
resp = requests.post(url, headers={"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}, json=query)
print(f"myEndpoints: {resp.status_code} - {resp.text[:300]}")
