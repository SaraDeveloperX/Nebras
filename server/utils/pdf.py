import os
import sys
import json
import subprocess
import tempfile
import uuid

async def generate_pdf(context_data: dict) -> str:
    """
    Generates a PDF report by calling the standalone pdf_generator.py script.
    Avoids asyncio event loop conflicts in Uvicorn on Windows.
    """
    
    # Write data to temp file
    # Using delete=False because windows can't open file twice if open
    # We will delete manually
    tf = tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False, suffix='.json')
    json.dump(context_data, tf)
    tf.close()
    
    generator_script = os.path.join(os.path.dirname(__file__), 'pdf_generator.py')
    
    try:
        # Call the script
        # Using sys.executable to ensure we use the same environment (venv)
        result = subprocess.run(
            [sys.executable, generator_script, tf.name],
            capture_output=True,
            text=True,
            check=True
        )
        filename = result.stdout.strip()
        return filename
    except subprocess.CalledProcessError as e:
        print(f"PDF Generation failed: {e.stderr}")
        raise e
    finally:
        if os.path.exists(tf.name):
            os.remove(tf.name)
