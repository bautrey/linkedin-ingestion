"""
ScoringEngine implementation for scoring profiles based on external algorithm configuration.
"""
from typing import Dict, Any, List


class ScoringEngine:
    """Implements scoring logic utilizing external configuration."""

    def __init__(self, algorithm_loader):
        """Initialize with algorithm loader dependency."""
        self.algorithm_loader = algorithm_loader

    async def calculate_score(self, profile_data: Dict[str, Any]) -> float:
        """
        Calculate the total score for a profile based on role algorithms.

        Args:
            profile_data: Profile information including role, experience, etc.

        Returns:
            Total score as a float between 0.0 and 1.0.
        """
        role = profile_data.get("role")

        # Load algorithms and thresholds for the specific role
        algorithms = await self.algorithm_loader.load_algorithms_for_role(role)
        thresholds = await self.algorithm_loader.load_thresholds_for_role(role)

        # Calculate scores for each category
        category_scores = []
        for algorithm in algorithms:
            category = algorithm["category"]
            config = algorithm["algorithm_config"]
            
            if role == "CTO":
                score = self._calculate_cto_category_score(profile_data, category, config)
            else:
                # Default scoring for other roles
                score = 0.5
            
            category_scores.append(score)

        if category_scores:
            overall_score = sum(category_scores) / len(category_scores)
        else:
            overall_score = 0.0

        # Ensure score is within range
        return max(0.0, min(1.0, overall_score))
    
    def _calculate_cto_category_score(self, profile_data: Dict[str, Any], category: str, config: Dict[str, Any]) -> float:
        """
        Calculate CTO-specific category score based on algorithm configuration.
        
        Args:
            profile_data: Profile information
            category: Scoring category (e.g., 'technical_leadership')
            config: Algorithm configuration from database
            
        Returns:
            Category score between 0.0 and 1.0
        """
        if category == "technical_leadership":
            return self._score_technical_leadership(profile_data, config)
        elif category == "industry_experience":
            return self._score_industry_experience(profile_data, config)
        elif category == "company_scale":
            return self._score_company_scale(profile_data, config)
        elif category == "education_background":
            return self._score_education_background(profile_data, config)
        elif category == "career_progression":
            return self._score_career_progression(profile_data, config)
        else:
            return 0.5  # Default score for unknown categories
    
    def _score_technical_leadership(self, profile_data: Dict[str, Any], config: Dict[str, Any]) -> float:
        """Score technical leadership based on keywords and experience."""
        keywords = config.get("keywords", [])
        experience_weight = config.get("experience_weight", 0.4)
        title_weight = config.get("title_weight", 0.3)
        
        # Check for leadership keywords in experience and name
        experience_text = " ".join(profile_data.get("experience", []))
        name = profile_data.get("name", "")
        
        keyword_matches = 0
        for keyword in keywords:
            if keyword.lower() in experience_text.lower() or keyword.lower() in name.lower():
                keyword_matches += 1
        
        # Calculate score based on keyword matches and weights
        keyword_score = min(1.0, keyword_matches / len(keywords)) if keywords else 0.0
        experience_score = min(1.0, len(profile_data.get("experience", [])) / 5.0)  # Normalize by 5 experiences
        
        total_score = (keyword_score * title_weight) + (experience_score * experience_weight)
        return min(1.0, total_score)
    
    def _score_industry_experience(self, profile_data: Dict[str, Any], config: Dict[str, Any]) -> float:
        """Score industry experience based on tech keywords."""
        tech_keywords = config.get("tech_keywords", [])
        years_weight = config.get("years_weight", 0.6)
        relevance_weight = config.get("relevance_weight", 0.4)
        
        experience_text = " ".join(profile_data.get("experience", []))
        
        # Count tech keyword matches
        tech_matches = 0
        for keyword in tech_keywords:
            if keyword.lower() in experience_text.lower():
                tech_matches += 1
        
        relevance_score = min(1.0, tech_matches / len(tech_keywords)) if tech_keywords else 0.0
        years_score = min(1.0, len(profile_data.get("experience", [])) / 4.0)  # Normalize by 4 positions
        
        return (relevance_score * relevance_weight) + (years_score * years_weight)
    
    def _score_company_scale(self, profile_data: Dict[str, Any], config: Dict[str, Any]) -> float:
        """Score based on company scale experience."""
        # Simple implementation - could be enhanced with actual company size data
        experience_count = len(profile_data.get("experience", []))
        return min(1.0, experience_count / 3.0)  # Normalize by 3 companies
    
    def _score_education_background(self, profile_data: Dict[str, Any], config: Dict[str, Any]) -> float:
        """Score education background."""
        education = profile_data.get("education", [])
        degrees = config.get("degrees", {})
        fields = config.get("fields", [])
        
        education_text = " ".join(education)
        
        # Check for relevant fields
        field_matches = 0
        for field in fields:
            if field.lower() in education_text.lower():
                field_matches += 1
        
        # Check for degree levels
        degree_score = 0.8  # Default for any degree
        if "MS" in education_text or "Master" in education_text:
            degree_score = 1.0
        elif "PhD" in education_text or "Doctor" in education_text:
            degree_score = 1.2
        
        field_score = min(1.0, field_matches / len(fields)) if fields else 0.5
        
        return min(1.0, (degree_score * 0.5) + (field_score * 0.5))
    
    def _score_career_progression(self, profile_data: Dict[str, Any], config: Dict[str, Any]) -> float:
        """Score career progression based on leadership roles."""
        leadership_roles = config.get("leadership_roles", [])
        progression_bonus = config.get("progression_bonus", 0.2)
        
        experience_text = " ".join(profile_data.get("experience", []))
        
        # Count leadership role mentions
        leadership_matches = 0
        for role in leadership_roles:
            if role.lower() in experience_text.lower():
                leadership_matches += 1
        
        base_score = min(1.0, leadership_matches / len(leadership_roles)) if leadership_roles else 0.0
        
        # Add progression bonus for multiple experiences
        experience_count = len(profile_data.get("experience", []))
        if experience_count > 2:
            base_score += progression_bonus
        
        return min(1.0, base_score)


