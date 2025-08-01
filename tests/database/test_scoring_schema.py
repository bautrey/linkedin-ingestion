"""
Tests for V1.8 scoring database schema
Tests database tables, constraints, and seed data for the scoring system
"""

import pytest
import pytest_asyncio
import asyncio
from typing import Dict, Any, List
from app.database.supabase_client import SupabaseClient
from app.core.config import settings


class TestScoringSchema:
    """Test suite for scoring database schema"""
    
    @pytest_asyncio.fixture
    async def supabase_client(self):
        """Create a Supabase client for testing"""
        client = SupabaseClient()
        await client._ensure_client()
        return client
    
    @pytest.mark.asyncio
    async def test_scoring_algorithms_table_exists(self, supabase_client):
        """Test that scoring_algorithms table exists with correct structure"""
        try:
            # Try to query the table structure
            result = await supabase_client.client.table('scoring_algorithms').select('*').limit(1).execute()
            assert result is not None
        except Exception as e:
            pytest.fail(f"scoring_algorithms table does not exist or is not accessible: {e}")
    
    @pytest.mark.asyncio
    async def test_scoring_categories_table_exists(self, supabase_client):
        """Test that scoring_categories table exists with correct structure"""
        try:
            result = await supabase_client.client.table('scoring_categories').select('*').limit(1).execute()
            assert result is not None
        except Exception as e:
            pytest.fail(f"scoring_categories table does not exist or is not accessible: {e}")
    
    @pytest.mark.asyncio
    async def test_scoring_thresholds_table_exists(self, supabase_client):
        """Test that scoring_thresholds table exists with correct structure"""
        try:
            result = await supabase_client.client.table('scoring_thresholds').select('*').limit(1).execute()
            assert result is not None
        except Exception as e:
            pytest.fail(f"scoring_thresholds table does not exist or is not accessible: {e}")
    
    @pytest.mark.asyncio
    async def test_profile_scores_table_exists(self, supabase_client):
        """Test that profile_scores table exists with correct structure"""
        try:
            result = await supabase_client.client.table('profile_scores').select('*').limit(1).execute()
            assert result is not None
        except Exception as e:
            pytest.fail(f"profile_scores table does not exist or is not accessible: {e}")
    
    @pytest.mark.asyncio
    async def test_scoring_categories_seed_data(self, supabase_client):
        """Test that scoring categories seed data is loaded"""
        result = await supabase_client.client.table('scoring_categories').select('name').execute()
        
        expected_categories = [
            'technical_leadership',
            'industry_experience', 
            'company_scale',
            'education_background',
            'career_progression'
        ]
        
        category_names = [row['name'] for row in result.data]
        
        for expected_category in expected_categories:
            assert expected_category in category_names, f"Missing category: {expected_category}"
    
    @pytest.mark.asyncio
    async def test_scoring_thresholds_seed_data(self, supabase_client):
        """Test that scoring thresholds seed data is loaded for all roles"""
        result = await supabase_client.client.table('scoring_thresholds').select('role, threshold_type, min_score, max_score').execute()
        
        # Check that we have thresholds for all three roles
        roles = ['CTO', 'CIO', 'CISO']
        threshold_types = ['excellent', 'good', 'fair', 'poor']
        
        role_thresholds = {}
        for row in result.data:
            role = row['role']
            if role not in role_thresholds:
                role_thresholds[role] = []
            role_thresholds[role].append(row['threshold_type'])
        
        for role in roles:
            assert role in role_thresholds, f"Missing thresholds for role: {role}"
            for threshold_type in threshold_types:
                assert threshold_type in role_thresholds[role], f"Missing {threshold_type} threshold for {role}"
    
    @pytest.mark.asyncio
    async def test_scoring_algorithms_seed_data(self, supabase_client):
        """Test that scoring algorithms seed data is loaded for all roles"""
        result = await supabase_client.client.table('scoring_algorithms').select('role, category').execute()
        
        roles = ['CTO', 'CIO', 'CISO']
        categories = [
            'technical_leadership',
            'industry_experience', 
            'company_scale',
            'education_background',
            'career_progression'
        ]
        
        role_categories = {}
        for row in result.data:
            role = row['role']
            if role not in role_categories:
                role_categories[role] = []
            role_categories[role].append(row['category'])
        
        for role in roles:
            assert role in role_categories, f"Missing algorithms for role: {role}"
            for category in categories:
                assert category in role_categories[role], f"Missing {category} algorithm for {role}"
    
    @pytest.mark.asyncio
    async def test_foreign_key_constraints(self, supabase_client):
        """Test that foreign key constraints work correctly"""
        # Test that profile_scores references profiles table correctly
        # This should fail if we try to insert with non-existent profile_id
        try:
            test_score = {
                'profile_id': 'non-existent-profile',
                'role': 'CTO',
                'overall_score': 0.85,
                'category_scores': {},
                'algorithm_version': 1
            }
            
            await supabase_client.client.table('profile_scores').insert(test_score).execute()
            pytest.fail("Foreign key constraint should have prevented this insert")
        except Exception:
            # This is expected - foreign key constraint should prevent the insert
            pass
    
    @pytest.mark.asyncio
    async def test_unique_constraints(self, supabase_client):
        """Test that unique constraints work correctly"""
        # Test scoring_categories unique constraint on name
        try:
            duplicate_category = {
                'name': 'technical_leadership',
                'description': 'Duplicate test',
                'weight': 1.0
            }
            
            await supabase_client.client.table('scoring_categories').insert(duplicate_category).execute()
            pytest.fail("Unique constraint should have prevented duplicate category name")
        except Exception:
            # This is expected - unique constraint should prevent duplicate
            pass
