# Use_txt2stix_fix
# TXT2STIX Batch Processing Toolkit

A comprehensive toolkit for batch processing threat intelligence reports using [txt2stix](https://github.com/muchdogesec/txt2stix) to generate STIX 2.1 bundles.

## Overview

This repository contains utilities and scripts to:
- Preprocess text files to ensure encoding compatibility
- Batch process multiple text files through txt2stix
- Support both standard (regex-based) and AI-powered extraction modes
- Generate STIX 2.1 bundles with custom naming conventions

## Prerequisites

- Python 3.8+
- Windows/Linux/macOS
- OpenAI API key (for AI mode only)

## Installation

### 1. Clone txt2stix

```bash
git clone https://github.com/muchdogesec/txt2stix
cd txt2stix
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv txt2stix-venv

# Activate virtual environment
# Windows:
txt2stix-venv\Scripts\activate
# Linux/macOS:
source txt2stix-venv/bin/activate
```

### 3. Install Dependencies

```bash
# Install txt2stix requirements
pip install -r requirements.txt

# Install additional dependencies
pip install git+https://github.com/muchdogesec/stix2extensions.git
pip install chardet  # For encoding detection
```

### 4. Configure Environment

Create `.env` file from template:
```bash
cp .env.example .env
```

Edit `.env` and add your API keys (if using AI mode):
```
OPENAI_API_KEY=your-openai-api-key
# Add other API keys as needed
```

### 5. Add Custom Scripts

Copy the following files from this repository to your txt2stix directory:
- `batch_process_custom.py` - Main batch processing script
- `preprocess_for_txt2stix.py` - Text preprocessing utility
- `fix_txt_encoding.py` - Encoding fix utility (optional)

## Repository Structure

```
txt2stix/
├── txt2stix-venv/              # Virtual environment (don't commit)
├── input_texts/                # Raw input text files
├── clean_input_texts/          # Preprocessed text files
├── output_stix/                # Generated STIX bundles
├── logs/                       # txt2stix logs
├── .env                        # API keys (don't commit)
├── batch_process_custom.py     # Batch processing script
├── preprocess_for_txt2stix.py  # Preprocessing script
└── README.md                   # This file
```

## Usage

### Step 1: Prepare Input Files

Place your threat intelligence reports (`.txt` files) in the `input_texts/` directory:
```bash
mkdir input_texts
# Copy your .txt files to input_texts/
```

### Step 2: Preprocess Files

Clean and standardize encoding for all text files:
```bash
python preprocess_for_txt2stix.py
```

This will:
- Fix encoding issues (UTF-8, cp1252, etc.)
- Replace problematic characters (smart quotes, special dashes)
- Save cleaned files to `clean_input_texts/`

### Step 3: Run Batch Processing

#### Standard Mode (Regex-based)
```bash
python batch_process_custom.py --input_dir clean_input_texts --output_dir output_stix --modes standard --extractions "pattern_*"
```

#### AI Mode (GPT-4)
```bash
python batch_process_custom.py --input_dir clean_input_texts --output_dir output_stix --modes gpt4o --extractions "pattern_*,ai_*"
```

#### Multiple Modes
```bash
python batch_process_custom.py \
    --input_dir clean_input_texts \
    --output_dir output_stix \
    --modes standard,gpt4o \
    --extractions "pattern_*,ai_*"
```

## Command Options

### batch_process_custom.py

```bash
python batch_process_custom.py --help
```

**Required Arguments:**
- `--input_dir`: Directory containing input text files
- `--output_dir`: Directory for output STIX bundles
- `--modes`: Processing modes (comma-separated)

**Optional Arguments:**
- `--extractions`: Extraction types (default: pattern_ipv4_address_only)
- `--tlp_level`: TLP level (clear, green, amber, amber_strict, red)
- `--confidence`: Confidence score (0-100)
- `--labels`: Comma-separated labels

**Available Modes:**
- `standard`: Regex-based extraction
- `gpt4o`: OpenAI GPT-4o
- `gpt4o-mini`: OpenAI GPT-4o-mini
- `claude`: Anthropic Claude
- `gemini`: Google Gemini
- `deepseek`: DeepSeek

### Extraction Types

**Pattern Extractions** (regex-based):
- `pattern_ipv4_address_only`
- `pattern_ipv6_address_only`
- `pattern_url`
- `pattern_email_address`
- `pattern_md5_hash`
- `pattern_sha1_hash`
- `pattern_sha256_hash`
- `pattern_cve_id`
- Use `pattern_*` to include all pattern extractions

**Lookup Extractions**:
- `lookup_mitre_attack_enterprise`
- `lookup_mitre_attack_mobile`
- `lookup_malware`
- `lookup_country_alpha2`
- Use `lookup_*` to include all lookup extractions

**AI Extractions** (requires AI mode):
- Various AI-powered extractions
- Use `ai_*` to include all AI extractions

## Examples

### Example 1: Basic Standard Processing
```bash
python batch_process_custom.py \
    --input_dir clean_input_texts \
    --output_dir output_stix \
    --modes standard \
    --extractions "pattern_ipv4_address_only,pattern_url,pattern_md5_hash"
```

### Example 2: Advanced AI Processing
```bash
python batch_process_custom.py \
    --input_dir clean_input_texts \
    --output_dir output_stix \
    --modes gpt4o \
    --extractions "pattern_*,lookup_mitre_attack_enterprise,ai_*" \
    --tlp_level amber \
    --confidence 85 \
    --labels "apt,malware,threat-intel"
```

### Example 3: Direct txt2stix Command (Single File)
```bash
python txt2stix.py \
    --input_file clean_input_texts/report.txt \
    --name "APT Report" \
    --relationship_mode ai \
    --ai_settings_extractions openai:gpt-4o \
    --ai_settings_relationships openai:gpt-4o \
    --use_extractions "pattern_*,ai_*" \
    --ai_create_attack_flow
```

## Output

Generated STIX bundles will be saved in `output_stix/` with naming convention:
- Standard mode: `filename_txt2stix+standard.json`
- AI mode: `filename_txt2stix+gpt4o.json`

Each bundle contains:
- STIX Report object
- Extracted indicators
- Relationships between objects
- TLP markings and confidence scores

## Troubleshooting

### Encoding Errors
If you encounter `UnicodeDecodeError`:
1. Run `python preprocess_for_txt2stix.py`
2. Use files from `clean_input_texts/` instead of `input_texts/`

### Module Not Found
If you get `ModuleNotFoundError: No module named 'stix2extensions'`:
```bash
pip install git+https://github.com/muchdogesec/stix2extensions.git
```

### API Key Issues
Ensure your `.env` file contains valid API keys:
```bash
# Check if environment variable is set
echo %OPENAI_API_KEY%  # Windows
echo $OPENAI_API_KEY   # Linux/macOS
```

## Best Practices

1. **Always preprocess files** before running txt2stix to avoid encoding issues
2. **Test with one file first** before batch processing
3. **Use standard mode** for quick extraction without API costs
4. **Use AI mode** for comprehensive analysis and relationship detection
5. **Monitor API usage** when processing large batches with AI mode
6. **Check logs** in `logs/` directory for detailed processing information

## License

This toolkit is provided as-is for use with txt2stix. Please refer to the [txt2stix license](https://github.com/muchdogesec/txt2stix/blob/main/LICENSE) for usage terms.

## Contributing

Feel free to submit issues or pull requests to improve this toolkit.

## Acknowledgments

- [DOGESEC](https://github.com/muchdogesec) for creating txt2stix
- [OASIS](https://www.oasis-open.org/) for the STIX 2.1 standard
