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

from __future__ import annotations

from typing import Optional, Tuple

from ....value_objects import (
    PublisherValue,
    TransformBroadcasterValue,
    TransformBufferValue,
    TransformValue,
)


class TransformBroadcasterValueLttng(TransformBroadcasterValue):
    def __init__(
        self,
        pub: PublisherValue,
        transforms: Tuple[TransformValue, ...],
        callback_ids: Tuple[str, ...],
        broadcaster_handler: int,
    ) -> None:
        super().__init__(pub, transforms, callback_ids)
        self._broadcaster_handler = broadcaster_handler

    @property
    def broadcaster_handler(self) -> int:
        return self._broadcaster_handler


class TransformBufferValueLttng(TransformBufferValue):
    def __init__(
        self,
        lookup_node_name: str,
        lookup_node_id: str,
        listener_node_name: Optional[str],
        listener_node_id: Optional[str],
        lookup_transforms: Optional[Tuple[TransformValue, ...]],
        buffer_handler: int
    ) -> None:
        super().__init__(
            lookup_node_name,
            lookup_node_id,
            listener_node_name,
            listener_node_id,
            lookup_transforms)
        self._buffer_handler = buffer_handler

    @property
    def buffer_handler(self) -> int:
        return self._buffer_handler
