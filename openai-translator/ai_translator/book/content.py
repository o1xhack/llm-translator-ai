import pandas as pd
from enum import Enum, auto
from PIL import Image as PILImage
from utils import LOG

class ContentType(Enum):
    TEXT = auto()
    TABLE = auto()
    IMAGE = auto()

class Content:
    def __init__(self, content_type, original, translation=None):
        self.content_type = content_type
        self.original = original
        self.translation = translation
        self.status = False

    def set_translation(self, translation, status):
        if not self.check_translation_type(translation):
            raise ValueError(f"Invalid translation type. Expected {self.content_type}, but got {type(translation)}")
        self.translation = translation
        self.status = status

    def check_translation_type(self, translation):
        if self.content_type == ContentType.TEXT and isinstance(translation, str):
            return True
        elif self.content_type == ContentType.TABLE and isinstance(translation, list):
            return True
        elif self.content_type == ContentType.IMAGE and isinstance(translation, PILImage.Image):
            return True
        return False


class TableContent(Content):
    def __init__(self, data, translation=None):
        df = pd.DataFrame(data)

        # Verify if the number of rows and columns in the data and DataFrame object match
        if len(data) != len(df) or len(data[0]) != len(df.columns):
            raise ValueError("The number of rows and columns in the extracted table data and DataFrame object do not match.")
        
        super().__init__(ContentType.TABLE, df)

    def set_translation(self, translation, status):
        try:
            if not isinstance(translation, str):
                raise ValueError(f"Invalid translation type. Expected str, but got {type(translation)}")

            LOG.debug(translation)
            # Convert the string to a list of lists
            table_data = self.preprocess_table_data(translation)
            # table_data = [row.strip().split() for row in translation.strip().split('\n')]
            # LOG.debug(table_data)
            # noted that turbo now return the table with |----|----| so we need to skip that line
            # table_data = [line for line in table_data if not any(cell.startswith("|--") for cell in line)]
            # LOG.debug(table_data)
            # Create a DataFrame from the table_data
            translated_df = pd.DataFrame(table_data[1:], columns=table_data[0])
            LOG.debug(translated_df)
            self.translation = translated_df
            self.status = status
        except Exception as e:
            LOG.error(f"An error occurred during table translation: {e}")
            self.translation = None
            self.status = False

    def __str__(self):
        return self.original.to_string(header=False, index=False)

    def iter_items(self, translated=False):
        target_df = self.translation if translated else self.original
        for row_idx, row in target_df.iterrows():
            for col_idx, item in enumerate(row):
                yield (row_idx, col_idx, item)

    def update_item(self, row_idx, col_idx, new_value, translated=False):
        target_df = self.translation if translated else self.original
        target_df.at[row_idx, col_idx] = new_value

    def get_original_as_str(self):
        return self.original.to_string(header=False, index=False)
    
    def preprocess_table_data(self, translation):
        rows = translation.strip().split('\n')
        processed_rows = []

        for row in rows:
            stripped_row = row.strip()
            # 如果这一行是分隔符线，则不进行分割 If this line is a separator line, do not split
            if '|' in stripped_row and '-' in stripped_row.replace('|', '').strip():
                continue  # 跳过这一行 Skip this line
            else:
                # 分割并保留分割符 '|' Split and keep the separator '|'
                split_row = stripped_row.split('|')
                # 重新组合保留 '|' Reassemble and keep '|'
                cleaned_row = []
                for i, cell in enumerate(split_row):
                    cleaned_row.append(cell.strip())
                    if i < len(split_row) - 1:
                        cleaned_row.append('|') 
                # 过滤掉空单元格，只保留内容和 '|' Filter out empty cells, keep only content and '|'
                cleaned_row = [cell for cell in cleaned_row if cell]
                processed_rows.append(cleaned_row)
        LOG.debug(processed_rows)
        return processed_rows