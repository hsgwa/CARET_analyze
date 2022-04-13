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

from typing import Dict, List, Optional, Sequence

from . import Lttng
from .value_objects import (
    PublisherValueLttng,
    TimerCallbackValueLttng,
    TransformBroadcasterValueLttng,
    TransformBufferValueLttng
)
from ...architecture.reader_interface import ArchitectureReader
from ...value_objects import (CallbackGroupValue,
                              ExecutorValue,
                              NodeValue,
                              PathValue,
                              SubscriptionCallbackValue,
                              SubscriptionValue,
                              TimerValue,
                              TransformValue,
                              VariablePassingValue)


class ArchitectureReaderLttng(ArchitectureReader):
    def __init__(
        self,
        lttng: Lttng
    ) -> None:
        self._lttng = lttng

    def get_nodes(self) -> Sequence[NodeValue]:
        return self._lttng.get_nodes()

    def _get_timer_callbacks(
        self,
        node: NodeValue
    ) -> Sequence[TimerCallbackValueLttng]:
        return self._lttng.get_timer_callbacks(node)

    def _get_variable_passings(
        self,
        node: NodeValue
    ) -> Sequence[VariablePassingValue]:
        return []

    def _get_message_contexts(
        self,
        node: NodeValue
    ) -> Sequence[Dict]:
        return []

    def get_executors(
        self
    ) -> Sequence[ExecutorValue]:
        return self._lttng.get_executors()

    def _get_subscription_callbacks(
        self,
        node: NodeValue
    ) -> Sequence[SubscriptionCallbackValue]:
        return self._lttng.get_subscription_callbacks(node)

    def _get_publishers(
        self,
        node: NodeValue
    ) -> Sequence[PublisherValueLttng]:
        return self._lttng.get_publishers(node)

    def _get_timers(
        self,
        node: NodeValue
    ) -> Sequence[TimerValue]:
        return self._lttng.get_timers(node)

    def _get_callback_groups(
        self,
        node: NodeValue
    ) -> Sequence[CallbackGroupValue]:
        return self._lttng.get_callback_groups(node)

    def get_paths(
        self
    ) -> Sequence[PathValue]:
        return []

    def get_tf_frames(
        self
    ) -> Sequence[TransformValue]:
        return self._lttng.get_tf_frames()

    def _get_subscriptions(
        self,
        node: NodeValue
    ) -> Sequence[SubscriptionValue]:
        info: List[SubscriptionValue] = []
        for sub_cb in self._get_subscription_callbacks(node):
            topic_name = sub_cb.subscribe_topic_name
            assert topic_name is not None
            info.append(SubscriptionValue(
                topic_name,
                sub_cb.node_name,
                sub_cb.node_id,
                sub_cb.callback_id
            ))
        return info

    def _get_tf_broadcaster(
        self,
        node: NodeValue
    ) -> Optional[TransformBroadcasterValueLttng]:
        return self._lttng.get_tf_broadcaster(node)

    def _get_tf_buffer(
        self,
        node: NodeValue
    ) -> Optional[TransformBufferValueLttng]:
        return self._lttng.get_tf_buffer(node)
