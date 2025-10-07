#!/usr/bin/env python3
"""
Switzerland Jobs Search - PhD & Software Engineering Positions
Searches for blockchain, distributed systems, and data analysis roles in Switzerland
"""

import os
from datetime import datetime
from jobspy import scrape_jobs
import pandas as pd

def search_switzerland_jobs():
    """Search for relevant jobs in Switzerland"""

    print("🔍 Searching for jobs in Switzerland...")
    print("=" * 80)

    # Define search queries tailored to Vincenzo's profile
    search_queries = [
        # Core Research Areas
        "distributed systems researcher",
        "blockchain researcher",
        "network analysis",
        "social network analysis",
        "user behavior analysis",

        # Blockchain & Web3
        "blockchain engineer",
        "web3 developer",
        "smart contracts",
        "cryptocurrency",
        "Nostr protocol",
        "decentralized systems",

        # PhD & Research positions
        "PhD researcher computer science",
        "postdoc distributed systems",
        "research scientist blockchain",
        "visiting researcher",

        # Data Science & Analysis
        "data scientist",
        "data analyst",
        "data engineer",
        "behavioral analytics",
        "network data analysis",

        # Software Engineering (Python, TypeScript, C++)
        "backend engineer Python",
        "full-stack TypeScript",
        "software engineer blockchain",
        "open source developer",

        # Security & Privacy
        "security researcher",
        "privacy engineer",
        "cryptography",
        "zero knowledge proofs",

        # Academic & Teaching
        "teaching assistant computer science",
        "university lecturer",
        "research associate",

        # Specific Technologies from CV
        "Python developer",
        "React developer",
        "Node.js",
        "PostgreSQL",
        "Docker",

        # Summer/Temporary Positions
        "summer internship 2026",
        "research internship",
        "temporary researcher"
    ]

    # Swiss cities to search
    locations = [
        "Zurich, Switzerland",
        "Lausanne, Switzerland",
        "Geneva, Switzerland",
        "Bern, Switzerland",
        "Basel, Switzerland",
        "Switzerland"  # General Switzerland search
    ]

    all_jobs = []

    for location in locations:
        print(f"\n📍 Searching in: {location}")

        for query in search_queries:
            try:
                print(f"   - Query: {query}")

                jobs = scrape_jobs(
                    site_name=["indeed", "linkedin", "glassdoor", "google"],
                    search_term=query,
                    location=location,
                    results_wanted=50,
                    hours_old=720,  # Last 30 days
                    country_indeed='Switzerland',
                    linkedin_fetch_description=True,
                    # Filters
                    job_type="fulltime",  # Can also search: internship, contract
                    is_remote=None,  # Include both remote and on-site
                )

                if jobs is not None and len(jobs) > 0:
                    jobs['search_query'] = query
                    jobs['search_location'] = location
                    jobs['search_date'] = datetime.now().strftime('%Y-%m-%d')
                    all_jobs.append(jobs)
                    print(f"      ✅ Found {len(jobs)} jobs")
                else:
                    print(f"      ⚠️ No jobs found")

            except Exception as e:
                print(f"      ❌ Error: {e}")
                continue

    if not all_jobs:
        print("\n❌ No jobs found. Please check your internet connection or try again later.")
        return None

    # Combine all results
    print(f"\n✅ Total job listings found: {sum(len(df) for df in all_jobs)}")
    combined_jobs = pd.concat(all_jobs, ignore_index=True)

    # Remove duplicates based on job title and company
    print(f"📊 Removing duplicates...")
    combined_jobs = combined_jobs.drop_duplicates(
        subset=['title', 'company', 'location'],
        keep='first'
    )
    print(f"✅ Unique jobs after deduplication: {len(combined_jobs)}")

    return combined_jobs


