#    Copyright 2013 Cloudscaling Group, Inc
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

from sqlalchemy import Column, Index, MetaData, PrimaryKeyConstraint
from sqlalchemy import String, Table, Text


def upgrade(migrate_engine):
    meta = MetaData()
    meta.bind = migrate_engine

    items = Table('items', meta,
        Column("id", String(length=255)),
        Column("project_id", String(length=255)),
        Column("kind", String(length=50)),
        Column("name", String(length=63)),
        Column("data", Text()),
        PrimaryKeyConstraint('kind', 'id'),
        Index('items_project_kind_name_idx', 'project_id', 'kind', 'name'),
        mysql_engine="InnoDB",
        mysql_charset="utf8"
    )
    items.create()


def downgrade(migrate_engine):
    raise NotImplementedError("Downgrade from Icehouse is unsupported.")
