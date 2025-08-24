#!/usr/bin/env python3
"""
Test Railway GraphQL API access

This script tests different GraphQL queries to see what works with your token.
"""

import requests
import json
import os

def test_api_access():
    token = os.getenv("RAILWAY_TOKEN", "5a725b5b-dfae-48ce-98fa-c90b6d7e2714")
    project_id = os.getenv("RAILWAY_PROJECT_ID", "d586086b-3ecb-404b-ad92-9672d36d1e3f")
    environment_id = os.getenv("RAILWAY_ENVIRONMENT_ID", "cd226704-be4d-469d-8bb9-cb05bdcd1196")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }
    
    print("🧪 Testing Railway GraphQL API Access")
    print("=" * 50)
    
    # Test 1: Simple introspection query
    print("\n1. Testing introspection query...")
    introspection_query = """
    query IntrospectionQuery {
        __schema {
            types {
                name
                kind
            }
        }
    }
    """
    
    try:
        response = requests.post(
            "https://backboard.railway.app/graphql/v2",
            json={'query': introspection_query},
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'errors' not in data:
                print("✅ Introspection query successful")
                schema_types = [t['name'] for t in data.get('data', {}).get('__schema', {}).get('types', []) 
                              if not t['name'].startswith('__')]
                print(f"   Available types: {len(schema_types)} types found")
                relevant_types = [t for t in schema_types if any(keyword in t.lower() 
                                for keyword in ['log', 'deployment', 'project', 'environment'])]
                print(f"   Log-related types: {relevant_types[:10]}")  # Show first 10
            else:
                print(f"❌ Introspection errors: {data['errors']}")
        else:
            print(f"❌ Introspection failed: {response.status_code} - {response.text[:200]}")
    except Exception as e:
        print(f"❌ Introspection exception: {e}")
    
    # Test 2: Simple project query
    print("\n2. Testing project query...")
    project_query = f"""
    query GetProject {{
        project(id: "{project_id}") {{
            id
            name
        }}
    }}
    """
    
    try:
        response = requests.post(
            "https://backboard.railway.app/graphql/v2",
            json={'query': project_query},
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'errors' not in data:
                project = data.get('data', {}).get('project')
                if project:
                    print(f"✅ Project query successful: {project['name']} ({project['id']})")
                else:
                    print("❌ Project query returned null")
            else:
                print(f"❌ Project query errors: {data['errors']}")
        else:
            print(f"❌ Project query failed: {response.status_code} - {response.text[:200]}")
    except Exception as e:
        print(f"❌ Project query exception: {e}")
    
    # Test 3: Environment query
    print("\n3. Testing environment query...")
    env_query = f"""
    query GetEnvironment {{
        project(id: "{project_id}") {{
            id
            name
            environments(first: 5) {{
                edges {{
                    node {{
                        id
                        name
                    }}
                }}
            }}
        }}
    }}
    """
    
    try:
        response = requests.post(
            "https://backboard.railway.app/graphql/v2",
            json={'query': env_query},
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'errors' not in data:
                project = data.get('data', {}).get('project')
                if project:
                    environments = project.get('environments', {}).get('edges', [])
                    print(f"✅ Environment query successful: {len(environments)} environments found")
                    for env_edge in environments:
                        env = env_edge['node']
                        marker = "🎯" if env['id'] == environment_id else "  "
                        print(f"   {marker} {env['name']} ({env['id']})")
                else:
                    print("❌ Environment query returned null project")
            else:
                print(f"❌ Environment query errors: {data['errors']}")
        else:
            print(f"❌ Environment query failed: {response.status_code} - {response.text[:200]}")
    except Exception as e:
        print(f"❌ Environment query exception: {e}")
    
    # Test 4: Deployment query
    print("\n4. Testing deployment query...")
    deployment_query = f"""
    query GetDeployments {{
        project(id: "{project_id}") {{
            environments(where: {{ id: "{environment_id}" }}) {{
                edges {{
                    node {{
                        deployments(first: 3, orderBy: {{ createdAt: desc }}) {{
                            edges {{
                                node {{
                                    id
                                    status
                                    createdAt
                                }}
                            }}
                        }}
                    }}
                }}
            }}
        }}
    }}
    """
    
    try:
        response = requests.post(
            "https://backboard.railway.app/graphql/v2",
            json={'query': deployment_query},
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'errors' not in data:
                print("✅ Deployment query successful")
                try:
                    deployments = (data.get('data', {}).get('project', {})
                                 .get('environments', {}).get('edges', [{}])[0]
                                 .get('node', {}).get('deployments', {}).get('edges', []))
                    print(f"   Found {len(deployments)} recent deployments")
                    for dep_edge in deployments:
                        dep = dep_edge['node']
                        print(f"   - {dep['status']} ({dep['id'][:8]}...) at {dep['createdAt']}")
                except (IndexError, KeyError):
                    print("   - No deployments found or query structure changed")
            else:
                print(f"❌ Deployment query errors: {data['errors']}")
        else:
            print(f"❌ Deployment query failed: {response.status_code} - {response.text[:200]}")
    except Exception as e:
        print(f"❌ Deployment query exception: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 Summary: If the above queries work, your token has proper access.")
    print("   If deployment queries work but log queries don't, it might be a schema issue.")

if __name__ == "__main__":
    test_api_access()
