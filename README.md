# Real-Time Dependency Deprecation & Migration Intelligence System

A powerful Python tool that analyzes your repository's dependencies, detects breaking changes, and generates AI-powered migration fixes.

## 🎯 Features

- **Automatic Dependency Detection**: Scans all `requirements*.txt` files
- **Live PyPI Integration**: Fetches latest package versions in real-time
- **Breaking Change Detection**: Identifies major version bumps using semantic versioning
- **AST-Based Code Analysis**: Scans Python files to find exact usage locations
- **Impact Mapping**: Links breaking changes to affected code with file and line numbers
- **AI-Powered Fixes**: Generates migration suggestions using LLM (optional)
- **Structured Output**: Exports detailed JSON reports

## 📋 Requirements

- Python 3.8+
- Git (for cloning repositories)

## 🚀 Installation

1. Clone or download this repository
2. Install system dependencies:

```bash
pip install -r requirements-system.txt
```

**Note**: The `pathway` library is optional. The system will work with a simplified streaming simulation if not installed.

## 💻 Usage

### Basic Usage

Analyze a local repository:
```bash
python app.py /path/to/your/repo
```

Analyze a GitHub repository:
```bash
python app.py https://github.com/username/repository
```

### Advanced Options

Specify custom output file:
```bash
python app.py . --output my_report.json
```

Enable AI-powered fixes (requires OpenAI API key):
```bash
python app.py . --openai-key sk-your-api-key
```

Or set environment variable:
```bash
export OPENAI_API_KEY=sk-your-api-key
python app.py .
```

## 📊 Output Format

The system generates a structured JSON report with the following information:

```json
{
  "repository": "/path/to/repo",
  "total_dependencies": 10,
  "total_updates": 8,
  "breaking_changes": 3,
  "outdated_packages": 5,
  "results": [
    {
      "package": "flask",
      "current_version": "2.0.0",
      "latest_version": "3.1.2",
      "status": "breaking",
      "impacted_files": [
        {
          "file": "app.py",
          "impacts": [
            {
              "line": 10,
              "api": "Flask",
              "context": "app = Flask(__name__)"
            }
          ],
          "ai_fix": {
            "explanation": "Breaking change explanation...",
            "fixed_code": "Updated code...",
            "migration_notes": "Migration steps...",
            "confidence": 0.85
          }
        }
      ]
    }
  ]
}
```

## 🏗️ Architecture

```
core/
├── repo_fetcher.py      # Clone/validate repositories
├── dep_parser.py        # Parse requirements files
├── pathway_stream.py    # Stream PyPI updates
├── code_scanner.py      # AST-based code analysis
├── impact_mapper.py     # Map changes to code
└── ai_fixer.py          # Generate AI fixes

app.py                   # Main orchestration
```

## 🔍 How It Works

1. **Repository Fetching**: Clones GitHub repos or validates local paths
2. **Dependency Parsing**: Auto-detects and parses all `requirements*.txt` files
3. **PyPI Streaming**: Fetches latest versions from PyPI for all dependencies
4. **Version Comparison**: Detects outdated packages and breaking changes (major version bumps)
5. **Code Scanning**: Uses Python AST to find all package usage locations
6. **Impact Mapping**: Links breaking changes to specific code locations
7. **AI Fix Generation**: Optionally generates migration suggestions using LLM

## 📝 Example Output

```
======================================================================
REAL-TIME DEPENDENCY DEPRECATION & MIGRATION INTELLIGENCE SYSTEM
======================================================================

[STEP 1/7] Fetching repository...
[OK] Repository ready at: /path/to/repo

[STEP 2/7] Parsing dependencies...
[INFO] Found 1 requirements file(s):
  - requirements.txt
[OK] Parsed 6 unique dependencies

[STEP 3/7] Streaming PyPI updates...
[INFO] Loading repository dependencies...
  - requests: 2.28.1
  - flask: 2.0.0
[OK] Loaded 2 dependencies with versions

[STEP 4/7] Detecting outdated and breaking changes...
  [OUTDATED] requests: 2.28.1 -> 2.32.5
  [BREAKING] flask: 2.0.0 -> 3.1.2

[SUMMARY] Found 1 breaking changes, 1 outdated packages

[STEP 5/7] Scanning code for package usage...
[INFO] Found 5 Python files
[OK] Scanned 5 files, found 8 usages

[STEP 6/7] Mapping breaking changes to impacted code...
  [BREAKING] flask: 4 impacts in 1 files

[STEP 7/7] Generating AI-powered migration fixes...
[INFO] Generating AI fixes for flask...
[OK] Generated 4 fixes
```

## 🧪 Testing

Each module can be tested independently:

```bash
# Test repository fetcher
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
```

## 🔧 Configuration

### Environment Variables

- `OPENAI_API_KEY`: OpenAI API key for AI-powered fixes (optional)

### Excluded Directories

The code scanner automatically excludes:
- `__pycache__`
- `.git`
- `.venv`, `venv`, `env`
- `node_modules`
- `.tox`
- `build`, `dist`
- `.eggs`

## ⚠️ Limitations

- **Python Only**: Currently supports Python projects only
- **PyPI Only**: Only checks PyPI for package updates
- **Requirements Files**: Only parses `requirements*.txt` (not `poetry`, `pipenv`, etc.)
- **Breaking Change Detection**: Based on semantic versioning (major version bumps)
- **AI Fixes**: Require OpenAI API key; fallback logic provided without it

## 🎓 AI Fix Quality

The AI fixer follows these principles:
- **No Hallucination**: Uses official documentation when available
- **Conservative Approach**: Provides TODO comments when uncertain
- **Confidence Scoring**: Each fix includes a confidence score (0-1)
- **Migration Notes**: Includes additional context and migration steps

## 📦 Dependencies

Core dependencies:
- `requests` - PyPI API communication
- `packaging` - Version comparison
- `openai` - AI-powered fixes (optional)

## 🤝 Contributing

This is an MVP implementation. Future enhancements could include:
- Support for `poetry.lock`, `Pipfile.lock`
- Multi-language support (JavaScript, Java, etc.)
- Real-time monitoring mode
- Integration with CI/CD pipelines
- Custom migration rule engine
- Automated PR generation

## 📄 License

This project is provided as-is for educational and development purposes.

## 🙏 Acknowledgments

Built with:
- Python AST for code analysis
- PyPI JSON API for package information
- OpenAI GPT for AI-powered fixes
- Pathway for streaming data processing (optional)
