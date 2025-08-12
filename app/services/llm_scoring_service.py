"""
V1.85 LLM Scoring Service

Provides OpenAI ChatGPT integration for flexible profile scoring with arbitrary prompts.
Handles async job processing, response parsing, and error management.
"""

import json
import uuid
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timezone
import asyncio
from asyncio import Semaphore

import openai
from openai import AsyncOpenAI
import tiktoken
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from app.core.logging import LoggerMixin
from app.core.config import settings
from app.models.canonical.profile import CanonicalProfile
from app.services.scoring_job_service import ScoringJobService
from app.models.scoring import JobStatus


class LLMScoringService(LoggerMixin):
    """
    Service for LLM-based profile scoring using OpenAI ChatGPT
    
    Handles profile data serialization, prompt formatting, API calls,
    response parsing, and async job management.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize LLM scoring service
        
        Args:
            api_key: OpenAI API key (falls back to environment if not provided)
        """
        self.api_key = api_key or settings.OPENAI_API_KEY
        if not self.api_key:
            self.logger.warning(
                "No OpenAI API key configured. LLM scoring will not work.",
                config_keys_checked=['OPENAI_API_KEY']
            )
        
        # Initialize OpenAI client with v1.x API
        self.client = None
        if self.api_key:
            try:
                # Try different initialization approaches for compatibility
                self.client = AsyncOpenAI(api_key=self.api_key)
            except TypeError as e:
                self.logger.warning(f"OpenAI client initialization error (v1): {e}")
                try:
                    # Try with minimal params
                    import openai
                    self.client = AsyncOpenAI(
                        api_key=self.api_key,
                        timeout=30.0
                    )
                except Exception as e2:
                    self.logger.warning(f"OpenAI client initialization error (v2): {e2}")
                    self.client = None
        
        # Service dependencies
        self.job_service = ScoringJobService()
        
        # Configuration from settings
        self.default_model = settings.OPENAI_DEFAULT_MODEL
        self.max_tokens = settings.OPENAI_MAX_TOKENS
        self.temperature = settings.OPENAI_TEMPERATURE
        self.max_input_tokens = 16000  # Conservative limit for input
        
        # Rate limiting
        self._rate_limiter = Semaphore(10)  # Max concurrent requests
        
        # Token counting
        self.encoding = tiktoken.get_encoding("cl100k_base")  # GPT-4 compatible
        
        self.logger.info(
            "LLM Scoring Service initialized",
            has_api_key=bool(self.api_key),
            default_model=self.default_model,
            max_concurrent=10
        )
    
    def count_tokens(self, text: str) -> int:
        """Count tokens in text using tiktoken"""
        if not text:
            return 0
        return len(self.encoding.encode(text))
    
    def truncate_text(self, text: str, max_tokens: int) -> str:
        """
        Truncate text to fit within token limits
        
        Args:
            text: Input text
            max_tokens: Maximum allowed tokens
            
        Returns:
            Truncated text that fits within token limit
        """
        if not text:
            return ""
        
        tokens = self.encoding.encode(text)
        if len(tokens) <= max_tokens:
            return text
        
        # Truncate and decode back to text
        truncated_tokens = tokens[:max_tokens]
        truncated_text = self.encoding.decode(truncated_tokens)
        
        self.logger.warning(
            "Text truncated for LLM input",
            original_tokens=len(tokens),
            truncated_tokens=max_tokens,
            original_length=len(text),
            truncated_length=len(truncated_text)
        )
        
        return truncated_text
    
    def profile_to_text(self, profile: CanonicalProfile) -> str:
        """
        Convert CanonicalProfile to comprehensive text representation for LLM analysis
        
        Args:
            profile: Canonical profile instance
            
        Returns:
            Formatted text representation of the profile
        """
        text_parts = []
        
        # Basic info
        if profile.full_name:
            text_parts.append(f"Name: {profile.full_name}")
        
        if profile.job_title:
            text_parts.append(f"Current Title: {profile.job_title}")
        
        if profile.company:
            text_parts.append(f"Current Company: {profile.company}")
        
        if profile.city:
            location = profile.city
            if profile.country:
                location += f", {profile.country}"
            text_parts.append(f"Location: {location}")
        
        # Professional summary
        if profile.about:
            text_parts.append(f"About: {profile.about}")
        
        # Experience
        if profile.experiences:
            text_parts.append("\\nExperience:")
            for i, exp in enumerate(profile.experiences):
                exp_text = f"  {i+1}. "
                if exp.title:
                    exp_text += f"{exp.title}"
                if exp.company:
                    exp_text += f" at {exp.company}"
                if exp.duration:
                    exp_text += f" ({exp.duration})"
                if exp.description:
                    exp_text += f"\\n     {exp.description}"
                text_parts.append(exp_text)
        
        # Education
        if profile.educations:
            text_parts.append("\\nEducation:")
            for i, edu in enumerate(profile.educations):
                edu_text = f"  {i+1}. "
                if edu.degree:
                    edu_text += f"{edu.degree}"
                if edu.field_of_study:
                    edu_text += f" in {edu.field_of_study}"
                if edu.school:
                    edu_text += f" from {edu.school}"
                if edu.date_range:
                    edu_text += f" ({edu.date_range})"
                text_parts.append(edu_text)
        
        # Skills (if available)
        if hasattr(profile, 'skills') and profile.skills:
            skills_text = ", ".join(profile.skills[:20])  # Limit to top 20 skills
            text_parts.append(f"\\nSkills: {skills_text}")
        
        # Connection metrics
        if profile.connection_count:
            text_parts.append(f"\\nConnections: {profile.connection_count}")
        
        if profile.follower_count:
            text_parts.append(f"Followers: {profile.follower_count}")
        
        profile_text = "\\n".join(text_parts)
        
        # Check token count and truncate if necessary
        token_count = self.count_tokens(profile_text)
        if token_count > self.max_input_tokens:
            profile_text = self.truncate_text(profile_text, self.max_input_tokens)
        
        self.logger.debug(
            "Profile converted to text",
            profile_id=profile.profile_id,
            text_length=len(profile_text),
            token_count=self.count_tokens(profile_text),
            has_experience=bool(profile.experiences),
            has_education=bool(profile.educations)
        )
        
        return profile_text
    
    def format_prompt(self, profile_text: str, user_prompt: str) -> str:
        """
        Format the complete prompt for LLM evaluation
        
        Args:
            profile_text: Formatted profile text
            user_prompt: User-provided evaluation prompt
            
        Returns:
            Complete formatted prompt for the LLM
        """
        system_prompt = """You are an expert recruiter and talent evaluator. You will be given a LinkedIn profile and asked to evaluate it according to specific criteria.

Please analyze the profile thoroughly and provide your evaluation in valid JSON format. Your response should include:
1. A detailed assessment based on the evaluation criteria
2. A numerical score or rating if requested
3. Specific rationale for your evaluation
4. Any relevant observations about the candidate's background

Make sure your response is valid JSON that can be parsed programmatically."""

        complete_prompt = f"""{system_prompt}

PROFILE TO EVALUATE:
{profile_text}

EVALUATION REQUEST:
{user_prompt}

Please provide your evaluation in JSON format:"""

        return complete_prompt
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        retry=retry_if_exception_type((openai.RateLimitError, openai.APITimeoutError, openai.InternalServerError))
    )
    async def _call_openai_api(
        self, 
        prompt: str, 
        model: str = None,
        max_tokens: int = None,
        temperature: float = None
    ) -> Dict[str, Any]:
        """
        Make API call to OpenAI with retry logic
        
        Args:
            prompt: Complete formatted prompt
            model: OpenAI model to use
            max_tokens: Maximum response tokens
            temperature: Sampling temperature
            
        Returns:
            Raw API response data
            
        Raises:
            openai.OpenAIError: For API errors that can't be retried
        """
        if not self.client:
            raise ValueError("OpenAI client not initialized - missing API key")
        
        model = model or self.default_model
        max_tokens = max_tokens or self.max_tokens
        temperature = temperature if temperature is not None else self.temperature
        
        async with self._rate_limiter:
            self.logger.info(
                "Making OpenAI API call",
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                prompt_tokens=self.count_tokens(prompt)
            )
            
            try:
                response = await self.client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=max_tokens,
                    temperature=temperature,
                    response_format={"type": "json_object"}  # Ensure JSON response
                )
                
                # Extract response data
                message = response.choices[0].message
                usage = response.usage
                
                result = {
                    "content": message.content,
                    "model": response.model,
                    "usage": {
                        "prompt_tokens": usage.prompt_tokens,
                        "completion_tokens": usage.completion_tokens,
                        "total_tokens": usage.total_tokens
                    },
                    "finish_reason": response.choices[0].finish_reason
                }
                
                self.logger.info(
                    "OpenAI API call successful",
                    model=result["model"],
                    prompt_tokens=result["usage"]["prompt_tokens"],
                    completion_tokens=result["usage"]["completion_tokens"],
                    total_tokens=result["usage"]["total_tokens"],
                    finish_reason=result["finish_reason"]
                )
                
                return result
                
            except openai.RateLimitError as e:
                self.logger.warning(
                    "OpenAI rate limit exceeded - will retry",
                    error=str(e),
                    model=model
                )
                raise
            
            except openai.APITimeoutError as e:
                self.logger.warning(
                    "OpenAI API timeout - will retry",
                    error=str(e),
                    model=model
                )
                raise
            
            except openai.InternalServerError as e:
                self.logger.warning(
                    "OpenAI internal server error - will retry",
                    error=str(e),
                    model=model
                )
                raise
            
            except openai.AuthenticationError as e:
                self.logger.error(
                    "OpenAI authentication failed",
                    error=str(e)
                )
                raise ValueError(f"OpenAI authentication failed: {e}")
            
            except openai.BadRequestError as e:
                self.logger.error(
                    "OpenAI bad request",
                    error=str(e),
                    model=model,
                    prompt_length=len(prompt)
                )
                raise ValueError(f"Invalid request to OpenAI: {e}")
            
            except Exception as e:
                self.logger.error(
                    "Unexpected OpenAI API error",
                    error=str(e),
                    error_type=type(e).__name__,
                    model=model
                )
                raise
    
    def parse_llm_response(self, response_content: str) -> Dict[str, Any]:
        """
        Parse and validate LLM response JSON
        
        Args:
            response_content: Raw response content from LLM
            
        Returns:
            Parsed and validated response data
            
        Raises:
            ValueError: If response cannot be parsed or validated
        """
        if not response_content or not response_content.strip():
            raise ValueError("Empty response from LLM")
        
        try:
            parsed_response = json.loads(response_content)
            
            # Basic validation - ensure it's a dict
            if not isinstance(parsed_response, dict):
                raise ValueError("LLM response is not a JSON object")
            
            self.logger.debug(
                "LLM response parsed successfully",
                response_keys=list(parsed_response.keys()),
                response_length=len(response_content)
            )
            
            return parsed_response
            
        except json.JSONDecodeError as e:
            self.logger.error(
                "Failed to parse LLM response as JSON",
                error=str(e),
                response_preview=response_content[:200] if response_content else None
            )
            raise ValueError(f"Invalid JSON in LLM response: {e}")
    
    async def score_profile(
        self,
        profile: CanonicalProfile,
        prompt: str,
        model: str = None,
        max_tokens: int = None,
        temperature: float = None
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Score a profile using LLM evaluation (direct synchronous call)
        
        Args:
            profile: Profile to evaluate
            prompt: Evaluation prompt
            model: OpenAI model to use
            max_tokens: Maximum response tokens
            temperature: Sampling temperature
            
        Returns:
            Tuple of (raw_llm_response, parsed_score)
            
        Raises:
            ValueError: For validation errors or API issues
        """
        if not profile:
            raise ValueError("Profile is required for scoring")
        
        if not prompt or not prompt.strip():
            raise ValueError("Evaluation prompt is required")
        
        self.logger.info(
            "Starting profile scoring",
            profile_id=profile.profile_id,
            profile_name=profile.full_name,
            prompt_length=len(prompt),
            model=model or self.default_model
        )
        
        # Convert profile to text
        profile_text = self.profile_to_text(profile)
        
        # Format complete prompt
        formatted_prompt = self.format_prompt(profile_text, prompt)
        
        # Check total token count
        prompt_tokens = self.count_tokens(formatted_prompt)
        if prompt_tokens > 15000:  # Leave room for response
            raise ValueError(f"Prompt too long: {prompt_tokens} tokens (max ~15000)")
        
        # Make API call
        try:
            raw_response = await self._call_openai_api(
                formatted_prompt, 
                model=model, 
                max_tokens=max_tokens, 
                temperature=temperature
            )
            
            # Parse response
            parsed_score = self.parse_llm_response(raw_response["content"])
            
            # Add metadata to parsed score
            parsed_score["_metadata"] = {
                "model_used": raw_response["model"],
                "tokens_used": raw_response["usage"]["total_tokens"],
                "prompt_tokens": raw_response["usage"]["prompt_tokens"],
                "completion_tokens": raw_response["usage"]["completion_tokens"],
                "finish_reason": raw_response["finish_reason"],
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
            self.logger.info(
                "Profile scoring completed successfully",
                profile_id=profile.profile_id,
                model_used=raw_response["model"],
                total_tokens=raw_response["usage"]["total_tokens"],
                has_parsed_score=bool(parsed_score)
            )
            
            return raw_response, parsed_score
            
        except Exception as e:
            self.logger.error(
                "Profile scoring failed",
                profile_id=profile.profile_id,
                error=str(e),
                error_type=type(e).__name__
            )
            raise
    
    async def process_scoring_job(
        self, 
        job_id: str, 
        max_tokens: Optional[int] = None, 
        temperature: Optional[float] = None
    ) -> bool:
        """
        Process an async scoring job
        
        Args:
            job_id: Scoring job ID to process
            
        Returns:
            bool: True if successful, False otherwise
        """
        self.logger.info("STEP 1: Starting process_scoring_job", job_id=job_id)
        
        job = await self.job_service.get_job(job_id)
        if not job:
            self.logger.error("STEP 1 FAILED: Scoring job not found", job_id=job_id)
            return False
        
        if job.status != JobStatus.PENDING:
            self.logger.warning(
                "STEP 1 FAILED: Job not in pending status", 
                job_id=job_id, 
                current_status=job.status
            )
            return False
        
        self.logger.info(
            "STEP 2: Job validation passed, starting processing",
            job_id=job_id,
            profile_id=job.profile_id,
            model_name=job.model_name,
            prompt_length=len(job.prompt)
        )
        
        try:
            # Update job status to processing
            self.logger.info("STEP 3: Updating job status to PROCESSING", job_id=job_id)
            started_at = datetime.now(timezone.utc)
            await self.job_service.update_job_status(
                job_id, 
                JobStatus.PROCESSING, 
                started_at=started_at
            )
            self.logger.info("STEP 3 SUCCESS: Job status updated to PROCESSING", job_id=job_id)
            
            # Get profile data
            self.logger.info("STEP 4: Retrieving profile data", job_id=job_id, profile_id=job.profile_id)
            profile = await self._get_profile_by_id(job.profile_id)
            if not profile:
                self.logger.error("STEP 4 FAILED: Profile not found, failing job", job_id=job_id, profile_id=job.profile_id)
                await self.job_service.fail_job(
                    job_id, 
                    f"Profile not found: {job.profile_id}"
                )
                return False
            
            self.logger.info(
                "STEP 4 SUCCESS: Profile retrieved", 
                job_id=job_id,
                profile_id=job.profile_id,
                profile_name=profile.full_name,
                experience_count=len(profile.experiences),
                education_count=len(profile.educations)
            )
            
            # Score the profile
            self.logger.info("STEP 5: Starting LLM scoring", job_id=job_id, model=job.model_name)
            raw_response, parsed_score = await self.score_profile(
                profile=profile,
                prompt=job.prompt,
                model=job.model_name,
                max_tokens=max_tokens,
                temperature=temperature
            )
            self.logger.info(
                "STEP 5 SUCCESS: LLM scoring completed", 
                job_id=job_id, 
                tokens_used=raw_response.get("usage", {}).get("total_tokens", 0),
                score_keys=list(parsed_score.keys()) if parsed_score else []
            )
            
            # Update job with results
            self.logger.info("STEP 6: Completing job with results", job_id=job_id)
            await self.job_service.complete_job(
                job_id=job_id,
                llm_response=raw_response,
                parsed_score=parsed_score
            )
            
            self.logger.info(
                "STEP 6 SUCCESS: Scoring job completed successfully",
                job_id=job_id,
                profile_id=job.profile_id,
                tokens_used=raw_response.get("usage", {}).get("total_tokens", 0)
            )
            
            return True
            
        except Exception as e:
            # Log error and mark job as failed
            error_message = f"{type(e).__name__}: {str(e)}"
            
            self.logger.error(
                "SCORING JOB PROCESSING FAILED - FULL ERROR",
                job_id=job_id,
                profile_id=job.profile_id,
                error_message=error_message,
                error_type=type(e).__name__,
                error_details=str(e)
            )
            
            try:
                await self.job_service.fail_job(job_id, error_message)
                self.logger.info("Job marked as failed", job_id=job_id)
            except Exception as fail_error:
                self.logger.error("Failed to mark job as failed", job_id=job_id, fail_error=str(fail_error))
            
            return False
    
    async def _get_profile_by_id(self, profile_id: str) -> Optional[CanonicalProfile]:
        """
        Get CanonicalProfile by ID from database
        
        Args:
            profile_id: Profile UUID
            
        Returns:
            CanonicalProfile instance or None if not found
        """
        try:
            # Import here to avoid circular imports
            from app.database.supabase_client import SupabaseClient
            from app.models.canonical.profile import (
                CanonicalProfile, Experience, Education
            )
            from pydantic import HttpUrl
            from datetime import datetime, timezone
            
            # Get profile data from database
            db_client = SupabaseClient()
            profile_data = await db_client.get_profile_by_id(profile_id)
            
            if not profile_data:
                self.logger.info("Profile not found in database", profile_id=profile_id)
                return None
            
            # Convert database record to CanonicalProfile
            # Handle experiences
            experiences = []
            if profile_data.get('experience'):
                for exp_data in profile_data['experience']:
                    if isinstance(exp_data, dict):
                        experiences.append(Experience(
                            title=exp_data.get('title'),
                            company=exp_data.get('company'),
                            duration=exp_data.get('duration'),
                            description=exp_data.get('description'),
                            location=exp_data.get('location')
                        ))
            
            # Handle educations
            educations = []
            if profile_data.get('education'):
                for edu_data in profile_data['education']:
                    if isinstance(edu_data, dict):
                        educations.append(Education(
                            school=edu_data.get('school'),
                            degree=edu_data.get('degree'),
                            field_of_study=edu_data.get('field_of_study'),
                            date_range=edu_data.get('date_range'),
                            description=edu_data.get('description')
                        ))
            
            # Parse timestamp
            timestamp = None
            if profile_data.get('timestamp'):
                try:
                    timestamp = datetime.fromisoformat(profile_data['timestamp'].replace('Z', '+00:00'))
                except ValueError:
                    timestamp = datetime.now(timezone.utc)
            else:
                timestamp = datetime.now(timezone.utc)
            
            # Create CanonicalProfile instance
            canonical_profile = CanonicalProfile(
                profile_id=profile_data.get('linkedin_id', profile_data['id']),
                full_name=profile_data.get('name'),
                linkedin_url=HttpUrl(profile_data['url']) if profile_data.get('url') else None,
                job_title=profile_data.get('position'),
                company=profile_data.get('current_company', {}).get('name') if profile_data.get('current_company') else None,
                about=profile_data.get('about'),
                city=profile_data.get('city'),
                country=profile_data.get('country_code'),
                connection_count=profile_data.get('connections'),
                follower_count=profile_data.get('followers'),
                experiences=experiences,
                educations=educations,
                timestamp=timestamp
            )
            
            self.logger.info(
                "Profile retrieved and converted to CanonicalProfile",
                profile_id=profile_id,
                profile_name=canonical_profile.full_name,
                experience_count=len(experiences),
                education_count=len(educations)
            )
            
            return canonical_profile
            
        except Exception as e:
            self.logger.error(
                "Failed to retrieve profile by ID",
                profile_id=profile_id,
                error=str(e),
                error_type=type(e).__name__
            )
            return None
