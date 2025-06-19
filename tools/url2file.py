from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

import requests

class Url2FileTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        url = tool_parameters['url']
        authorization = tool_parameters['authorization']
        headers = {'Authorization': authorization}
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
        except Exception as e:
            raise Exception(f"Error fetching file from URL: {str(e)}")

        file_bytes = response.content
        mime_type = response.headers.get('Content-Type', 'application/octet-stream')
        filename = tool_parameters.get('filename', 'Downloaded_File')
        if not filename.endswith('.xlsx') and 'excel' in mime_type:
            filename += '.xlsx'

        yield self.create_text_message(f"File '{filename}' downloaded successfully from URL.")
        yield self.create_blob_message(
            blob=file_bytes,
            meta={
                "mime_type": mime_type,
                "filename": filename
            }
        )
