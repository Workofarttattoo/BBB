import sys
import os
import asyncio
from datetime import datetime

# Setup paths and mocks
sys.path.insert(0, os.path.abspath('src'))
from unittest.mock import MagicMock

# Mock fastapi
sys.modules['fastapi'] = MagicMock()
sys.modules['fastapi.security'] = MagicMock()

# Mock pydantic
class BaseModel: pass
class Field: pass
class EmailStr: pass
class ConfigDict: pass
pydantic_mock = MagicMock()
pydantic_mock.BaseModel = BaseModel
pydantic_mock.Field = Field
pydantic_mock.EmailStr = EmailStr
pydantic_mock.ConfigDict = ConfigDict
sys.modules['pydantic'] = pydantic_mock

# Mock sqlalchemy
class Column: pass
class Integer: pass
class String: pass
class Float: pass
class DateTime: pass
class Boolean: pass
class Text: pass
class func: pass
class case: pass
class cast: pass
class and_: pass
class or_: pass

class Session: pass

sqlalchemy_mock = MagicMock()
sqlalchemy_mock.Column = Column
sqlalchemy_mock.Integer = Integer
sqlalchemy_mock.String = String
sqlalchemy_mock.Float = Float
sqlalchemy_mock.DateTime = DateTime
sqlalchemy_mock.Boolean = Boolean
sqlalchemy_mock.Text = Text
sqlalchemy_mock.func = func
sqlalchemy_mock.case = case
sqlalchemy_mock.cast = cast
sqlalchemy_mock.and_ = and_
sqlalchemy_mock.or_ = or_
sys.modules['sqlalchemy'] = sqlalchemy_mock
sys.modules['sqlalchemy.ext'] = MagicMock()
sys.modules['sqlalchemy.ext.declarative'] = MagicMock()
sys.modules['sqlalchemy.orm'] = MagicMock()
sys.modules['sqlalchemy.exc'] = MagicMock()

# Import the module under test
from blank_business_builder.api_licensing import get_license_status

print("Successfully imported!")
