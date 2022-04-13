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

from typing import List, Union


from .path_base import PathBase
from ..common import Summarizable
from ..infra import RecordsProvider, RuntimeDataProvider
from ..record import RecordsInterface
from ..value_objects import (
    TransformBroadcasterStructValue,
    TransformBufferStructValue,
    TransformValue,
)


class TransformFrameBuffer(PathBase):

    def __init__(
        self,
        buffer: TransformBufferStructValue,
        transform: TransformValue,
        provider: Union[RecordsProvider, RuntimeDataProvider]
    ) -> None:
        self._buff = buffer
        self._provider = provider
        self._transform = transform

    @property
    def frame_id(self) -> str:
        return self._transform.frame_id

    # @property
    # def summary(self) -> Summary:
    #     return self._buff.summary

    @property
    def child_frame_id(self) -> str:
        return self._transform.child_frame_id

    def _to_records_core(self) -> RecordsInterface:
        return self._provider.tf_set_lookup_records(self._buff, self._transform)


class TransformBuffer():

    def __init__(
        self,
        buffer: TransformBufferStructValue,
        provider: Union[RecordsProvider, RuntimeDataProvider]
    ) -> None:
        self._buff = buffer
        self._provider = provider

    @property
    def lookup_transforms(self) -> List[TransformValue]:
        return list(self._buff.lookup_transforms)

    def get(self, transform: TransformValue) -> TransformFrameBuffer:
        return TransformFrameBuffer(self._buff, transform, self._provider)


class TransformFrameBroadcaster(PathBase):
    def __init__(
        self,
        broadcaster: TransformBroadcasterStructValue,
        transform: TransformValue,
        provider: Union[RecordsProvider, RuntimeDataProvider]
    ) -> None:
        self._broadcaster = broadcaster
        self._transform = transform
        self._provider = provider

    @property
    def frame_id(self) -> str:
        return self._transform.frame_id

    @property
    def child_frame_id(self) -> str:
        return self._transform.child_frame_id

    @property
    def topic_name(self) -> str:
        return self._broadcaster.topic_name

    def _to_records_core(self) -> RecordsInterface:
        records = self._provider.tf_broadcast_records(self._broadcaster, self._transform)
        return records


class TransformBroadcaster():

    def __init__(
        self,
        broadcaster: TransformBroadcasterStructValue,
        provider: Union[RecordsProvider, RuntimeDataProvider]
    ) -> None:
        self._broadcaster = broadcaster
        self._provider = provider

    @property
    def transforms(self) -> List[TransformValue]:
        return list(self._broadcaster.transforms)

    def get(self, transforms: TransformValue):
        return TransformFrameBroadcaster(self._broadcaster, transforms, self._provider)

