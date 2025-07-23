# Product Mission

> Last Updated: 2025-01-23
> Version: 1.0.0

## Pitch

LinkedIn Ingestion Service is a comprehensive data foundation service that helps Fortium's evaluation and partner management systems make intelligent candidate and partner decisions by providing automated LinkedIn profile and company data collection into a searchable vector store.

## Users

### Primary Customers

- **Internal Fortium Systems**: Services requiring LinkedIn intelligence for candidate evaluation, partner matching, and engagement decisions
- **AI/LLM Integration Services**: MCP servers and other AI systems that need structured LinkedIn data for analysis

### User Personas

**System Integration Developer** (25-40 years old)
- **Role:** Backend Developer / AI Engineer
- **Context:** Building candidate evaluation or partner matching systems
- **Pain Points:** Manual LinkedIn data collection, inconsistent data formats, missing company context
- **Goals:** Reliable automated LinkedIn data ingestion, structured data for AI analysis

**Business Development Analyst** (28-45 years old)
- **Role:** BD Analyst / Partner Manager
- **Context:** Evaluating candidates and partners for client engagements
- **Pain Points:** Time-consuming manual research, incomplete candidate profiles, disconnected company information
- **Goals:** Complete candidate profiles with company context, automated data updates

## The Problem

### Fragmented LinkedIn Intelligence

Manual LinkedIn profile collection and analysis is time-intensive and inconsistent. Fortium needs comprehensive candidate and partner profiles that include both personal LinkedIn data and detailed company information from their work history to make informed engagement decisions.

**Our Solution:** Automated LinkedIn profile and company data ingestion with structured storage for AI-powered analysis.

### Missing Company Context

Individual LinkedIn profiles don't provide sufficient context about the companies in candidates' work experience, making it difficult to assess the quality and relevance of their background for specific client engagements.

**Our Solution:** Automatic company profile collection for every work experience entry, creating comprehensive candidate intelligence.

### Data Integration Complexity

Multiple Fortium systems need LinkedIn data in different formats, leading to duplicate data collection efforts and inconsistent information across systems.

**Our Solution:** Centralized vector store with standardized API access for all downstream systems.

## Differentiators

### Comprehensive Profile Intelligence

Unlike simple LinkedIn scrapers, we provide complete candidate intelligence by automatically collecting both personal profiles and associated company data, creating a comprehensive view of each candidate's professional background.

### AI-Ready Data Structure

Unlike manual data collection processes, we provide structured JSON data optimized for vector storage and AI analysis, enabling sophisticated candidate matching and evaluation algorithms.

### Integration-First Design

Unlike standalone tools, we're designed as a service layer that multiple Fortium systems can integrate with, providing consistent data formats and avoiding duplicate collection efforts.

## Key Features

### Core Features

- **LinkedIn Profile Ingestion:** Complete profile data extraction from LinkedIn URLs with structured JSON output
- **Automatic Company Collection:** Fetches company profiles for every work experience entry in the candidate's background
- **Vector Store Integration:** Intelligent storage with proper relationship mapping between profiles and companies
- **Duplicate Management:** Smart handling of existing profiles with update vs create logic

### API Features

- **RESTful Profile API:** POST for ingestion, GET for retrieval with comprehensive error handling
- **Status Tracking:** Real-time ingestion status and completion notifications
- **Relationship Queries:** Retrieve profiles with full company context and work history connections
- **Batch Processing:** Support for multiple profile ingestion with progress tracking

### Integration Features

- **MCP Server Ready:** API designed for seamless LLM and AI system integration
- **OpenAPI Documentation:** Auto-generated API documentation for easy integration
- **Webhook Support:** Optional notifications for completed ingestion processes
- **Data Export:** Flexible data export formats for downstream system integration
