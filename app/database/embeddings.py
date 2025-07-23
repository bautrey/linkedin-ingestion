"""
Embedding generation service using OpenAI's embedding API

Handles text-to-vector conversion for LinkedIn profiles and companies
"""

import openai
from typing import List, Optional, Dict, Any
import tiktoken
from functools import lru_cache

from app.core.config import settings
from app.core.logging import LoggerMixin
from app.cassidy.models import LinkedInProfile, CompanyProfile


class EmbeddingService(LoggerMixin):
    """Service for generating vector embeddings from text data"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize embedding service
        
        Args:
            api_key: OpenAI API key (falls back to environment if not provided)
        """
        if api_key:
            openai.api_key = api_key
        
        self.model = "text-embedding-ada-002"  # OpenAI's current embedding model
        self.max_tokens = 8192  # Model token limit
        self.encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4 encoding
    
    @lru_cache(maxsize=128)
    def _count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken"""
        return len(self.encoding.encode(text))
    
    def _truncate_text(self, text: str, max_tokens: int = None) -> str:
        """
        Truncate text to fit within token limits
        
        Args:
            text: Input text
            max_tokens: Maximum tokens (uses model limit if None)
            
        Returns:
            Truncated text
        """
        if max_tokens is None:
            max_tokens = self.max_tokens - 100  # Leave buffer for safety
        
        tokens = self.encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text
        
        # Truncate and decode back to text
        truncated_tokens = tokens[:max_tokens]
        truncated_text = self.encoding.decode(truncated_tokens)
        
        self.logger.warning(
            "Text truncated for embedding",
            original_tokens=len(tokens),
            truncated_tokens=max_tokens,
            original_length=len(text),
            truncated_length=len(truncated_text)
        )
        
        return truncated_text
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        
        Args:
            text: Input text to embed
            
        Returns:
            Vector embedding as list of floats
        """
        if not text or not text.strip():
            # Return zero vector for empty text
            return [0.0] * settings.VECTOR_DIMENSION
        
        # Truncate if necessary
        processed_text = self._truncate_text(text.strip())
        token_count = self._count_tokens(processed_text)
        
        self.logger.debug(
            "Generating embedding",
            text_length=len(processed_text),
            token_count=token_count
        )
        
        try:
            response = await openai.Embedding.acreate(
                model=self.model,
                input=processed_text
            )
            
            embedding = response['data'][0]['embedding']
            
            self.logger.debug(
                "Embedding generated successfully",
                dimension=len(embedding),
                tokens_used=response.get('usage', {}).get('total_tokens', token_count)
            )
            
            return embedding
            
        except Exception as e:
            self.logger.error(
                "Failed to generate embedding",
                error=str(e),
                error_type=type(e).__name__,
                text_length=len(processed_text)
            )
            raise
    
    async def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batch
        
        Args:
            texts: List of texts to embed
            
        Returns:
            List of vector embeddings
        """
        if not texts:
            return []
        
        # Process and truncate texts
        processed_texts = [self._truncate_text(text.strip()) if text else "" for text in texts]
        
        # Filter out empty texts but keep track of indices
        non_empty_texts = []
        text_indices = []
        for i, text in enumerate(processed_texts):
            if text:
                non_empty_texts.append(text)
                text_indices.append(i)
        
        if not non_empty_texts:
            # Return zero vectors for all empty texts
            return [[0.0] * settings.VECTOR_DIMENSION] * len(texts)
        
        self.logger.info(
            "Generating batch embeddings",
            total_texts=len(texts),
            non_empty_texts=len(non_empty_texts)
        )
        
        try:
            response = await openai.Embedding.acreate(
                model=self.model,
                input=non_empty_texts
            )
            
            embeddings = [item['embedding'] for item in response['data']]
            
            # Reconstruct full embedding list with zero vectors for empty texts
            result = []
            embedding_idx = 0
            
            for i in range(len(texts)):
                if i in text_indices:
                    result.append(embeddings[embedding_idx])
                    embedding_idx += 1
                else:
                    result.append([0.0] * settings.VECTOR_DIMENSION)
            
            self.logger.info(
                "Batch embeddings generated successfully",
                embeddings_count=len(result),
                tokens_used=response.get('usage', {}).get('total_tokens', 0)
            )
            
            return result
            
        except Exception as e:
            self.logger.error(
                "Failed to generate batch embeddings",
                error=str(e),
                error_type=type(e).__name__,
                texts_count=len(non_empty_texts)
            )
            raise
    
    def profile_to_text(self, profile: LinkedInProfile) -> str:
        """
        Convert LinkedIn profile to searchable text
        
        Args:
            profile: LinkedInProfile instance
            
        Returns:
            Concatenated text representation
        """
        text_parts = []
        
        # Basic info
        if profile.name:
            text_parts.append(f"Name: {profile.name}")
        if profile.position:
            text_parts.append(f"Position: {profile.position}")
        if profile.about:
            text_parts.append(f"About: {profile.about}")
        
        # Location
        location_parts = []
        if profile.city:
            location_parts.append(profile.city)
        if profile.country_code:
            location_parts.append(profile.country_code)
        if location_parts:
            text_parts.append(f"Location: {', '.join(location_parts)}")
        
        # Current company
        if profile.current_company:
            company_text = f"Current Company: {profile.current_company.get('name', '')}"
            if profile.current_company.get('position'):
                company_text += f" as {profile.current_company['position']}"
            text_parts.append(company_text)
        
        # Experience
        if profile.experience:
            exp_texts = []
            for exp in profile.experience[:5]:  # Limit to recent experience
                exp_text = f"{exp.get('position', '')} at {exp.get('company', '')}"
                if exp.get('description'):
                    exp_text += f": {exp['description'][:200]}..."  # Truncate long descriptions
                exp_texts.append(exp_text)
            text_parts.append(f"Experience: {'; '.join(exp_texts)}")
        
        # Education
        if profile.education:
            edu_texts = []
            for edu in profile.education[:3]:  # Limit to recent education
                edu_text = f"{edu.get('degree', '')} from {edu.get('school', '')}"
                if edu.get('field_of_study'):
                    edu_text += f" in {edu['field_of_study']}"
                edu_texts.append(edu_text)
            text_parts.append(f"Education: {'; '.join(edu_texts)}")
        
        return " | ".join(text_parts)
    
    def company_to_text(self, company: CompanyProfile) -> str:
        """
        Convert company profile to searchable text
        
        Args:
            company: CompanyProfile instance
            
        Returns:
            Concatenated text representation
        """
        text_parts = []
        
        # Basic info
        if company.company_name:
            text_parts.append(f"Company: {company.company_name}")
        if company.description:
            text_parts.append(f"Description: {company.description}")
        
        # Industries
        if company.industries:
            text_parts.append(f"Industries: {', '.join(company.industries)}")
        
        # Location
        location_parts = []
        if company.hq_city:
            location_parts.append(company.hq_city)
        if company.hq_region:
            location_parts.append(company.hq_region)
        if company.hq_country:
            location_parts.append(company.hq_country)
        if location_parts:
            text_parts.append(f"Headquarters: {', '.join(location_parts)}")
        
        # Size and founding
        if company.employee_range:
            text_parts.append(f"Size: {company.employee_range}")
        if company.year_founded:
            text_parts.append(f"Founded: {company.year_founded}")
        
        # Funding
        if company.funding_info:
            funding_text = f"Funding: {company.funding_info.get('total_funding', 'Unknown')}"
            if company.funding_info.get('latest_round'):
                funding_text += f" (Latest: {company.funding_info['latest_round']})"
            text_parts.append(funding_text)
        
        return " | ".join(text_parts)
    
    async def embed_profile(self, profile: LinkedInProfile) -> List[float]:
        """
        Generate embedding for LinkedIn profile
        
        Args:
            profile: LinkedInProfile instance
            
        Returns:
            Vector embedding
        """
        text = self.profile_to_text(profile)
        return await self.generate_embedding(text)
    
    async def embed_company(self, company: CompanyProfile) -> List[float]:
        """
        Generate embedding for company profile
        
        Args:
            company: CompanyProfile instance
            
        Returns:
            Vector embedding
        """
        text = self.company_to_text(company)
        return await self.generate_embedding(text)
