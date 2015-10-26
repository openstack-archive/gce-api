# Copyright 2014
# The Cloudscaling Group, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
SQLAlchemy models for gceapi data.
"""

from oslo_db.sqlalchemy import models
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Index, PrimaryKeyConstraint, String, Text


BASE = declarative_base()


class Item(BASE, models.ModelBase):
    __tablename__ = 'items'
    __table_args__ = (
        PrimaryKeyConstraint('kind', 'id'),
        Index('items_project_kind_name_idx', 'project_id', 'kind', 'name'),
    )
    id = Column(String(length=255))
    project_id = Column(String(length=255))
    kind = Column(String(length=50))
    name = Column(String(length=63))
    data = Column(Text())

    def save(self, session=None):
        from gceapi.db.sqlalchemy import api
        if session is None:
            session = api.get_session()

        super(Item, self).save(session=session)
