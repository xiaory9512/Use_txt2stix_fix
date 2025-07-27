#!/usr/bin/env python3
"""
Batch process txt files with support for standard and AI modes
File naming reflects the processing mode used
"""
import os
import subprocess
import json
import glob
import time
from pathlib import Path
import argparse


def find_new_bundle_file(existing_files, output_dir="output"):
    """Find newly generated bundle file in the output directory"""
    current_files = set(glob.glob(os.path.join(output_dir, "bundle--*.json")))
    new_files = current_files - existing_files
    return list(new_files)[0] if new_files else None


def create_temp_utf8_file(original_file):
    """Create a temporary UTF-8 version of the file"""
    temp_file = original_file.parent / f"temp_{original_file.name}"

    encodings_to_try = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252', 'windows-1252']
    content = None

    for encoding in encodings_to_try:
        try:
            with open(original_file, 'r', encoding=encoding) as f:
                content = f.read()
            break
        except UnicodeDecodeError:
            continue

    if content is None:
        with open(original_file, 'r', encoding='latin-1', errors='replace') as f:
            content = f.read()

    # Clean problematic characters
    content = content.replace('\x9d', '').replace('\ufeff', '')

    # Write as UTF-8
    with open(temp_file, 'w', encoding='utf-8') as f:
        f.write(content)

    return temp_file


def process_single_file(txt_file_path, output_dir, mode_suffix, extractions,
                        relationship_mode, ai_model=None, additional_args=None):
    """
    Process a single txt file

    Args:
        txt_file_path: Path to txt file
        output_dir: Output directory
        mode_suffix: Suffix for output file (e.g., _txt2stix+standard)
        extractions: Extraction types to use (can be None)
        relationship_mode: Relationship mode (standard or ai)
        ai_model: AI model to use (if using AI mode)
        additional_args: Additional command line arguments
    """
    # Get filename without extension
    file_name = Path(txt_file_path).stem

    # Create temporary UTF-8 file to avoid encoding issues
    temp_file = None
    try:
        temp_file = create_temp_utf8_file(Path(txt_file_path))
        txt_file_to_use = str(temp_file)
    except Exception as e:
        print(f"  Warning: Could not create temp file: {e}")
        txt_file_to_use = str(txt_file_path)

    # Build command
    # Use full Python path to ensure we're using the virtual environment
    import sys
    python_cmd = sys.executable
    cmd = [
        python_cmd, "txt2stix.py",
        "--input_file", txt_file_to_use,
        "--name", file_name[:72],
        "--relationship_mode", relationship_mode
    ]

    # Only add extractions if specified
    if extractions:
        cmd.extend(["--use_extractions", extractions])

    # Add AI parameters if using AI mode
    if ai_model and relationship_mode == "ai":
        cmd.extend(["--ai_settings_extractions", ai_model])
        cmd.extend(["--ai_settings_relationships", ai_model])

    # Add additional arguments
    if additional_args:
        for arg, value in additional_args.items():
            if value is not None:
                cmd.extend([f"--{arg}", str(value)])

    try:
        # Record existing bundle files in the output directory
        txt2stix_output_dir = "output"
        existing_bundles = set(glob.glob(os.path.join(txt2stix_output_dir, "bundle--*.json")))

        # Execute command
        print(f"Processing: {txt_file_path} (mode: {mode_suffix})")
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)

        # Wait for file generation
        time.sleep(0.5)

        # Find newly generated bundle file in output directory
        bundle_file = find_new_bundle_file(existing_bundles, txt2stix_output_dir)

        if bundle_file:
            # Build new filename
            new_filename = f"{file_name}{mode_suffix}.json"
            output_path = os.path.join(output_dir, new_filename)

            # Move file from txt2stix output to our output directory
            os.rename(bundle_file, output_path)
            print(f"✓ Success: {output_path}")

            # Print statistics
            try:
                with open(output_path, 'r', encoding='utf-8') as f:
                    bundle_data = json.load(f)
                    object_count = len(bundle_data.get('objects', []))
                    print(f"  Contains {object_count} STIX objects")
            except:
                pass

            return True, output_path
        else:
            print(f"✗ No bundle file found")
            if result.stderr:
                print(f"  Error: {result.stderr}")
            return False, None

    except subprocess.CalledProcessError as e:
        print(f"✗ Failed: {txt_file_path}")
        print(f"  Error: {e.stderr}")
        return False, None
    except UnicodeDecodeError as e:
        print(f"✗ Failed: {txt_file_path}")
        print(f"  Unicode encoding error: {str(e)}")
        print(f"  Try converting the file to UTF-8 encoding")
        return False, None
    finally:
        # Clean up temp file if it exists
        if temp_file and temp_file.exists():
            try:
                temp_file.unlink()
            except:
                pass


