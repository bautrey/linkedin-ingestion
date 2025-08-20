# Spec Requirements Document

> Spec: V2.3 Enhanced Scoring with Company Context
> Created: 2025-08-20
> Status: Planning

## Overview

Transform profile scoring accuracy by integrating rich company context into LLM evaluation prompts, enabling the scoring system to distinguish between dramatically different professional experiences (e.g., "CTO at 50-person startup" vs "CTO at 284K-employee enterprise") and provide nuanced assessments that consider company scale, industry relevance, and organizational complexity.

## User Stories

### Context-Aware Executive Scoring

As a **Business Development Analyst**, I want profile scoring to consider the scale and complexity of companies in a candidate's background, so that I can accurately assess whether their experience matches the scope and requirements of our client engagements.

**Detailed Workflow:** When scoring a CTO candidate, the system automatically includes company context in the evaluation prompt ("Led technology at PricewaterhouseCoopers (284K employees, Professional Services, global scale)" vs "Led technology at StartupCorp (45 employees, early-stage)"), resulting in differentiated scoring that reflects the vastly different leadership challenges and organizational complexity involved in each role.

### Industry-Specific Experience Evaluation

As a **Business Development Analyst**, I want scoring to recognize relevant industry experience by analyzing the companies in a candidate's background, so that I can identify candidates whose industry exposure aligns with specific client requirements.

**Detailed Workflow:** Scoring system analyzes company industries from work experience (["Professional Services", "Financial Technology", "Healthcare"]), includes industry diversity and relevance in evaluation prompts, and provides scoring commentary that highlights specific industry expertise and cross-sector experience value for client matching.

### Company Scale Context in Scoring

As a **Business Development Analyst**, I want scoring results to explicitly explain how company scale influences the assessment, so that I can understand whether a candidate's experience is appropriate for small-scale implementations or enterprise-level transformations.

**Detailed Workflow:** Scoring output includes company context analysis ("Experience across 3 companies totaling 295K employees: 2 Enterprise (10K+), 1 Mid-size (1K-10K)") and explains how this scale diversity impacts the leadership assessment, operational complexity understanding, and suitability for different client engagement types.

## Spec Scope

1. **Company Context Integration** - Automatic inclusion of rich company data in scoring prompts and evaluation logic
2. **Enhanced Scoring Templates** - Updated CTO/CIO/CISO templates that leverage company scale, industry, and complexity factors
3. **Context-Aware Scoring Logic** - Scoring algorithms that weight experience differently based on company characteristics
4. **Company Analytics in Results** - Scoring outputs that include company context analysis and insights
5. **Template Management Enhancement** - Admin interface updates to manage company-aware scoring templates

## Out of Scope

- Company data validation or correction within scoring workflow
- Real-time company data fetching during scoring (uses existing stored data)
- Custom company weighting factors or manual company importance scoring
- Historical rescoring of existing profiles with new company context
- Company similarity scoring or company-to-company comparison features

## Expected Deliverable

1. **Dramatically Improved Scoring Accuracy** - Scoring system distinguishes between startup CTOs and enterprise CTOs, providing assessments that reflect actual leadership scope and complexity
2. **Company-Contextual Scoring Reports** - All scoring results include company context analysis, industry diversity metrics, and scale-based insights for informed candidate evaluation
3. **Updated Scoring Templates** - All role-based templates (CTO, CIO, CISO) enhanced with company context prompts that produce nuanced, company-aware evaluations for better client matching

## Spec Documentation

- Tasks: @agent-os/specs/2025-08-20-v2.3-scoring-with-companies/tasks.md  
- Technical Specification: @agent-os/specs/2025-08-20-v2.3-scoring-with-companies/sub-specs/technical-spec.md
- Scoring Enhancement Specification: @agent-os/specs/2025-08-20-v2.3-scoring-with-companies/sub-specs/scoring-spec.md
- Tests Specification: @agent-os/specs/2025-08-20-v2.3-scoring-with-companies/sub-specs/tests.md
