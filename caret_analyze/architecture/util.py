# Copyright 2021 Research Institute of Systems Planning, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

from typing import Tuple, Union

from logging import StreamHandler, getLogger, INFO

from ..value_objects import NodePathStructValue, NodeStructValue
from .architecture_loaded import NodeValuesLoaded
from .architecture_reader_factory import ArchitectureReaderFactory
from .architecture import Architecture


def check_procedure(
    file_type: str,
    file_path: str,
    app_arch: Architecture,
    node_name: str,
) -> Tuple[NodePathStructValue, ...]:

    handler = StreamHandler()
    handler.setLevel(INFO)

    root_logger = getLogger()
    root_logger.addHandler(handler)

    reader = ArchitectureReaderFactory.create_instance(file_type, file_path)
    node = app_arch.get_node(node_name)

    paths = NodeValuesLoaded._search_node_paths(node, reader)

    root_logger.removeHandler(handler)
    return paths