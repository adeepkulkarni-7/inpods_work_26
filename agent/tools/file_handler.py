"""
File Handler Tool

Handles file uploads, validation, and information extraction.
"""

import os
import pandas as pd
from .base import BaseTool, ToolResult


class FileHandlerTool(BaseTool):
    """Handle file operations"""

    name = "get_file_info"
    description = """Get information about an uploaded file.
    Returns row count, column names, and validation status."""

    parameters = {
        "type": "object",
        "properties": {
            "file_path": {
                "type": "string",
                "description": "Path to the file"
            },
            "file_type": {
                "type": "string",
                "description": "Expected type: question, reference, or mapped",
                "enum": ["question", "reference", "mapped"]
            }
        },
        "required": ["file_path"]
    }

    def __init__(self, config: dict):
        super().__init__(config)
        self.upload_folder = config.get('upload_folder', 'uploads')
        os.makedirs(self.upload_folder, exist_ok=True)

    async def execute(self, params: dict) -> ToolResult:
        """Get file information"""
        try:
            file_path = params['file_path']
            file_type = params.get('file_type', 'question')

            if not os.path.exists(file_path):
                return ToolResult(
                    success=False,
                    error=f"File not found: {file_path}"
                )

            # Read file
            try:
                if file_path.endswith('.csv'):
                    df = pd.read_csv(file_path)
                elif file_path.endswith('.ods'):
                    df = pd.read_excel(file_path, engine='odf')
                else:
                    df = pd.read_excel(file_path, engine='openpyxl')
            except Exception as e:
                return ToolResult(
                    success=False,
                    error=f"Failed to read file: {str(e)}"
                )

            # Validate based on type
            validation_errors = []
            required_columns = {
                'question': ['Question Number', 'Question Text'],
                'reference': [],  # Flexible
                'mapped': ['Question Number', 'Question Text']
            }

            for col in required_columns.get(file_type, []):
                if col not in df.columns:
                    validation_errors.append(f"Missing column: {col}")

            # Get sample data
            sample = df.head(3).to_dict('records')

            # Detect dimension from reference file
            detected_dimension = None
            if file_type == 'reference':
                if 'ID' in df.columns:
                    first_id = df['ID'].dropna().iloc[0] if len(df) > 0 else ''
                    if str(first_id).startswith('MI'):
                        detected_dimension = 'nmc_competency'
                    elif str(first_id).startswith('C'):
                        detected_dimension = 'competency'
                    elif str(first_id).startswith('O'):
                        detected_dimension = 'objective'
                    elif str(first_id).startswith('S'):
                        detected_dimension = 'skill'
                elif 'Topic Area (CBME)' in df.columns or 'Topic Area' in df.columns:
                    detected_dimension = 'area_topics'

            file_info = {
                'file_path': file_path,
                'filename': os.path.basename(file_path),
                'file_type': file_type,
                'row_count': len(df),
                'columns': df.columns.tolist(),
                'sample': sample,
                'valid': len(validation_errors) == 0,
                'validation_errors': validation_errors,
                'detected_dimension': detected_dimension
            }

            return ToolResult(
                success=True,
                data=file_info,
                message=f"File '{os.path.basename(file_path)}' has {len(df)} rows and {len(df.columns)} columns",
                metadata=file_info
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e)
            )


class SaveUploadTool(BaseTool):
    """Save an uploaded file"""

    name = "save_upload"
    description = "Save an uploaded file to the uploads folder."

    parameters = {
        "type": "object",
        "properties": {
            "filename": {
                "type": "string",
                "description": "Original filename"
            },
            "content": {
                "type": "string",
                "description": "File content (base64 encoded for binary)"
            }
        },
        "required": ["filename", "content"]
    }

    def __init__(self, config: dict):
        super().__init__(config)
        self.upload_folder = config.get('upload_folder', 'uploads')
        os.makedirs(self.upload_folder, exist_ok=True)

    async def execute(self, params: dict) -> ToolResult:
        try:
            from werkzeug.utils import secure_filename

            filename = secure_filename(params['filename'])
            file_path = os.path.join(self.upload_folder, filename)

            # For binary files, decode base64
            content = params['content']
            if isinstance(content, str) and content.startswith('base64:'):
                import base64
                content = base64.b64decode(content[7:])
                with open(file_path, 'wb') as f:
                    f.write(content)
            else:
                with open(file_path, 'w') as f:
                    f.write(content)

            return ToolResult(
                success=True,
                data={'file_path': file_path, 'filename': filename},
                message=f"Saved file: {filename}"
            )

        except Exception as e:
            return ToolResult(
                success=False,
                error=str(e)
            )