def batch_process_multimode(input_dir, output_dir, processing_modes, extractions, additional_args=None):
    """
    Batch process files with multiple processing modes

    Args:
        input_dir: Input directory containing txt files
        output_dir: Output directory for STIX bundles
        processing_modes: List of processing modes, each containing (mode_suffix, relationship_mode, ai_model)
        extractions: Extraction types to use
        additional_args: Additional arguments
    """
    # Create output directory
    os.makedirs(output_dir, exist_ok=True)

    # Get all txt files
    txt_files = list(Path(input_dir).glob("*.txt"))

    if not txt_files:
        print(f"No txt files found in {input_dir}")
        return

    print(f"Found {len(txt_files)} txt files")
    print(f"Will generate {len(processing_modes)} versions for each file")
    print("=" * 70)

    # Statistics
    total_tasks = len(txt_files) * len(processing_modes)
    completed = 0
    success_count = 0
    failed_tasks = []
    start_time = time.time()

    # Process each file with each mode
    for txt_file in txt_files:
        print(f"\nProcessing file: {txt_file.name}")
        print("-" * 50)

        for mode_suffix, relationship_mode, ai_model in processing_modes:
            completed += 1
            print(f"\n[{completed}/{total_tasks}] ", end="")

            success, output_path = process_single_file(
                txt_file,
                output_dir,
                mode_suffix,
                extractions,
                relationship_mode,
                ai_model,
                additional_args
            )

            if success:
                success_count += 1
            else:
                failed_tasks.append((str(txt_file), mode_suffix))

    # Cleanup leftover files
    cleanup_bundle_files()

    # Print statistics
    elapsed_time = time.time() - start_time
    print(f"\n{'=' * 70}")
    print(f"Batch processing complete!")
    print(f"Success: {success_count}/{total_tasks}")
    print(f"Total time: {elapsed_time:.2f} seconds")
    print(f"Average: {elapsed_time / total_tasks:.2f} seconds/task")

    if failed_tasks:
        print(f"\nFailed tasks ({len(failed_tasks)}):")
        for file_path, mode in failed_tasks:
            print(f"  - {file_path} ({mode})")


def cleanup_bundle_files():
    """Clean up leftover bundle files"""
    leftover_bundles = glob.glob("bundle--*.json")
    if leftover_bundles:
        print(f"\nCleaning up {len(leftover_bundles)} leftover files...")
        for bundle in leftover_bundles:
            try:
                os.remove(bundle)
            except:
                pass


def main():
    # Predefined processing modes
    PRESET_MODES = {
        "standard": ("_txt2stix+standard", "standard", None),
        "gpt4o": ("_txt2stix+gpt4o", "ai", "openai:gpt-4o"),
        "gpt4o-mini": ("_txt2stix+gpt4o-mini", "ai", "openai:gpt-4o-mini"),
        "claude": ("_txt2stix+claude", "ai", "anthropic:claude-3-5-sonnet-latest"),
        "gemini": ("_txt2stix+gemini", "ai", "gemini:models/gemini-1.5-pro-latest"),
        "deepseek": ("_txt2stix+deepseek", "ai", "deepseek:deepseek-chat")
    }

    parser = argparse.ArgumentParser(
        description="Batch process txt files with multiple modes and mode-specific naming",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Preset modes:
  standard   - Standard mode (no AI required)
  gpt4o      - Use OpenAI GPT-4o
  gpt4o-mini - Use OpenAI GPT-4o-mini
  claude     - Use Anthropic Claude
  gemini     - Use Google Gemini
  deepseek   - Use DeepSeek

Examples:
  # Use both standard and gpt4o modes
  python batch_process_custom.py --input_dir input_texts --output_dir output_stix --modes standard,gpt4o

  # Use only standard mode
  python batch_process_custom.py --input_dir input_texts --output_dir output_stix --modes standard
        """
    )

    # Required arguments
    parser.add_argument("--input_dir", required=True, help="Input directory containing txt files")
    parser.add_argument("--output_dir", required=True, help="Output directory for STIX bundles")
    parser.add_argument("--modes", required=True, help="Processing modes, comma separated (e.g., standard,gpt4o)")

    # Extraction options
    parser.add_argument(
        "--extractions",
        default=None,
        help="Extraction types, comma separated. If not specified, txt2stix defaults will be used"
    )

    # Optional arguments
    parser.add_argument("--tlp_level", choices=["clear", "green", "amber", "amber_strict", "red"],
                        default="clear", help="TLP level")
    parser.add_argument("--confidence", type=int, help="Confidence score (0-100)")
    parser.add_argument("--labels", help="Labels, comma separated")

    args = parser.parse_args()

    # Parse processing modes
    selected_modes = []
    for mode_name in args.modes.split(','):
        mode_name = mode_name.strip().lower()
        if mode_name in PRESET_MODES:
            selected_modes.append(PRESET_MODES[mode_name])
        else:
            print(f"Warning: Unknown mode '{mode_name}', skipping")

    if not selected_modes:
        print("Error: No valid processing modes selected")
        return

    # Build additional arguments
    additional_args = {}
    if args.tlp_level != "clear":
        additional_args["tlp_level"] = args.tlp_level
    if args.confidence:
        additional_args["confidence"] = args.confidence
    if args.labels:
        additional_args["labels"] = args.labels

    # Check for AI mode requirements
    ai_modes = [m for m in selected_modes if m[1] == "ai"]
    if ai_modes:
        print("Note: AI modes require API keys to be configured in .env file")
        print("Required API keys:")
        for _, _, ai_model in ai_modes:
            provider = ai_model.split(':')[0]
            if provider == "openai":
                print("  - OPENAI_API_KEY")
            elif provider == "anthropic":
                print("  - ANTHROPIC_API_KEY")
            elif provider == "gemini":
                print("  - GOOGLE_API_KEY")
            elif provider == "deepseek":
                print("  - DEEPSEEK_API_KEY")
        print()

    # Execute batch processing
    batch_process_multimode(
        args.input_dir,
        args.output_dir,
        selected_modes,
        args.extractions,
        additional_args
    )


if __name__ == "__main__":
    main()