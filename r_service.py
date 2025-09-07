import os
import uuid
import subprocess

# Directories
CHARTS_DIR = "static/charts"
R_SCRIPTS_DIR = "uploads"  # temporary R scripts

# Ensure directories exist
os.makedirs(CHARTS_DIR, exist_ok=True)
os.makedirs(R_SCRIPTS_DIR, exist_ok=True)


def generate_chart_from_script(r_script: str) -> str | None:
    """
    Executes AI-generated R code safely to generate a chart as PNG.

    Args:
        r_script: AI-generated R code as string.

    Returns:
        Relative path to saved chart (e.g., 'charts/uuid.png'), or None on failure.
    """

    # Generate unique filenames
    unique_id = uuid.uuid4()
    script_filename = f"{unique_id}.R"
    chart_filename = f"{unique_id}.png"

    script_filepath = os.path.join(R_SCRIPTS_DIR, script_filename)
    chart_filepath = os.path.join(CHARTS_DIR, chart_filename)

    # -----------------------------
    # Helper: clean AI code
    # -----------------------------
    def clean_r_code(code: str) -> list[str]:
        """
        Comments out English-like lines and removes stray braces.
        Returns list of cleaned lines.
        """
        lines = code.splitlines()
        cleaned = []
        for line in lines:
            l = line.strip()
            if not l:
                cleaned.append("")
                continue

            # If line does NOT start with R keywords, comment it and remove braces
            if not l.startswith(("#", "library", "gg", "geom", "aes", "plot", "data", "for", "if", "function")):
                cleaned_line = line.replace("{", "").replace("}", "")
                cleaned.append("# " + cleaned_line)
            else:
                cleaned.append(line)
        return cleaned

    # -----------------------------
    # Helper: escape quotes in all lines
    # -----------------------------
    def escape_r_quotes(line: str) -> str:
        return line.replace('"', r'\"')

    # Clean and escape lines
    cleaned_lines = clean_r_code(r_script)
    escaped_lines = [escape_r_quotes(l) for l in cleaned_lines]

    # Wrap in try() to prevent crashes
    safe_r_code = "try({\n" + "\n".join(escaped_lines) + "\n})"

    # Append ggsave() outside wrapper
    full_r_script = safe_r_code + f'\nggsave("{chart_filepath}", plot = last_plot(), width = 8, height = 6, dpi = 150)'

    # -----------------------------
    # Execute R script
    # -----------------------------
    try:
        with open(script_filepath, "w", encoding="utf-8") as f:
            f.write(full_r_script)

        print(f"Executing R script: {script_filepath}")
        result = subprocess.run(
            ["Rscript", script_filepath],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"R script executed successfully. STDOUT:\n{result.stdout}")
        return os.path.join("charts", chart_filename)

    except FileNotFoundError:
        print("ERROR: 'Rscript' not found. Install R and ensure it's in PATH.")
        return None
    except subprocess.CalledProcessError as e:
        print(f"ERROR: R script failed (return code {e.returncode}). STDERR:\n{e.stderr}")
        return None
    except Exception as e:
        print(f"Unexpected error in R service: {e}")
        return None
    finally:
        if os.path.exists(script_filepath):
            os.remove(script_filepath)
            print(f"Cleaned up temporary R script: {script_filepath}")
