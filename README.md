# Switzerland Jobs Search 🇨🇭

Automated job search tool using JobSpy to find positions in Switzerland matching Vincenzo Imperati's profile: PhD researcher in distributed systems, blockchain, and social network analysis.

## 👤 Profile: Vincenzo Imperati

### Education
- **PhD in Computer Science** - Sapienza University (Nov 2023 - Oct 2026)
  - Research: User behavior analysis in distributed systems & blockchains
  - Published at **USENIX Security** (121k conspiracy Telegram channels)
- **Visiting PhD Student** - ETH Zurich, Switzerland (Sep 2025 - Oct 2026)
- **MSc Computer Science** - Sapienza University (GPA 3.88/4.0)
- **Outstanding University Student 2025** - Top 400 graduates university-wide

### Experience
- **OpenSats Grant Recipient** (Aug 2025 - Present)
  - Developing Bigbrotr: Full-archive system for Nostr protocol
  - Built nostr-tools Python library
- **Hackathon Team Lead** - 10 prizes in international competitions
- **Data Analyst** - Analyzed 20M+ blockchain transactions
- **Teaching Assistant** - 3 fellowships, taught 200+ students

### Technical Skills
- **Languages**: Python, TypeScript/JavaScript, C, C++, Solidity
- **Frameworks**: React, Node.js, Flask, Docker
- **Databases**: PostgreSQL, MongoDB
- **Specializations**: Distributed Systems, Network Analysis, Data Visualization, Blockchain

### Target Positions
- Research positions (PhD, Postdoc, Visiting Researcher)
- Blockchain & Web3 engineering
- Data science & behavioral analytics
- Software engineering (Backend/Full-stack)
- Summer programs 2026
- Academic/Teaching roles

## 🚀 Quick Start

### Option 1: Using Docker (Recommended)

```bash
# Build and run
docker-compose up --build

# Results will be saved in ./results/ directory
```

### Option 2: Local Python (Requires Python 3.10+)

```bash
# Install dependencies
pip install -r requirements.txt

# Run job search
cd scripts
python search_jobs.py

# Analyze results
python analyze_jobs.py
```

## 📁 Project Structure

```
switzerland-jobs-search/
├── scripts/
│   ├── search_jobs.py      # Main job search script
│   └── analyze_jobs.py     # Results analysis tool
├── results/                # Generated CSV/Excel files (gitignored)
├── config/                 # Configuration files
├── Dockerfile             # Docker container
├── docker-compose.yml     # Docker orchestration
├── requirements.txt       # Python dependencies
└── README.md
```

## 🔍 Search Queries

The tool searches for positions matching Vincenzo's specific background:

### Core Research Areas
- Distributed systems researcher
- Blockchain researcher
- Network analysis
- Social network analysis
- User behavior analysis

### Blockchain & Web3
- Blockchain engineer
- Web3 developer
- Smart contracts, Cryptocurrency
- Nostr protocol
- Decentralized systems

### Research Positions
- PhD researcher / Postdoc
- Research scientist blockchain
- Visiting researcher
- Research associate

### Data Science
- Data scientist/analyst/engineer
- Behavioral analytics
- Network data analysis
- Transaction analysis

### Software Engineering
- Backend engineer (Python)
- Full-stack (TypeScript/React)
- Blockchain software engineer
- Open source developer

### Security & Privacy
- Security researcher
- Privacy engineer
- Cryptography
- Zero-knowledge proofs

### Academic Roles
- Teaching assistant
- University lecturer
- Research associate

### Technology-Specific
- Python/TypeScript/React developer
- Node.js, PostgreSQL, Docker

### Summer/Temporary
- Summer internship 2026
- Research internship
- Temporary researcher positions

## 📍 Locations Searched

- Zurich (primary focus)
- Lausanne (EPFL)
- Geneva
- Bern
- Basel
- General Switzerland

## 🎯 Relevance Scoring

The tool automatically scores jobs based on relevance to Vincenzo's profile:

| Criteria | Score Weight |
|----------|--------------|
| Blockchain & Distributed Systems | +20 |
| PhD/Research positions | +18 |
| Data analysis & User behavior | +15 |
| Summer 2026 programs | +15 |
| Security & Privacy (ZK, Cryptography) | +12 |
| Academic institutions (ETH/EPFL) | +12 |
| ETH Zurich specifically | +10 |
| Social network analysis | +10 |
| Technical stack (Python/TypeScript/React) | +8 |
| Open source development | +8 |
| Teaching positions | +6 |
| Computer Science | +5 |
| Zurich/Lausanne location | +5 |
| Hackathon/Competition | +5 |

