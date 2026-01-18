# Example: How to use the system

## Quick Start

# 1. Analyze current directory
python app.py .

# 2. Analyze a GitHub repository
python app.py https://github.com/psf/requests

# 3. Analyze with custom output
python app.py . --output custom_report.json

# 4. With AI-powered fixes (requires OpenAI API key)
export OPENAI_API_KEY=sk-your-key-here
python app.py . --openai-key $OPENAI_API_KEY

## Testing Individual Modules

# Test repo fetcher
python core/repo_fetcher.py

# Test dependency parser
python core/dep_parser.py

# Test streaming engine
python core/pathway_stream.py

# Test code scanner
python core/code_scanner.py

# Test impact mapper
python core/impact_mapper.py

# Test AI fixer
python core/ai_fixer.py
