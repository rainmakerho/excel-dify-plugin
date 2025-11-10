from collections.abc import Generator
from typing import Any

from dify_plugin import Tool
from dify_plugin.entities.tool import ToolInvokeMessage

import pandas as pd
import json, re
from io import StringIO, BytesIO

class Json2ExcelTool(Tool):
    def _invoke(self, tool_parameters: dict[str, Any]) -> Generator[ToolInvokeMessage]:
        json_str = tool_parameters['json_str']
        try:
            df = self.json_to_df_auto(json_str)  # 修改为 self.json_to_df_auto
        except Exception as e:
            raise Exception(f"Error reading JSON string: {str(e)}")

        # convert df to excel bytes
        excel_buffer = BytesIO()
        try:
            df.to_excel(excel_buffer, index=False)
            excel_buffer.seek(0)
        except Exception as e:
            raise Exception(f"Error converting DataFrame to Excel: {str(e)}")

        # create a blob with the excel bytes
        try:
            excel_bytes = excel_buffer.getvalue()
            filename = tool_parameters.get('filename', 'Converted Data')
            filename = f"{filename.replace(' ', '_')}.xlsx"

            yield self.create_text_message(f"Excel file '{filename}' generated successfully")

            yield self.create_blob_message(
                    blob=excel_bytes,
                    meta={
                        "mime_type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        "filename": filename
                    }
                )
        except Exception as e:
            raise Exception(f"Error creating Excel file message: {str(e)}")
        
    def json_to_df_auto(self, json_str):
        parsed = json.loads(json_str)
        rows = parsed if isinstance(parsed, list) else [parsed]
        df = pd.json_normalize(rows)

        preserve_string_cols = set()
        # 偵測：只要該欄在任何一列有字串且是以 0 開頭的純數字字串，就保留前導零
        for col in df.columns:
            for r in rows:
                if not isinstance(r, dict):
                    continue
                v = r.get(col)
                if isinstance(v, str) and re.match(r"^0\d+$", v):
                    preserve_string_cols.add(col)
                    break

        # 轉換：保留需要的欄位為字串，其他欄位嘗試轉數值
        for col in df.columns:
            if col in preserve_string_cols:
                df[col] = df[col].where(df[col].notnull(), "").astype(str)
            else:
                # 只要能轉成數字就轉，不能就保留原值
                df[col] = pd.to_numeric(df[col], errors='ignore')

        return df