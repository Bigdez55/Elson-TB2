#!/usr/bin/env python3
"""
Curriculum Sampler for Elson Financial AI

Creates training manifests with controlled domain and difficulty distributions.
Implements the three-phase curriculum approach:
- Phase A: Domain blocks (train one domain at a time)
- Phase B: Mixed curriculum (balanced across all domains)
- Phase C: Stress epoch (heavy on complex scenarios)

Usage:
    python scripts/curriculum_sampler.py --phase A --domain federal_income_tax
    python scripts/curriculum_sampler.py --phase B --target-records 10000
    python scripts/curriculum_sampler.py --phase C --stress-ratio 0.3
    python scripts/curriculum_sampler.py --config curriculum_config.yaml

Output:
    - training_manifest.jsonl: File paths and indices for training
    - merged_training.jsonl: Pre-merged training data
    - manifest_stats.json: Statistics about the manifest
"""

import argparse
import json
import os
import random
import yaml
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict

# Paths
DEFAULT_BUCKETS_DIR = Path(__file__).parent.parent / "backend" / "training_data" / "domain_buckets"
DEFAULT_OUTPUT_DIR = Path(__file__).parent.parent / "backend" / "training_data" / "curriculum_runs"

# Difficulty tiers
DIFFICULTY_TIERS = ["easy", "medium", "hard", "extremely_complex"]


# =============================================================================
# CONFIGURATION
# =============================================================================

@dataclass
class PhaseAConfig:
    """Configuration for Phase A: Domain Blocks"""
    tier_mix: Dict[str, float] = None  # Difficulty tier percentages
    domain_quota: int = 1000  # Target examples per domain
    domains: Optional[List[str]] = None  # Specific domains to train (None = all)

    def __post_init__(self):
        if self.tier_mix is None:
            self.tier_mix = {
                "easy": 0.35,
                "medium": 0.35,
                "hard": 0.25,
                "extremely_complex": 0.05,
            }


@dataclass
class PhaseBConfig:
    """Configuration for Phase B: Mixed Curriculum"""
    tier_mix: Dict[str, float] = None
    domain_cap: float = 0.15  # Max percentage for any domain
    target_records: int = 10000

    def __post_init__(self):
        if self.tier_mix is None:
            self.tier_mix = {
                "easy": 0.20,
                "medium": 0.40,
                "hard": 0.30,
                "extremely_complex": 0.10,
            }


@dataclass
class PhaseCConfig:
    """Configuration for Phase C: Stress Epoch"""
    extreme_ratio: float = 0.30
    tier_mix: Dict[str, float] = None
    focus_multi_domain: bool = True
    focus_compliance: bool = True
    target_records: int = 5000

    def __post_init__(self):
        if self.tier_mix is None:
            self.tier_mix = {
                "easy": 0.10,
                "medium": 0.25,
                "hard": 0.35,
                "extremely_complex": 0.30,
            }


@dataclass
class CurriculumConfig:
    """Full curriculum configuration"""
    phase_a: PhaseAConfig = None
    phase_b: PhaseBConfig = None
    phase_c: PhaseCConfig = None
    seed: int = 42

    def __post_init__(self):
        if self.phase_a is None:
            self.phase_a = PhaseAConfig()
        if self.phase_b is None:
            self.phase_b = PhaseBConfig()
        if self.phase_c is None:
            self.phase_c = PhaseCConfig()


# =============================================================================
# MANIFEST ENTRY
# =============================================================================

@dataclass
class ManifestEntry:
    """Entry in the training manifest"""
    source_file: str
    line_index: int
    domain: str
    difficulty: str
    task_type: Optional[str] = None
    risk_level: Optional[str] = None


# =============================================================================
# BUCKET LOADER
# =============================================================================

