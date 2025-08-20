# Canonical Models Documentation

This directory contains the canonical Pydantic V2 models that serve as the internal data contract for the LinkedIn ingestion application.

## CanonicalCompany Model

The `CanonicalCompany` model is a comprehensive representation of LinkedIn company data that normalizes information from various data providers.

### Key Features

#### 🧹 **Data Validation & Cleaning**
- **Company Name**: Automatically cleans multiple spaces and whitespace
- **Email**: Validates format and converts to lowercase
- **Industries**: Deduplicates entries while preserving order
- **Employee/Follower Counts**: Validates non-negative values
- **Year Founded**: Validates reasonable year ranges (1600 - current year + 1)

#### 🔗 **Domain Extraction**
- Automatically extracts domain from website URLs
- Removes 'www.' prefix for consistency
- Handles domain/website consistency validation

#### 📊 **Computed Properties**
- **`display_name`**: Clean display name for UI
- **`company_age`**: Calculated age in years
- **`size_category`**: Categorizes by employee count (Startup, Small, Medium, Large, Enterprise)
- **`headquarters`**: Synthesizes HQ location from various fields
- **`specialties_list`**: Parses comma-separated specialties into list

#### 🚀 **Business Intelligence Methods**
- **`is_startup()`**: Intelligent startup detection based on size, age, and funding
- **`has_funding_info()`**: Checks for any funding information
- **`get_primary_industry()`**: Returns first industry from list
- **`get_location_by_city()`**: Find locations by city name
- **`to_summary_dict()`**: Returns key company information for APIs

### Usage Examples

#### Basic Company Creation
```python
from app.models.canonical.company import CanonicalCompany

# Minimal company
company = CanonicalCompany(company_name="Acme Corp")
print(company.display_name)  # "Acme Corp"
```

#### Automatic Data Cleaning
```python
# Data gets cleaned automatically
company = CanonicalCompany(
    company_name="  Messy   Name  ",  # Multiple spaces
    email="Contact@EXAMPLE.COM",      # Mixed case
    industries=["Tech", "AI", "Tech"] # Duplicates
)

print(company.company_name)  # "Messy Name"
print(company.email)         # "contact@example.com"
print(company.industries)    # ["Tech", "AI"]
```

#### Domain Auto-Extraction
```python
company = CanonicalCompany(
    company_name="Test Corp",
    website="https://www.example.com/path"
)
print(company.domain)  # "example.com"
```

#### Startup Detection
```python
startup = CanonicalCompany(
    company_name="Young Startup",
    employee_count=15,
    year_founded=2022,
    funding_info={
        "last_funding_round_type": "Seed",
        "last_funding_round_year": 2024
    }
)
print(startup.is_startup())      # True
print(startup.size_category)     # "Small"
print(startup.company_age)       # 3 (current year - 2022)
```

#### Headquarters Synthesis
```python
company = CanonicalCompany(
    company_name="Global Corp",
    hq_city="San Francisco",
    hq_region="CA",
    hq_country="United States"
)
hq = company.headquarters
print(hq.city)           # "San Francisco"
print(hq.is_headquarter) # True
```

### Size Categories

| Employee Count | Category    |
|---------------|-------------|
| < 10          | Startup     |
| 10-49         | Small       |
| 50-199        | Medium      |
| 200-999       | Large       |
| 1000+         | Enterprise  |
| None          | Unknown     |

### Startup Detection Algorithm

A company is considered a startup if:
1. **Small**: Less than 200 employees
2. **Young**: Founded within last 10 years
3. **Funding**: Has startup-type funding (Seed, Series A/B, Angel) OR
4. **Default**: Small (<50 employees) and young (≤7 years)

### Field Validation

- **Company Name**: Required, cleaned of extra whitespace
- **Email**: Optional, validated format, converted to lowercase
- **Year Founded**: Optional, must be between 1600 and next year
- **Employee Count**: Optional, must be non-negative
- **Follower Count**: Optional, must be non-negative
- **Industries**: List, automatically deduplicated
- **URLs**: HttpUrl type with automatic validation

### Nested Models

- **`CanonicalFundingInfo`**: Funding round details
- **`CanonicalCompanyLocation`**: Office location information
- **`CanonicalAffiliatedCompany`**: Related company information

All nested models support `extra='allow'` for future extensibility.

### Testing

The model includes comprehensive test coverage (26 tests) validating:
- Field validation and cleaning
- Computed properties
- Utility methods
- Startup detection logic
- Domain extraction
- Serialization round-trips
- Edge cases and error conditions

Run tests with:
```bash
python -m pytest app/tests/test_canonical_models.py -v
```
