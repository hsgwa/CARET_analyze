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

from logging import getLogger
from typing import Dict, List, Optional, Sequence, Set, Tuple

from .reader_interface import ArchitectureReader
from .struct import (
    CommunicationsStruct,
    ExecutorsStruct,
    NodesStruct,
    PathsStruct,
)
from ..common import Progress, Util
from ..exceptions import InvalidReaderError
from ..value_objects import (
    CallbackGroupValue,
    CommunicationStructValue,
    ExecutorStructValue,
    ExecutorValue,
    NodeStructValue,
    NodeValue,
    PathStructValue,
    PathValue,
    PublisherValue,
    SubscriptionCallbackValue,
    SubscriptionValue,
    TimerCallbackValue,
    TimerValue,
    TransformBroadcasterValue,
    TransformBufferValue,
    TransformValue,
    VariablePassingValue,
)

logger = getLogger(__name__)


class ArchitectureLoaded():
    def __init__(
        self,
        reader: ArchitectureReader,
        ignore_topics: List[str]
    ) -> None:

        topic_ignored_reader = TopicIgnoredReader(reader, ignore_topics)

        nodes = NodesStruct.create_from_reader(topic_ignored_reader)
        self._nodes = nodes.to_value()

        executors = ExecutorsStruct.create_from_reader(topic_ignored_reader, nodes)
        self._executors = executors.to_value()

        comms = CommunicationsStruct(nodes)
        self._communications = comms.to_value()

        paths = PathsStruct(topic_ignored_reader, nodes, comms)
        self._paths = paths.to_value()

        return None

    @property
    def paths(self) -> Tuple[PathStructValue, ...]:
        return self._paths

    @property
    def executors(self) -> Tuple[ExecutorStructValue, ...]:
        return self._executors

    @property
    def nodes(self) -> Tuple[NodeStructValue, ...]:
        return self._nodes

    @property
    def communications(self) -> Tuple[CommunicationStructValue, ...]:
        return self._communications


class TopicIgnoredReader(ArchitectureReader):
    def __init__(
        self,
        reader: ArchitectureReader,
        ignore_topics: List[str],
    ) -> None:
        self._reader = reader
        self._ignore_topics = ignore_topics
        self._ignore_callback_ids = self._get_ignore_callback_ids(reader, ignore_topics)

    def _get_publishers(self, node: NodeValue) -> Sequence[PublisherValue]:
        publishers: List[PublisherValue] = []
        for publisher in self._reader._get_publishers(node):
            if publisher.topic_name in self._ignore_topics:
                continue
            publishers.append(publisher)
        return publishers

    def get_tf_frames(self) -> Sequence[TransformValue]:
        return self._reader.get_tf_frames()

    def _get_timers(self, node: NodeValue) -> Sequence[TimerValue]:
        timers: List[TimerValue] = []
        for timer in self._reader._get_timers(node):
            timers.append(timer)
        return timers

    def _get_callback_groups(
        self,
        node: NodeValue
    ) -> Sequence[CallbackGroupValue]:
        return [
            CallbackGroupValue(
                cbg.callback_group_type.type_name,
                cbg.node_name,
                cbg.node_id,
                tuple(set(cbg.callback_ids) - self._ignore_callback_ids),
                cbg.callback_group_id,
                callback_group_name=cbg.callback_group_name
            )
            for cbg
            in self._reader._get_callback_groups(node)
        ]

    def get_executors(self) -> Sequence[ExecutorValue]:
        return self._reader.get_executors()

    def _get_message_contexts(
        self,
        node: NodeValue
    ) -> Sequence[Dict]:
        return self._reader._get_message_contexts(node)

    def _get_tf_buffer(self, node: NodeValue) -> Optional[TransformBufferValue]:
        return self._reader._get_tf_buffer(node)

    def _get_tf_broadcaster(self, node: NodeValue) -> Optional[TransformBroadcasterValue]:
        return self._reader._get_tf_broadcaster(node)

    def _filter_callback_id(
        self,
        callback_ids: Tuple[str, ...]
    ) -> Tuple[str, ...]:
        def is_not_ignored(callback_id: str):
            return callback_id not in self._ignore_callback_ids

        return tuple(Util.filter_items(is_not_ignored, callback_ids))

    @staticmethod
    def _get_ignore_callback_ids(
        reader: ArchitectureReader,
        ignore_topics: List[str]
    ) -> Set[str]:
        ignore_callback_ids: List[str] = []
        ignore_topic_set = set(ignore_topics)

        nodes = reader.get_nodes()
        for node in Progress.tqdm(nodes, 'Loading callbacks'):

            sub = reader._get_subscription_callbacks(node)
            for sub_val in sub:
                if sub_val.subscribe_topic_name not in ignore_topic_set:
                    continue

                if sub_val.callback_id is None:
                    continue

                ignore_callback_ids.append(sub_val.callback_id)

        return set(ignore_callback_ids)

    def get_paths(self) -> Sequence[PathValue]:
        return self._reader.get_paths()

    def get_nodes(self) -> Sequence[NodeValue]:
        nodes = self._reader.get_nodes()
        nodes_: List[NodeValue] = []
        node_names = set()
        for node in nodes:
            if node.node_name not in node_names:
                node_names.add(node.node_name)
                nodes_.append(node)
        try:
            self._validate(nodes)
        except InvalidReaderError as e:
            logger.warn(e)
        nodes_ = sorted(nodes_, key=lambda x: x.node_name)

        return nodes_

    @staticmethod
    def _validate(nodes: Sequence[NodeValue]):
        from itertools import groupby

        # validate node name uniqueness.
        node_names = [n.node_name for n in nodes]
        duplicated: List[str] = []
        for node_name, group in groupby(node_names):
            if len(list(group)) >= 2:
                duplicated.append(node_name)
        if len(duplicated) >= 1:
            raise InvalidReaderError(f'Duplicated node name. {duplicated}. Use first node only.')

    def _get_subscriptions(self, node: NodeValue) -> List[SubscriptionValue]:
        subscriptions: List[SubscriptionValue] = []
        for subscription in self._reader._get_subscriptions(node):
            if subscription.topic_name in self._ignore_topics:
                continue
            subscriptions.append(subscription)
        return subscriptions

    def _get_variable_passings(
        self,
        node: NodeValue
    ) -> Sequence[VariablePassingValue]:
        return self._reader._get_variable_passings(node)

    def _get_timer_callbacks(
        self,
        node: NodeValue
    ) -> Sequence[TimerCallbackValue]:
        return self._reader.get_timer_callbacks(node.node_name)

    def _get_subscription_callbacks(
        self,
        node: NodeValue
    ) -> Sequence[SubscriptionCallbackValue]:
        callbacks: List[SubscriptionCallbackValue] = []
        for subscription_callback in self._reader._get_subscription_callbacks(node):
            if subscription_callback.subscribe_topic_name in self._ignore_topics:
                continue
            callbacks.append(subscription_callback)
        return callbacks
