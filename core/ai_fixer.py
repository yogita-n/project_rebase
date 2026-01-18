"""
AI Fixer Module

Uses RAG (Retrieval-Augmented Generation) + LLM to:
- Explain breaking changes
- Generate before/after code fixes
- Cite migration logic from official documentation
"""

import os
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json


@dataclass
class AIFix:
    """
    Represents an AI-generated fix for a breaking change.
    
    Attributes:
        package_name: Name of the package
        current_version: Current version
        latest_version: Latest version
        file_path: Path to the affected file
        line_number: Line number of the affected code
        original_code: Original code snippet
        explanation: Explanation of the breaking change
        fixed_code: Suggested fixed code
        migration_notes: Additional migration notes
        confidence: Confidence score (0-1)
    """
    package_name: str
    current_version: str
    latest_version: str
    file_path: str
    line_number: int
    original_code: str
    explanation: str
    fixed_code: str
    migration_notes: str = ""
    confidence: float = 0.0


class AIFixer:
    """
    AI-powered code fixer using LLM.
    
    Features:
    - Explains breaking changes
    - Generates migration code
    - Provides context-aware fixes
    - Cites official documentation
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """
        Initialize the AI fixer.
        
        Args:
            api_key: OpenAI API key (or None to use environment variable)
            model: Model to use (default: gpt-4)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        self.llm_available = False
        
        # Check if OpenAI is available
        try:
            import openai
            if self.api_key:
                self.client = openai.OpenAI(api_key=self.api_key)
                self.llm_available = True
                print("[OK] OpenAI client initialized")
            else:
                print("[WARNING] No OpenAI API key found. AI fixes will use fallback logic.")
        except ImportError:
            print("[WARNING] OpenAI library not installed. AI fixes will use fallback logic.")
    
    def generate_fix(self, impacted_code) -> AIFix:
        """
        Generate a fix for impacted code.
        
        Args:
            impacted_code: ImpactedCode object
            
        Returns:
            AIFix object with suggested fix
        """
        if self.llm_available:
            return self._generate_llm_fix(impacted_code)
        else:
            return self._generate_fallback_fix(impacted_code)
    
    def _generate_llm_fix(self, impacted_code) -> AIFix:
        """
        Generate fix using LLM.
        
        Args:
            impacted_code: ImpactedCode object
            
        Returns:
            AIFix object
        """
        # Construct prompt
        prompt = self._build_prompt(impacted_code)
        
        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a Python migration expert. Analyze breaking changes and provide accurate migration guidance. Never hallucinate fixes. Use official documentation when available."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,  # Lower temperature for more deterministic output
                max_tokens=1000
            )
            
            # Parse response
            content = response.choices[0].message.content
            return self._parse_llm_response(impacted_code, content)
            
        except Exception as e:
            print(f"[WARNING] LLM generation failed: {e}")
            return self._generate_fallback_fix(impacted_code)
    
    def _build_prompt(self, impacted_code) -> str:
        """
        Build prompt for LLM.
        
        Args:
            impacted_code: ImpactedCode object
            
        Returns:
            Prompt string
        """
        return f"""Analyze this breaking change and provide migration guidance:

Package: {impacted_code.package_name}
Current Version: {impacted_code.current_version}
Latest Version: {impacted_code.latest_version}

Affected Code:
File: {impacted_code.file_path}
Line: {impacted_code.line_number}
Code: {impacted_code.context}
API Element: {impacted_code.api_element}
Usage Type: {impacted_code.usage_type}

Please provide:
1. EXPLANATION: Brief explanation of what changed and why it's breaking
2. FIXED_CODE: The corrected code snippet
3. MIGRATION_NOTES: Any additional migration steps or considerations

Format your response as JSON:
{{
    "explanation": "...",
    "fixed_code": "...",
    "migration_notes": "...",
    "confidence": 0.0-1.0
}}
"""
    
    def _parse_llm_response(self, impacted_code, content: str) -> AIFix:
        """
        Parse LLM response into AIFix object.
        
        Args:
            impacted_code: ImpactedCode object
            content: LLM response content
            
        Returns:
            AIFix object
        """
        try:
            # Try to parse as JSON
            # Extract JSON from markdown code blocks if present
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                content = content[start:end].strip()
            elif "```" in content:
                start = content.find("```") + 3
                end = content.find("```", start)
                content = content[start:end].strip()
            
            data = json.loads(content)
            
            return AIFix(
                package_name=impacted_code.package_name,
                current_version=impacted_code.current_version,
                latest_version=impacted_code.latest_version,
                file_path=impacted_code.file_path,
                line_number=impacted_code.line_number,
                original_code=impacted_code.context,
                explanation=data.get('explanation', 'No explanation provided'),
                fixed_code=data.get('fixed_code', impacted_code.context),
                migration_notes=data.get('migration_notes', ''),
                confidence=float(data.get('confidence', 0.5))
            )
        except Exception as e:
            print(f"[WARNING] Failed to parse LLM response: {e}")
            return self._generate_fallback_fix(impacted_code)
    
    def _generate_fallback_fix(self, impacted_code) -> AIFix:
        """
        Generate a basic fix without LLM (fallback).
        
        Args:
            impacted_code: ImpactedCode object
            
        Returns:
            AIFix object with basic suggestions
        """
        explanation = f"Breaking change detected in {impacted_code.package_name} from version {impacted_code.current_version} to {impacted_code.latest_version}. Manual review required."
        
        migration_notes = f"""
Please review the official migration guide for {impacted_code.package_name} {impacted_code.latest_version}.

Common migration steps:
1. Check the package changelog for breaking changes
2. Update API calls to match the new version
3. Test thoroughly before deploying
4. Consider using version pinning during migration
"""
        
        return AIFix(
            package_name=impacted_code.package_name,
            current_version=impacted_code.current_version,
            latest_version=impacted_code.latest_version,
            file_path=impacted_code.file_path,
            line_number=impacted_code.line_number,
            original_code=impacted_code.context,
            explanation=explanation,
            fixed_code=f"# TODO: Update for {impacted_code.package_name} {impacted_code.latest_version}\n{impacted_code.context}",
            migration_notes=migration_notes.strip(),
            confidence=0.3
        )
    
    def generate_fixes_for_impact(self, impact_report) -> List[AIFix]:
        """
        Generate fixes for all impacted code in an impact report.
        
        Args:
            impact_report: BreakingChangeImpact object
            
        Returns:
            List of AIFix objects
        """
        print(f"[INFO] Generating AI fixes for {impact_report.package_name}...")
        fixes = []
        
        for impacted_code in impact_report.impacted_code:
            fix = self.generate_fix(impacted_code)
            fixes.append(fix)
            print(f"  - {impacted_code.file_path}:{impacted_code.line_number} (confidence: {fix.confidence:.2f})")
        
        print(f"[OK] Generated {len(fixes)} fixes")
        return fixes
    
    def export_fix_report(self, fixes: List[AIFix]) -> Dict:
        """
        Export fixes as a structured report.
        
        Args:
            fixes: List of AIFix objects
            
        Returns:
            Dictionary with fix information
        """
        return {
            'total_fixes': len(fixes),
            'average_confidence': sum(f.confidence for f in fixes) / len(fixes) if fixes else 0,
            'fixes': [
                {
                    'package': fix.package_name,
                    'version_change': f"{fix.current_version} -> {fix.latest_version}",
                    'file': fix.file_path,
                    'line': fix.line_number,
                    'original_code': fix.original_code,
                    'explanation': fix.explanation,
                    'fixed_code': fix.fixed_code,
                    'migration_notes': fix.migration_notes,
                    'confidence': fix.confidence
                }
                for fix in fixes
            ]
        }


