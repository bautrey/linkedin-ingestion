import asyncio
from app.database.supabase_client import SupabaseClient

async def summarize_recent_profiles(limit=5):
    client = SupabaseClient()
    try:
        profiles = await client.list_recent_profiles(limit=limit)
        
        print("\nRecent LinkedIn Profiles Summary:\n")
        for profile in profiles:
            print(f"Name: {profile.get('name', 'N/A')}")
            print(f"Position: {profile.get('position', 'N/A')}")
            print(f"City: {profile.get('city', 'N/A')} | Country: {profile.get('country_code', 'N/A')}")
            print(f"Connections: {profile.get('connections', 'N/A'):,}")
            print(f"Followers: {profile.get('followers', 'N/A'):,}")
            print(f"Experience Items: {len(profile.get('experience', []))}")
            print(f"Education Items: {len(profile.get('education', []))}\n")

    except Exception as e:
        print(f"Failed to summarize recent profiles: {e}")

if __name__ == '__main__':
    asyncio.run(summarize_recent_profiles())

