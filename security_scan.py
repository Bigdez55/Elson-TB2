#!/usr/bin/env python3
"""
Comprehensive Security Vulnerability Scanner
Scans for OWASP Top 10 and common security issues
"""

import os
import re
import json
from pathlib import Path
from typing import List, Dict, Tuple

class SecurityScanner:
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.vulnerabilities = []

    def scan_all(self):
        """Run all security scans"""
        print("=" * 60)
        print("COMPREHENSIVE SECURITY VULNERABILITY SCAN")
        print("=" * 60)

        self.scan_hardcoded_secrets()
        self.scan_sql_injection()
        self.scan_command_injection()
        self.scan_path_traversal()
        self.scan_insecure_random()
        self.scan_weak_crypto()
        self.scan_xss_vulnerabilities()
        self.scan_insecure_deserialization()

        return self.generate_report()

    def scan_hardcoded_secrets(self):
        """Scan for hardcoded secrets, API keys, passwords"""
        print("\n🔍 Scanning for hardcoded secrets...")

        patterns = [
            (r'password\s*=\s*["\']([^"\']+)["\']', 'Hardcoded password'),
            (r'api[_-]?key\s*=\s*["\']([^"\']+)["\']', 'Hardcoded API key'),
            (r'secret[_-]?key\s*=\s*["\']([^"\']+)["\']', 'Hardcoded secret'),
            (r'aws[_-]?access[_-]?key\s*=\s*["\']([^"\']+)["\']', 'AWS key'),
            (r'(sk-[a-zA-Z0-9]{32,})', 'OpenAI API key pattern'),
        ]

        exclude_patterns = [
            'test', 'example', 'CHANGE_ME', 'your_', 'TODO',
            '.env.template', '.env.example'
        ]

        for py_file in self.root_dir.rglob('*.py'):
            if 'venv' in str(py_file) or 'node_modules' in str(py_file):
                continue

            try:
                content = py_file.read_text()
                for pattern, description in patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        value = match.group(1) if match.groups() else match.group(0)
                        # Skip if it's clearly a placeholder
                        if any(excl in value for excl in exclude_patterns):
                            continue
                        if len(value) > 8:  # Actual secrets are usually longer
                            self.vulnerabilities.append({
                                'type': 'Hardcoded Secret',
                                'severity': 'CRITICAL',
                                'file': str(py_file),
                                'line': content[:match.start()].count('\n') + 1,
                                'description': description,
                                'evidence': value[:20] + '...'
                            })
            except Exception as e:
                pass

    def scan_sql_injection(self):
        """Scan for SQL injection vulnerabilities"""
        print("🔍 Scanning for SQL injection...")

        patterns = [
            r'execute\(["\'].*\%s.*["\'].*\%',
            r'\.raw\(["\'].*\+.*["\']',
            r'f"SELECT.*\{.*\}"',
            r"f'SELECT.*\{.*\}'",
        ]

        for py_file in self.root_dir.rglob('*.py'):
            if 'venv' in str(py_file) or 'node_modules' in str(py_file):
                continue

            try:
                content = py_file.read_text()
                for pattern in patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        self.vulnerabilities.append({
                            'type': 'SQL Injection',
                            'severity': 'CRITICAL',
                            'file': str(py_file),
                            'line': content[:match.start()].count('\n') + 1,
                            'description': 'Potential SQL injection via string formatting',
                            'evidence': match.group(0)[:50]
                        })
            except Exception:
                pass

    def scan_command_injection(self):
        """Scan for command injection vulnerabilities"""
        print("🔍 Scanning for command injection...")

        patterns = [
            r'os\.system\(',
            r'subprocess\.call\([^)]*shell=True',
            r'eval\(',
            r'exec\(',
        ]

        for py_file in self.root_dir.rglob('*.py'):
            if 'venv' in str(py_file) or 'node_modules' in str(py_file):
                continue

            try:
                content = py_file.read_text()
                for pattern in patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        # Check if it's user input
                        line_start = content.rfind('\n', 0, match.start())
                        line_end = content.find('\n', match.end())
                        line = content[line_start:line_end]

                        if any(dangerous in line for dangerous in ['request', 'input', 'args', 'params']):
                            self.vulnerabilities.append({
                                'type': 'Command Injection',
                                'severity': 'CRITICAL',
                                'file': str(py_file),
                                'line': content[:match.start()].count('\n') + 1,
                                'description': 'Potential command injection',
                                'evidence': match.group(0)[:50]
                            })
            except Exception:
                pass

    def scan_path_traversal(self):
        """Scan for path traversal vulnerabilities"""
        print("🔍 Scanning for path traversal...")

        patterns = [
            r'open\(.*request\.',
            r'Path\(.*request\.',
            r'os\.path\.join\(.*request\.',
        ]

        for py_file in self.root_dir.rglob('*.py'):
            if 'venv' in str(py_file) or 'node_modules' in str(py_file):
                continue

            try:
                content = py_file.read_text()
                for pattern in patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        self.vulnerabilities.append({
                            'type': 'Path Traversal',
                            'severity': 'HIGH',
                            'file': str(py_file),
                            'line': content[:match.start()].count('\n') + 1,
                            'description': 'Potential path traversal vulnerability',
                            'evidence': match.group(0)[:50]
                        })
            except Exception:
                pass

    def scan_insecure_random(self):
        """Scan for insecure random number generation"""
        print("🔍 Scanning for insecure random...")

        for py_file in self.root_dir.rglob('*.py'):
            if 'venv' in str(py_file) or 'node_modules' in str(py_file):
                continue

            try:
                content = py_file.read_text()
                # Check for random module usage in security context
                if 'import random' in content and any(sec in content.lower() for sec in ['token', 'password', 'secret', 'key']):
                    self.vulnerabilities.append({
                        'type': 'Insecure Random',
                        'severity': 'HIGH',
                        'file': str(py_file),
                        'line': content.find('import random'),
                        'description': 'Using random instead of secrets module',
                        'evidence': 'import random (should use secrets module)'
                    })
            except Exception:
                pass

    def scan_weak_crypto(self):
        """Scan for weak cryptography"""
        print("🔍 Scanning for weak cryptography...")

        weak_patterns = [
            (r'hashlib\.md5', 'MD5 is cryptographically broken'),
            (r'hashlib\.sha1', 'SHA1 is weak, use SHA256+'),
            (r'DES', 'DES is insecure'),
        ]

        for py_file in self.root_dir.rglob('*.py'):
            if 'venv' in str(py_file) or 'node_modules' in str(py_file):
                continue

            try:
                content = py_file.read_text()
                for pattern, description in weak_patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        self.vulnerabilities.append({
                            'type': 'Weak Cryptography',
                            'severity': 'HIGH',
                            'file': str(py_file),
                            'line': content[:match.start()].count('\n') + 1,
                            'description': description,
                            'evidence': match.group(0)
                        })
            except Exception:
                pass

    def scan_xss_vulnerabilities(self):
        """Scan for XSS vulnerabilities in frontend"""
        print("🔍 Scanning for XSS vulnerabilities...")

        patterns = [
            r'dangerouslySetInnerHTML',
            r'innerHTML\s*=',
            r'eval\(',
        ]

        for tsx_file in self.root_dir.rglob('*.tsx'):
            try:
                content = tsx_file.read_text()
                for pattern in patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        self.vulnerabilities.append({
                            'type': 'XSS Vulnerability',
                            'severity': 'HIGH',
                            'file': str(tsx_file),
                            'line': content[:match.start()].count('\n') + 1,
                            'description': 'Potential XSS vulnerability',
                            'evidence': match.group(0)[:50]
                        })
            except Exception:
                pass

    def scan_insecure_deserialization(self):
        """Scan for insecure deserialization"""
        print("🔍 Scanning for insecure deserialization...")

        patterns = [
            r'pickle\.loads?\(',
            r'yaml\.load\([^)]*Loader=.*\)',
        ]

        for py_file in self.root_dir.rglob('*.py'):
            if 'venv' in str(py_file) or 'node_modules' in str(py_file):
                continue

            try:
                content = py_file.read_text()
                for pattern in patterns:
                    matches = re.finditer(pattern, content)
                    for match in matches:
                        if 'SafeLoader' not in match.group(0):
                            self.vulnerabilities.append({
                                'type': 'Insecure Deserialization',
                                'severity': 'CRITICAL',
                                'file': str(py_file),
                                'line': content[:match.start()].count('\n') + 1,
                                'description': 'Insecure deserialization',
                                'evidence': match.group(0)[:50]
                            })
            except Exception:
                pass

    def generate_report(self):
        """Generate security report"""
        print("\n" + "=" * 60)
        print("SECURITY SCAN RESULTS")
        print("=" * 60)

        if not self.vulnerabilities:
            print("\n✅ No vulnerabilities found!")
            return []

        # Group by severity
        critical = [v for v in self.vulnerabilities if v['severity'] == 'CRITICAL']
        high = [v for v in self.vulnerabilities if v['severity'] == 'HIGH']
        medium = [v for v in self.vulnerabilities if v['severity'] == 'MEDIUM']

        print(f"\n🔴 CRITICAL: {len(critical)}")
        print(f"🟠 HIGH: {len(high)}")
        print(f"🟡 MEDIUM: {len(medium)}")
        print(f"\nTotal: {len(self.vulnerabilities)} vulnerabilities")

        print("\n" + "=" * 60)
        print("VULNERABILITY DETAILS")
        print("=" * 60)

        for vuln in self.vulnerabilities:
            severity_emoji = "🔴" if vuln['severity'] == "CRITICAL" else "🟠" if vuln['severity'] == "HIGH" else "🟡"
            print(f"\n{severity_emoji} {vuln['type']} - {vuln['severity']}")
            print(f"   File: {vuln['file']}")
            print(f"   Line: {vuln['line']}")
            print(f"   Description: {vuln['description']}")
            if 'evidence' in vuln:
                print(f"   Evidence: {vuln['evidence']}")

        return self.vulnerabilities

if __name__ == "__main__":
    scanner = SecurityScanner("/workspaces/Elson-TB2")
    vulnerabilities = scanner.scan_all()

    # Save to file
    with open("/workspaces/Elson-TB2/security_scan_results.json", "w") as f:
        json.dump(vulnerabilities, f, indent=2)

    print(f"\n📄 Full results saved to: security_scan_results.json")