Jobs scoring >10 are considered highly relevant and saved separately.

## 📊 Output Files

The tool generates timestamped files in the `results/` directory:

- **all_jobs_[timestamp].csv**: All jobs found
- **all_jobs_[timestamp].xlsx**: Excel format with formatting
- **relevant_jobs_[timestamp].csv**: Filtered highly relevant jobs
- **relevant_jobs_[timestamp].xlsx**: Excel format

## 🔧 Customization

### Modify Search Queries

Edit `scripts/search_jobs.py`, lines 19-76 to adjust the search queries. The current queries are tailored to Vincenzo's research areas and technical skills:

```python
search_queries = [
    # Core Research Areas
    "distributed systems researcher",
    "blockchain researcher",
    # ... add your custom queries
]
```

### Adjust Relevance Scoring

Edit the `calculate_relevance_score()` function in `scripts/search_jobs.py` (lines 175-239) to adjust weights. Current weights prioritize:
- Blockchain/distributed systems (+20)
- PhD/research positions (+18)
- Data analysis (+15)

```python
# Example: Increase blockchain weight
if any(keyword in text for keyword in blockchain_keywords):
    score += 25  # Changed from 20
```

### Filter by Specific Companies

Edit `scripts/analyze_jobs.py`:

```python
target_companies = ['Google', 'ETH Zurich', 'EPFL', 'IBM Research']
export_filtered_by_company(df, target_companies)
```

## 📈 Analysis Features

Run `python analyze_jobs.py` to get:

- **Top Companies Hiring**: Most active recruiters
- **Job Locations**: Geographic distribution
- **Common Keywords**: Trending skills and technologies
- **Salary Information**: If available
- **Job Types**: Full-time, contract, internship breakdown
- **Remote Opportunities**: On-site vs remote distribution

## 🌐 Data Sources

The tool scrapes jobs from:
- LinkedIn
- Indeed
- Glassdoor
- Google Jobs

## ⚠️ Important Notes

1. **Rate Limiting**: JobSpy may hit rate limits on job sites. If you encounter issues:
   - Reduce `results_wanted` parameter (default: 50)
   - Increase delay between searches
   - Run searches at different times

2. **Python Version**: Requires Python 3.10+ (use Docker if you have Python 3.9 or lower)

3. **Results Freshness**: Default search looks at jobs posted in the last 30 days (`hours_old=720`)

4. **Duplicates**: The tool automatically removes duplicate listings based on title, company, and location

## 🔄 Running Periodic Searches

### Using Cron (Linux/Mac)

```bash
# Run daily at 9 AM
0 9 * * * cd /path/to/switzerland-jobs-search && docker-compose up
```

### Manual Scheduling

Run the script manually whenever you want to check for new positions.

## 📝 Example Output

```
🔍 Searching for jobs in Switzerland...
================================================================================

📍 Searching in: Zurich, Switzerland
   - Query: blockchain engineer
      ✅ Found 23 jobs
   - Query: PhD candidate computer science
      ✅ Found 15 jobs

✅ Total job listings found: 342
📊 Removing duplicates...
✅ Unique jobs after deduplication: 187

🔍 Filtering relevant jobs...
✅ Found 45 highly relevant jobs

🎯 TOP 10 MOST RELEVANT JOBS
================================================================================

1. Blockchain Research Scientist
   Company: ETH Zurich
   Location: Zurich, Switzerland
   Relevance Score: 48
   URL: https://...

2. PhD Position - Distributed Systems
   Company: EPFL
   Location: Lausanne, Switzerland
   Relevance Score: 43
   URL: https://...
```

## 🤝 Contributing

Feel free to customize the search queries, scoring algorithm, and analysis features to better match your needs.

## 📄 License

MIT License

## 🆘 Troubleshooting

### Docker Issues

```bash
# Rebuild container
docker-compose down
docker-compose up --build

# View logs
docker-compose logs
```

### Python Issues

```bash
# Check Python version
python3 --version  # Should be 3.10+

# Reinstall dependencies
pip install --upgrade -r requirements.txt
```

### No Results Found

- Check internet connection
- Try fewer search queries
- Increase `hours_old` parameter (search older jobs)
- Check if job sites are blocking requests (try again later)

## 📞 Support

For issues with JobSpy library, visit: https://github.com/speedyapply/JobSpy

---

**Good luck with your job search! 🍀**
