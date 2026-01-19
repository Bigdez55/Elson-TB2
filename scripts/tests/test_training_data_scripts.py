#!/usr/bin/env python3
"""
Unit tests for Elson TB2 training data scripts.

Tests:
1. augment_training_data.py
2. domain_classifier.py
3. validate_training_data.py
4. merge_all_training_data.py
"""

import json
import sys
import tempfile
from pathlib import Path
import pytest

# Add scripts directory to path
scripts_dir = Path(__file__).parent.parent
sys.path.insert(0, str(scripts_dir))

# Import modules to test
from augment_training_data import (
    generate_hash,
    paraphrase_question,
    scale_difficulty,
    inject_scenario,
    augment_dataset
)
from domain_classifier import (
    classify_text,
    classify_qa_pair,
    DOMAIN_TAXONOMY
)
from validate_training_data import (
    validate_json_structure,
    validate_field_lengths,
    check_duplicates,
    check_unsafe_content
)
from merge_all_training_data import (
    normalize_pair,
    load_json_file
)


class TestAugmentTrainingData:
    """Tests for augment_training_data.py"""

    def test_generate_hash(self):
        """Test hash generation is consistent and unique."""
        hash1 = generate_hash("test input")
        hash2 = generate_hash("test input")
        hash3 = generate_hash("different input")

        assert hash1 == hash2, "Same input should produce same hash"
        assert hash1 != hash3, "Different input should produce different hash"
        assert len(hash1) == 12, "Hash should be 12 characters"

    def test_paraphrase_question(self):
        """Test paraphrasing produces variations."""
        original = "What is a 401(k) retirement account?"
        paraphrased = paraphrase_question(original)

        assert isinstance(paraphrased, list), "Should return list"
        assert len(paraphrased) >= 1, "Should return at least one paraphrase"

    def test_scale_difficulty(self):
        """Test difficulty variant generation."""
        pair = {
            "instruction": "What is a 401(k)?",
            "output": "A 401(k) is a retirement savings plan.",
            "category": "retirement_planning"
        }

        variants = scale_difficulty(pair)

        assert len(variants) >= 2, "Should generate at least 2 difficulty variants"
        difficulties = [v.get("difficulty") for v in variants]
        assert any("beginner" in str(d).lower() for d in difficulties if d)

    def test_inject_scenario(self):
        """Test scenario variant generation."""
        pair = {
            "instruction": "How do I save for retirement?",
            "output": "Start by contributing to a 401(k).",
            "category": "retirement_planning"
        }

        variants = inject_scenario(pair)

        assert len(variants) >= 1, "Should generate at least 1 scenario variant"

    def test_augment_dataset(self):
        """Test full dataset augmentation."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            test_data = [
                {
                    "instruction": "What is a 401(k)?",
                    "output": "A 401(k) is a retirement savings plan.",
                    "category": "retirement_planning"
                },
                {
                    "instruction": "What is an IRA?",
                    "output": "An IRA is an Individual Retirement Account.",
                    "category": "retirement_planning"
                }
            ]
            json.dump(test_data, f)
            input_path = f.name

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            output_path = f.name

        stats = augment_dataset(input_path, output_path, target_multiplier=2.0)

        assert stats["original_count"] == 2
        assert stats["augmented_count"] >= 2
        assert stats["multiplier"] >= 1.0


class TestDomainClassifier:
    """Tests for domain_classifier.py"""

    def test_classify_text_retirement(self):
        """Test classification of retirement content."""
        text = "What are the contribution limits for a 401(k) retirement account?"
        domain, confidence, matches = classify_text(text)

        assert domain is not None, "Should return a domain"
        assert confidence >= 0, "Confidence should be non-negative"
        assert isinstance(matches, list), "Should return list of matches"

    def test_classify_text_tax(self):
        """Test classification of tax content."""
        text = "What are the federal income tax brackets for 2026?"
        domain, confidence, matches = classify_text(text)

        assert domain is not None, "Should return a domain"

    def test_classify_text_estate(self):
        """Test classification of estate planning content."""
        text = "How do I set up a revocable living trust for estate planning?"
        domain, confidence, matches = classify_text(text)

        assert domain is not None, "Should return a domain"

    def test_classify_qa_pair(self):
        """Test QA pair classification."""
        pair = {
            "instruction": "What is a 401(k)?",
            "output": "A 401(k) is a retirement savings plan.",
            "category": "general_finance"
        }

        classified = classify_qa_pair(pair)

        assert "category" in classified
        assert "domain_confidence" in classified

    def test_domain_taxonomy_completeness(self):
        """Test that domain taxonomy has expected domains."""
        assert len(DOMAIN_TAXONOMY) >= 50, "Should have at least 50 domain entries"


class TestValidateTrainingData:
    """Tests for validate_training_data.py"""

    def test_validate_json_structure_valid(self):
        """Test validation of valid JSON structure."""
        data = [
            {"instruction": "Test?", "output": "Answer."},
            {"instruction": "Test2?", "output": "Answer2."}
        ]

        is_valid, errors = validate_json_structure(data)

        assert is_valid
        assert len(errors) == 0

    def test_validate_json_structure_missing_fields(self):
        """Test validation catches missing fields."""
        data = [
            {"instruction": "Test?"},  # Missing output
            {"output": "Answer."}  # Missing instruction
        ]

        is_valid, errors = validate_json_structure(data)

        assert not is_valid
        assert len(errors) == 2

    def test_validate_field_lengths(self):
        """Test field length validation."""
        data = [
            {"instruction": "Short question?", "output": "This is a reasonable length answer that provides useful information."},
            {"instruction": "", "output": ""}  # Empty fields
        ]

        is_valid, errors, stats = validate_field_lengths(data)

        assert not is_valid  # Should fail due to empty fields
        assert stats["empty_instructions"] == 1
        assert stats["empty_outputs"] == 1

    def test_check_duplicates(self):
        """Test duplicate detection."""
        data = [
            {"instruction": "What is X?", "output": "X is Y."},
            {"instruction": "What is X?", "output": "X is Y."},  # Duplicate
            {"instruction": "What is Z?", "output": "Z is A."}
        ]

        is_valid, errors, stats = check_duplicates(data)

        assert stats["duplicate_pairs"] == 1
        assert stats["unique_pairs"] == 2

    def test_check_unsafe_content(self):
        """Test unsafe content detection."""
        data = [
            {"instruction": "What is a safe investment?", "output": "Diversification is key."},
            {"instruction": "How do I get guaranteed returns?", "output": "Invest in this get rich quick scheme!"}
        ]

        is_valid, warnings, stats = check_unsafe_content(data)

        assert stats["flagged_count"] >= 1


class TestMergeTrainingData:
    """Tests for merge_all_training_data.py"""

    def test_normalize_pair(self):
        """Test pair normalization."""
        pair = {
            "question": "What is X?",
            "answer": "X is Y.",
            "domain": "test_domain"
        }

        normalized = normalize_pair(pair, "test_source")

        assert "instruction" in normalized
        assert "output" in normalized
        assert "category" in normalized
        assert "source" in normalized
        assert normalized["instruction"] == "What is X?"
        assert normalized["output"] == "X is Y."
        assert normalized["source"] == "test_source"

    def test_load_json_file_array(self):
        """Test loading JSON array file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{"a": 1}, {"b": 2}], f)
            path = Path(f.name)

        data = load_json_file(path)

        assert len(data) == 2
        assert data[0]["a"] == 1

    def test_load_json_file_jsonl(self):
        """Test loading JSONL file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"a": 1}\n')
            f.write('{"b": 2}\n')
            path = Path(f.name)

        data = load_json_file(path)

        assert len(data) == 2

    def test_load_json_file_not_found(self):
        """Test loading non-existent file."""
        path = Path("/nonexistent/file.json")
        data = load_json_file(path)

        assert data == []


class TestIntegration:
    """Integration tests across multiple scripts."""

    def test_full_pipeline(self):
        """Test a simple version of the full pipeline."""
        # Create sample training data
        sample_data = [
            {
                "instruction": "What is a 401(k) retirement plan?",
                "output": "A 401(k) is an employer-sponsored retirement savings plan that allows employees to contribute a portion of their salary on a pre-tax basis. Employers may also match contributions up to a certain percentage.",
                "category": "retirement_planning"
            },
            {
                "instruction": "What are the tax benefits of a traditional IRA?",
                "output": "Traditional IRA contributions may be tax-deductible, and earnings grow tax-deferred until withdrawal in retirement. This can result in significant tax savings over time.",
                "category": "retirement_planning"
            },
            {
                "instruction": "How does estate planning work?",
                "output": "Estate planning involves creating legal documents like wills and trusts to manage how your assets will be distributed after death. It also includes strategies to minimize estate taxes and ensure your wishes are followed.",
                "category": "estate_planning"
            }
        ]

        # Test validation
        is_valid, errors = validate_json_structure(sample_data)
        assert is_valid, f"Validation failed: {errors}"

        # Test domain classification
        for item in sample_data:
            domain, confidence, matches = classify_text(item["instruction"])
            assert domain is not None

        # Test normalization
        for item in sample_data:
            normalized = normalize_pair(item, "test")
            assert normalized["instruction"]
            assert normalized["output"]

        # Test hash generation
        hashes = [generate_hash(item["instruction"] + item["output"]) for item in sample_data]
        assert len(set(hashes)) == len(hashes), "All hashes should be unique"


def run_all_tests():
    """Run all tests and return results."""
    pytest.main([__file__, "-v", "--tb=short"])


if __name__ == "__main__":
    run_all_tests()
