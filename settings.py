from pydantic import BaseModel
from enum import Enum
from datetime import date, time
from cat.mad_hatter.decorators import plugin

# settings
class SQLGPTSettings(BaseModel):
    db_uri: str
    test_db: bool = False

# Give your settings schema to the Cat.
@plugin
def settings_schema():   
    return SQLGPTSettings.model_json_schema()