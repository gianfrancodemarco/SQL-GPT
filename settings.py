from pydantic import BaseModel
from enum import Enum
from datetime import date, time
from cat.mad_hatter.decorators import plugin

# settings
class DBGPTsettings(BaseModel):
    db_uri: str

# Give your settings schema to the Cat.
@plugin
def settings_schema():   
    return DBGPTsettings.model_json_schema()