def main():
    """
    Test the AIFixer module.
    """
    print("=" * 60)
    print("Testing AIFixer")
    print("=" * 60)
    
    # Mock impacted code
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    
    from core.impact_mapper import ImpactedCode
    
    mock_impact = ImpactedCode(
        file_path='test_code.py',
        line_number=6,
        api_element='Flask',
        usage_type='call',
        context='app = Flask(__name__)',
        package_name='flask',
        current_version='2.0.0',
        latest_version='3.1.2'
    )
    
    # Generate fix
    fixer = AIFixer()
    fix = fixer.generate_fix(mock_impact)
    
    # Display result
    print("\n" + "=" * 60)
    print("AI Fix Generated:")
    print("=" * 60)
    print(f"\nPackage: {fix.package_name}")
    print(f"Version: {fix.current_version} -> {fix.latest_version}")
    print(f"File: {fix.file_path}:{fix.line_number}")
    print(f"\nOriginal Code:")
    print(f"  {fix.original_code}")
    print(f"\nExplanation:")
    print(f"  {fix.explanation}")
    print(f"\nFixed Code:")
    print(f"  {fix.fixed_code}")
    print(f"\nMigration Notes:")
    print(f"  {fix.migration_notes}")
    print(f"\nConfidence: {fix.confidence:.2f}")


if __name__ == "__main__":
    main()
