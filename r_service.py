import os
import uuid
import subprocess

# Define constants for directories to avoid magic strings.
CHARTS_DIR = "static/charts"
R_SCRIPTS_DIR = "uploads" # Temporary storage for R scripts

# Ensure the necessary directories exist on application startup.
os.makedirs(CHARTS_DIR, exist_ok=True)
os.makedirs(R_SCRIPTS_DIR, exist_ok=True)

def generate_chart_from_script(r_script: str) -> str | None:
    """
    Executes a given R script to generate and save a chart as a PNG image.

    This function takes a string of R code, saves it to a temporary file,
    and then calls the system's `Rscript` interpreter to run it. It is
    designed to be robust, with error handling for cases where R is not
    installed or the script itself fails.

    Args:
        r_script: A string containing the R code to execute. This script
                  is expected to generate a ggplot2 plot as its last expression.

    Returns:
        The relative path to the generated chart image (e.g., 'charts/some-uuid.png')
        if successful, otherwise None.
    """
    # Generate unique filenames to prevent conflicts during concurrent requests.
    unique_id = uuid.uuid4()
    script_filename = f"{unique_id}.R"
    chart_filename = f"{unique_id}.png"

    script_filepath = os.path.join(R_SCRIPTS_DIR, script_filename)
    chart_filepath = os.path.join(CHARTS_DIR, chart_filename)

    # Append a `ggsave` command to the AI-generated script. This standardizes
    # the output process, ensuring all charts are saved to the correct location
    # with a unique name and consistent dimensions.
    ggsave_command = f'\nggsave("{chart_filepath}", plot = last_plot(), width = 8, height = 6, dpi = 150)'
    full_r_script = r_script + ggsave_command

    try:
        # Write the complete R script to a temporary file.
        with open(script_filepath, "w") as f:
            f.write(full_r_script)

        print(f"Executing R script: {script_filepath}")
        # Execute the script using the `Rscript` command-line tool.
        # `check=True` will automatically raise a CalledProcessError for non-zero exit codes.
        result = subprocess.run(
            ["Rscript", script_filepath],
            capture_output=True,
            text=True,
            check=True
        )
        print(f"R script executed successfully. STDOUT: {result.stdout}")

        # Return the relative path for use in HTML templates.
        return os.path.join("charts", chart_filename)

    except FileNotFoundError:
        # This error occurs if the `Rscript` command is not found in the system's PATH.
        print("ERROR: 'Rscript' command not found. Please ensure R is installed and accessible.")
        return None
    except subprocess.CalledProcessError as e:
        # This error occurs if the R script itself fails (e.g., syntax error).
        print(f"ERROR: R script execution failed with return code {e.returncode}.")
        print(f"STDERR: {e.stderr}")
        return None
    except Exception as e:
        # Catch any other unexpected errors.
        print(f"An unexpected error occurred in the R service: {e}")
        return None
    finally:
        # Crucially, always attempt to clean up the temporary R script file.
        if os.path.exists(script_filepath):
            os.remove(script_filepath)
            print(f"Cleaned up temporary R script: {script_filepath}")