class BucketLoader:
    """Loads domain buckets from the filesystem"""

    def __init__(self, buckets_dir: Path):
        self.buckets_dir = buckets_dir
        self.manifest_path = buckets_dir / "manifest.json"
        self.manifest = self._load_manifest()
        self._cache = {}  # Cache loaded examples

    def _load_manifest(self) -> Dict:
        """Load the bucket manifest"""
        if not self.manifest_path.exists():
            raise FileNotFoundError(f"Bucket manifest not found: {self.manifest_path}")

        with open(self.manifest_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_domains(self) -> List[str]:
        """Get list of all domains"""
        return list(self.manifest.get("domains", {}).keys())

    def get_domain_stats(self, domain: str) -> Dict:
        """Get statistics for a domain"""
        return self.manifest.get("domains", {}).get(domain, {})

    def load_bucket(self, domain: str, difficulty: str) -> List[Tuple[Dict, int]]:
        """
        Load examples from a specific bucket.

        Returns list of (example, line_index) tuples for manifest tracking.
        """
        cache_key = f"{domain}/{difficulty}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        bucket_file = self.buckets_dir / domain / f"{difficulty}.jsonl"
        if not bucket_file.exists():
            return []

        examples = []
        with open(bucket_file, 'r', encoding='utf-8') as f:
            for idx, line in enumerate(f):
                if line.strip():
                    try:
                        example = json.loads(line)
                        examples.append((example, idx))
                    except json.JSONDecodeError:
                        continue

        self._cache[cache_key] = examples
        return examples

    def get_bucket_count(self, domain: str, difficulty: str) -> int:
        """Get the count of examples in a bucket without loading"""
        stats = self.get_domain_stats(domain)
        return stats.get("by_difficulty", {}).get(difficulty, 0)


# =============================================================================
# CURRICULUM SAMPLER
# =============================================================================

class CurriculumSampler:
    """Generates training manifests based on curriculum configuration"""

    def __init__(self, buckets_dir: Path, seed: int = 42):
        self.loader = BucketLoader(buckets_dir)
        self.seed = seed
        self.rng = random.Random(seed)

    def sample_phase_a(
        self,
        config: PhaseAConfig,
        domain: Optional[str] = None
    ) -> Tuple[List[ManifestEntry], Dict]:
        """
        Phase A: Domain Blocks

        Train one domain at a time until it hits competence minimums.
        Tier mix: 70% easy+medium, 25% hard, 5% extreme
        """
        domains = [domain] if domain else (config.domains or self.loader.get_domains())
        manifest_entries = []
        stats = {"phase": "A", "domains": {}, "total": 0}

        for dom in domains:
            domain_entries = []
            tier_counts = {t: 0 for t in DIFFICULTY_TIERS}

            # Calculate target per tier
            targets = {
                tier: int(config.domain_quota * pct)
                for tier, pct in config.tier_mix.items()
            }

            for tier in DIFFICULTY_TIERS:
                bucket = self.loader.load_bucket(dom, tier)
                target = targets.get(tier, 0)

                if not bucket:
                    continue

                # Sample up to target
                sample_count = min(len(bucket), target)
                sampled = self.rng.sample(bucket, sample_count)

                for example, idx in sampled:
                    entry = ManifestEntry(
                        source_file=f"{dom}/{tier}.jsonl",
                        line_index=idx,
                        domain=dom,
                        difficulty=tier,
                        task_type=example.get("task_type"),
                        risk_level=example.get("risk_level"),
                    )
                    domain_entries.append(entry)
                    tier_counts[tier] += 1

            # Shuffle within domain
            self.rng.shuffle(domain_entries)
            manifest_entries.extend(domain_entries)

            stats["domains"][dom] = {
                "total": len(domain_entries),
                "by_difficulty": tier_counts,
            }

        stats["total"] = len(manifest_entries)
        return manifest_entries, stats

    def sample_phase_b(self, config: PhaseBConfig) -> Tuple[List[ManifestEntry], Dict]:
        """
        Phase B: Mixed Curriculum

        Shuffle domains to force generalization and cross-domain reasoning.
        Batch composition: 40% medium, 30% hard, 20% easy, 10% extreme
        Domain weights capped so no domain exceeds 15% effective sampling.
        """
        domains = self.loader.get_domains()
        manifest_entries = []
        stats = {"phase": "B", "by_difficulty": {t: 0 for t in DIFFICULTY_TIERS},
                "by_domain": defaultdict(int), "total": 0}

        # Calculate target per tier
        tier_targets = {
            tier: int(config.target_records * pct)
            for tier, pct in config.tier_mix.items()
        }

        # Calculate per-domain cap
        domain_cap_count = int(config.target_records * config.domain_cap)

        # Pool examples by tier
        tier_pools = {tier: [] for tier in DIFFICULTY_TIERS}
        domain_counts = defaultdict(int)

        for domain in domains:
            for tier in DIFFICULTY_TIERS:
                bucket = self.loader.load_bucket(domain, tier)
                for example, idx in bucket:
                    tier_pools[tier].append((domain, example, idx))

        # Shuffle each tier pool
        for tier in DIFFICULTY_TIERS:
            self.rng.shuffle(tier_pools[tier])

        # Sample from each tier respecting domain caps
        for tier in DIFFICULTY_TIERS:
            target = tier_targets.get(tier, 0)
            pool = tier_pools[tier]
            sampled = 0

            for domain, example, idx in pool:
                if sampled >= target:
                    break

                # Check domain cap
                if domain_counts[domain] >= domain_cap_count:
                    continue

                entry = ManifestEntry(
                    source_file=f"{domain}/{tier}.jsonl",
                    line_index=idx,
                    domain=domain,
                    difficulty=tier,
                    task_type=example.get("task_type"),
                    risk_level=example.get("risk_level"),
                )
                manifest_entries.append(entry)
                domain_counts[domain] += 1
                stats["by_difficulty"][tier] += 1
                sampled += 1

        # Shuffle final manifest
        self.rng.shuffle(manifest_entries)

        stats["by_domain"] = dict(domain_counts)
        stats["total"] = len(manifest_entries)
        return manifest_entries, stats

    def sample_phase_c(self, config: PhaseCConfig) -> Tuple[List[ManifestEntry], Dict]:
        """
        Phase C: Stress Epoch

        30% of batches are extremely complex, mostly multi-domain and compliance-heavy.
        Focus on high-risk scenarios.
        """
        domains = self.loader.get_domains()
        manifest_entries = []
        stats = {"phase": "C", "by_difficulty": {t: 0 for t in DIFFICULTY_TIERS},
                "by_domain": defaultdict(int), "total": 0,
                "multi_domain": 0, "compliance": 0}

        # Identify high-risk domains
        high_risk_domains = {
            "compliance", "securities_regulation", "aml_kyc", "federal_income_tax",
            "insurance", "derivatives", "estate_planning", "trade_execution"
        }

        # Calculate tier targets with extreme emphasis
        tier_targets = {
            tier: int(config.target_records * pct)
            for tier, pct in config.tier_mix.items()
        }

        # Pool examples with priority for high-risk
        all_examples = []

        for domain in domains:
            is_high_risk = domain in high_risk_domains

            for tier in DIFFICULTY_TIERS:
                bucket = self.loader.load_bucket(domain, tier)
                for example, idx in bucket:
                    priority = 1.0
                    # Boost high-risk domains
                    if is_high_risk:
                        priority *= 2.0
                    # Boost complex tiers
                    if tier in ["hard", "extremely_complex"]:
                        priority *= 1.5
                    # Boost compliance-related
                    if example.get("risk_level") == "high":
                        priority *= 1.5

                    all_examples.append((domain, tier, example, idx, priority))

        # Sort by priority (descending) then shuffle within priority bands
        all_examples.sort(key=lambda x: -x[4])

        # Sample with tier distribution
        tier_counts = {t: 0 for t in DIFFICULTY_TIERS}
        domain_counts = defaultdict(int)

        for domain, tier, example, idx, priority in all_examples:
            if len(manifest_entries) >= config.target_records:
                break

            # Check tier quota
            if tier_counts[tier] >= tier_targets.get(tier, 0):
                continue

            entry = ManifestEntry(
                source_file=f"{domain}/{tier}.jsonl",
                line_index=idx,
                domain=domain,
                difficulty=tier,
                task_type=example.get("task_type"),
                risk_level=example.get("risk_level"),
            )
            manifest_entries.append(entry)
            tier_counts[tier] += 1
            domain_counts[domain] += 1

            # Track special categories
            if example.get("risk_level") == "high":
                stats["compliance"] += 1
            if example.get("requires_tools") or example.get("requires_retrieval"):
                stats["multi_domain"] += 1

        # Shuffle
        self.rng.shuffle(manifest_entries)

        stats["by_difficulty"] = tier_counts
        stats["by_domain"] = dict(domain_counts)
        stats["total"] = len(manifest_entries)
        return manifest_entries, stats


# =============================================================================
# OUTPUT GENERATION
# =============================================================================

def save_manifest(
    entries: List[ManifestEntry],
    stats: Dict,
    output_dir: Path,
    phase: str,
    buckets_dir: Path,
    merge_data: bool = True
) -> Dict[str, Path]:
    """Save manifest and optionally merge training data"""
    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_files = {}

    # Save manifest
    manifest_path = output_dir / f"manifest_phase{phase}_{timestamp}.jsonl"
    with open(manifest_path, 'w', encoding='utf-8') as f:
        for entry in entries:
            f.write(json.dumps(asdict(entry)) + '\n')
    output_files["manifest"] = manifest_path

    # Save stats
    stats["timestamp"] = datetime.now().isoformat()
    stats["seed"] = entries[0].source_file if entries else None  # For reproducibility tracking
    stats_path = output_dir / f"manifest_stats_phase{phase}_{timestamp}.json"
    with open(stats_path, 'w', encoding='utf-8') as f:
        json.dump(stats, f, indent=2)
    output_files["stats"] = stats_path

    # Optionally merge data
    if merge_data:
        merged_path = output_dir / f"merged_phase{phase}_{timestamp}.jsonl"
        with open(merged_path, 'w', encoding='utf-8') as f:
            for entry in entries:
                source_path = buckets_dir / entry.source_file
                if source_path.exists():
                    with open(source_path, 'r', encoding='utf-8') as sf:
                        lines = sf.readlines()
                        if entry.line_index < len(lines):
                            f.write(lines[entry.line_index])
        output_files["merged"] = merged_path

    return output_files


def print_stats(stats: Dict, phase: str):
    """Print statistics summary"""
    print("\n" + "=" * 60)
    print(f"PHASE {phase} SAMPLING COMPLETE")
    print("=" * 60)

    print(f"\nTotal Examples: {stats['total']:,}")

    if "by_difficulty" in stats:
        print("\nBy Difficulty:")
        for tier in DIFFICULTY_TIERS:
            count = stats["by_difficulty"].get(tier, 0)
            pct = 100 * count / stats["total"] if stats["total"] > 0 else 0
            print(f"  {tier}: {count:,} ({pct:.1f}%)")

    if "by_domain" in stats:
        print("\nTop 10 Domains:")
        sorted_domains = sorted(stats["by_domain"].items(), key=lambda x: -x[1])[:10]
        for domain, count in sorted_domains:
            pct = 100 * count / stats["total"] if stats["total"] > 0 else 0
            print(f"  {domain}: {count:,} ({pct:.1f}%)")

    if "compliance" in stats:
        print(f"\nCompliance-heavy examples: {stats['compliance']:,}")

    if "multi_domain" in stats:
        print(f"Multi-domain/tool examples: {stats['multi_domain']:,}")


# =============================================================================
# MAIN
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="Generate curriculum training manifests")
    parser.add_argument("--buckets-dir", type=str, default=str(DEFAULT_BUCKETS_DIR),
                       help="Directory containing domain buckets")
    parser.add_argument("--output-dir", type=str, default=str(DEFAULT_OUTPUT_DIR),
                       help="Output directory for manifests")
    parser.add_argument("--phase", type=str, choices=["A", "B", "C", "all"], default="B",
                       help="Curriculum phase to generate")
    parser.add_argument("--domain", type=str, default=None,
                       help="Specific domain for Phase A")
    parser.add_argument("--target-records", type=int, default=10000,
                       help="Target number of records")
    parser.add_argument("--seed", type=int, default=42,
                       help="Random seed for reproducibility")
    parser.add_argument("--config", type=str, default=None,
                       help="YAML config file (overrides other args)")
    parser.add_argument("--no-merge", action="store_true",
                       help="Don't merge data, only create manifest")
    args = parser.parse_args()

    buckets_dir = Path(args.buckets_dir)
    output_dir = Path(args.output_dir)

    print("=" * 60)
    print("Elson Financial AI - Curriculum Sampler")
    print("=" * 60)
    print(f"Timestamp: {datetime.now().isoformat()}")
    print(f"Buckets: {buckets_dir}")
    print(f"Output: {output_dir}")
    print(f"Phase: {args.phase}")
    print(f"Seed: {args.seed}")

    # Load config if provided
    if args.config:
        with open(args.config, 'r') as f:
            config_data = yaml.safe_load(f)
        config = CurriculumConfig(**config_data)
    else:
        config = CurriculumConfig(seed=args.seed)

    # Initialize sampler
    sampler = CurriculumSampler(buckets_dir, seed=args.seed)

    phases_to_run = ["A", "B", "C"] if args.phase == "all" else [args.phase]

    for phase in phases_to_run:
        print(f"\n[PHASE {phase}] Generating manifest...")

        if phase == "A":
            config.phase_a.domain_quota = args.target_records
            entries, stats = sampler.sample_phase_a(config.phase_a, domain=args.domain)
        elif phase == "B":
            config.phase_b.target_records = args.target_records
            entries, stats = sampler.sample_phase_b(config.phase_b)
        else:  # Phase C
            config.phase_c.target_records = args.target_records
            entries, stats = sampler.sample_phase_c(config.phase_c)

        # Save outputs
        output_files = save_manifest(
            entries, stats, output_dir, phase, buckets_dir,
            merge_data=not args.no_merge
        )

        print_stats(stats, phase)

        print(f"\nOutput files:")
        for name, path in output_files.items():
            print(f"  {name}: {path}")

    print("\nDone!")


if __name__ == "__main__":
    main()