def filter_relevant_jobs(jobs_df):
    """Filter jobs based on relevance to Vincenzo's profile"""

    print("\n🔍 Filtering relevant jobs...")
    print("=" * 80)

    # Keywords matching Vincenzo's CV
    phd_keywords = ['phd', 'doctoral', 'research', 'postdoc', 'scientist', 'researcher',
                    'visiting', 'academic']

    blockchain_keywords = ['blockchain', 'crypto', 'distributed', 'web3', 'ethereum',
                           'bitcoin', 'smart contract', 'defi', 'consensus', 'nostr',
                           'decentralized', 'peer-to-peer', 'p2p']

    data_keywords = ['data', 'analysis', 'analytics', 'behavior', 'behavioral',
                    'network analysis', 'visualization', 'mining', 'transaction',
                    'pattern', 'graph', 'user behavior']

    security_keywords = ['security', 'privacy', 'cryptography', 'encryption',
                        'zero-knowledge', 'zk', 'homomorphic', 'usenix']

    social_keywords = ['social network', 'telegram', 'community', 'user engagement',
                      'monetization', 'social media']

    tech_keywords = ['python', 'typescript', 'javascript', 'react', 'node.js',
                    'postgresql', 'mongodb', 'docker', 'c++', 'solidity']

    summer_keywords = ['summer', '2026', 'intern', 'temporary', 'short-term']

    # Academic institutions (high value for Vincenzo)
    academic_keywords = ['eth zurich', 'epfl', 'university', 'institute', 'academia',
                        'sapienza']

    def calculate_relevance_score(row):
        """Calculate relevance score based on Vincenzo's profile"""
        score = 0
        text = (str(row.get('title', '')) + ' ' +
                str(row.get('description', '')) + ' ' +
                str(row.get('company', ''))).lower()

        # Core strengths - highest priority
        # Distributed systems & Blockchain (Vincenzo's PhD focus)
        if any(keyword in text for keyword in blockchain_keywords):
            score += 20

        # Data analysis & user behavior (published USENIX research)
        if any(keyword in text for keyword in data_keywords):
            score += 15

        # PhD/Research positions (currently PhD at Sapienza, visiting ETH)
        if any(keyword in text for keyword in phd_keywords):
            score += 18

        # Security & Privacy (zk proofs, homomorphic encryption experience)
        if any(keyword in text for keyword in security_keywords):
            score += 12

        # Social network analysis (Telegram research published)
        if any(keyword in text for keyword in social_keywords):
            score += 10

        # Technical skills matching CV
        if any(keyword in text for keyword in tech_keywords):
            score += 8

        # Summer programs (graduating Oct 2026)
        if any(keyword in text for keyword in summer_keywords):
            score += 15

        # Academic institutions (currently at ETH Zurich)
        if any(keyword in text for keyword in academic_keywords):
            score += 12

        # Open source (OpenSats grant recipient)
        if 'open source' in text or 'opensource' in text:
            score += 8

        # Hackathon/competition winner
        if 'hackathon' in text or 'competition' in text:
            score += 5

        # Teaching experience (3 fellowships)
        if 'teaching' in text or 'lecturer' in text:
            score += 6

        # Computer Science
        if 'computer science' in text:
            score += 5

        # Switzerland location bonus (currently at ETH Zurich)
        if 'zurich' in text or 'zürich' in text:
            score += 5
        elif 'lausanne' in text or 'epfl' in text:
            score += 5
        elif 'eth zurich' in text or 'eth zürich' in text:
            score += 10  # Extra bonus for ETH

        return score

    # Calculate scores
    jobs_df['relevance_score'] = jobs_df.apply(calculate_relevance_score, axis=1)

    # Filter jobs with score > 10
    relevant_jobs = jobs_df[jobs_df['relevance_score'] > 10].copy()
    relevant_jobs = relevant_jobs.sort_values('relevance_score', ascending=False)

    print(f"✅ Found {len(relevant_jobs)} highly relevant jobs")

    return relevant_jobs


def save_results(jobs_df, filename_prefix='jobs'):
    """Save results to CSV and Excel"""

    os.makedirs('../results', exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    # Save to CSV
    csv_path = f'../results/{filename_prefix}_{timestamp}.csv'
    jobs_df.to_csv(csv_path, index=False)
    print(f"💾 Saved to CSV: {csv_path}")

    # Save to Excel with formatting
    try:
        excel_path = f'../results/{filename_prefix}_{timestamp}.xlsx'
        with pd.ExcelWriter(excel_path, engine='openpyxl') as writer:
            jobs_df.to_excel(writer, index=False, sheet_name='Jobs')

            # Auto-adjust column widths
            worksheet = writer.sheets['Jobs']
            for idx, col in enumerate(jobs_df.columns):
                max_length = max(
                    jobs_df[col].astype(str).map(len).max(),
                    len(str(col))
                )
                worksheet.column_dimensions[chr(65 + idx)].width = min(max_length + 2, 50)

        print(f"💾 Saved to Excel: {excel_path}")
    except Exception as e:
        print(f"⚠️ Could not save Excel file: {e}")

    return csv_path


def main():
    """Main execution function"""

    print("""
    ╔════════════════════════════════════════════════════════════════════╗
    ║          Switzerland Jobs Search - Vincenzo Imperati               ║
    ║                                                                    ║
    ║  Profile:                                                          ║
    ║  • PhD Candidate @ Sapienza University (Nov 2023 - Oct 2026)     ║
    ║  • Visiting PhD @ ETH Zurich (Sep 2025 - Oct 2026)                ║
    ║  • Research: User behavior in distributed systems & blockchains   ║
    ║  • Published: USENIX Security (Telegram conspiracy channels)      ║
    ║  • OpenSats Grant: Nostr protocol development                     ║
    ║  • Skills: Python, TypeScript, C++, React, Data Analysis          ║
    ║  • Target: Research, Software Engineering, Summer 2026 positions  ║
    ╚════════════════════════════════════════════════════════════════════╝
    """)

    # Search for jobs
    all_jobs = search_switzerland_jobs()

    if all_jobs is None or len(all_jobs) == 0:
        print("\n❌ No jobs found. Exiting.")
        return

    # Save all results
    print("\n💾 Saving all results...")
    save_results(all_jobs, 'all_jobs')

    # Filter relevant jobs
    relevant_jobs = filter_relevant_jobs(all_jobs)

    if len(relevant_jobs) == 0:
        print("\n⚠️ No highly relevant jobs found after filtering.")
        print("💡 Tip: Check the 'all_jobs' file for broader results.")
        return

    # Save filtered results
    print("\n💾 Saving filtered results...")
    save_results(relevant_jobs, 'relevant_jobs')

    # Display top matches
    print("\n" + "=" * 80)
    print("🎯 TOP 10 MOST RELEVANT JOBS")
    print("=" * 80)

    for idx, row in relevant_jobs.head(10).iterrows():
        print(f"\n{idx + 1}. {row['title']}")
        print(f"   Company: {row['company']}")
        print(f"   Location: {row['location']}")
        print(f"   Relevance Score: {row['relevance_score']}")
        if pd.notna(row.get('job_url')):
            print(f"   URL: {row['job_url']}")

    print("\n" + "=" * 80)
    print("✅ Job search complete!")
    print(f"📊 Total unique jobs: {len(all_jobs)}")
    print(f"🎯 Highly relevant jobs: {len(relevant_jobs)}")
    print("\n💡 Check the 'results' folder for detailed CSV and Excel files.")


if __name__ == "__main__":
    main()
