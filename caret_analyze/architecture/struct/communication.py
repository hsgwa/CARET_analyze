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

from typing import Tuple, List, Union
from itertools import product
from logging import getLogger

from caret_analyze.architecture.struct.transform import TransformFrameBroadcasterStruct, TransformFrameBroadcastersStruct, TransformFrameBufferStruct

from .callback import CallbackStruct
from .node import NodeStruct, NodesStruct
from .publisher import PublisherStruct
from .subscription import SubscriptionStruct
from ...exceptions import ItemNotFoundError, MultipleItemFoundError
from ...common import Progress
from ...value_objects import (
    CommunicationStructValue,
    TransformCommunicationStructValue,
)


logger = getLogger(__name__)


class CommunicationStruct():

    def __init__(
        self,
        nodes: NodesStruct,
        pub: PublisherStruct,
        sub: SubscriptionStruct,
        node_pub: NodeStruct,
        node_sub: NodeStruct,
    ) -> None:
        from ...common import Util

        self._sub = sub
        self._pub = pub
        self._node_pub = node_pub
        self._node_sub = node_sub

        self._callback_pub = None
        self._callback_sub = None
        # try:
        #     callbacks_pub = None
        #     is_target_pub_cb = CommunicationsStruct.IsTargetPubCallback(pub)
        #     callbacks = nodes.get_node(pub.node_name).callbacks
        #     callbacks_pub = Util.filter_items(is_target_pub_cb, callbacks)
        # except ItemNotFoundError:
        #     logger.info(f'Failed to find publisher callback. {node_pub}. Skip loading')
        # except MultipleItemFoundError:
        #     msg = 'Failed to identify subscription. Several candidates were found. Skip loading.'
        #     msg += f'node_name: {node_sub.node_name}, '
        #     msg += f'topic_name: {sub.topic_name}'
        #     logger.warning(msg)

        # try:
        #     callback_sub = None
        #     is_target_sub_cb = CommunicationsStruct.IsTargetSubCallback(sub)
        #     callback_values = nodes.get_node(sub.node_name).callbacks
        #     callback_sub = Util.find_one(is_target_sub_cb, callback_values)
        # except ItemNotFoundError:
        #     logger.info(f'Failed to find publisher callback. {node_sub}. Skip loading')
        # except MultipleItemFoundError:
        #     msg = 'Failed to identify subscription. Several candidates were found. Skip loading.'
        #     msg += f'node_name: {node_sub.node_name}, '
        #     msg += f'topic_name: {sub.topic_name}'
        #     logger.warning(msg)

    @property
    def callback_sub(self) -> None:
        return self._callback_sub

    @property
    def callbacks_pub(self) -> None:
        return self._callback_pub

    @property
    def node_pub(self) -> NodeStruct:
        return self._node_pub

    @property
    def node_sub(self) -> NodeStruct:
        return self._node_sub

    @property
    def publisher(self) -> PublisherStruct:
        return self._pub

    @property
    def subscription(self) -> SubscriptionStruct:
        return self._sub

    def to_value(self) -> Union[CommunicationStructValue, TransformCommunicationStructValue]:
        callbacks_pub = None if self.callbacks_pub is None else self.callbacks_pub.to_value()
        callback_sub = None if self.callback_sub is None else self.callback_sub.to_value()

        return CommunicationStructValue(
            self.node_pub.to_value(),
            self.node_sub.to_value(),
            self.publisher.to_value(),
            self.subscription.to_value(),
            callbacks_pub,
            callback_sub)


class TransformCommunicationStruct():
    def __init__(
        self,
        broadcaster: TransformFrameBroadcasterStruct,
        buffer: TransformFrameBufferStruct,
    ) -> None:
        self._broadcaster = broadcaster
        self._buffer = buffer

    @property
    def buffer(self) -> TransformFrameBufferStruct:
        return self._buffer

    @property
    def broadcaster(self) -> TransformFrameBroadcasterStruct:
        return self._broadcaster

    def to_value(self) -> TransformCommunicationStructValue:
        return TransformCommunicationStructValue(
            broadcaster=self.broadcaster.to_value(),
            buffer=self.buffer.to_value(),
        )


class CommunicationsStruct():

    def __init__(
        self,
        nodes: NodesStruct
    ) -> None:
        data: List[Union[CommunicationStruct, TransformCommunicationStruct]] = []
        pub_sub_pair = product(nodes, nodes)

        node_recv: NodeStruct
        node_send: NodeStruct
        for node_recv, node_send in Progress.tqdm(pub_sub_pair, 'Searching communications.'):
            for node_input, node_output in product(node_recv.node_inputs, node_send.node_outputs):
                if not node_input.is_pair(node_output):
                    continue

                comm: Union[CommunicationStruct, TransformCommunicationStruct]

                if isinstance(node_input, TransformFrameBufferStruct) and \
                        isinstance(node_output, TransformFrameBroadcasterStruct):
                    comm = TransformCommunicationStruct(node_output, node_input)
                elif isinstance(node_input, SubscriptionStruct) and \
                        isinstance(node_output, PublisherStruct):
                    comm = CommunicationStruct(
                        nodes,
                        node_output,
                        node_input,
                        node_recv,
                        node_send,
                    )
                else:
                    NotImplementedError(f'Unsupported communication: {node_input} -> {node_output}')
                data.append(comm)

        self._data = data

    def to_value(self) -> Tuple[CommunicationStructValue, ...]:
        return tuple(_.to_value() for _ in self._data)

    def find_communication(
        self,
        topic_name: str,
        publish_node_name: str,
        subscribe_node_name: str,
    ) -> CommunicationStruct:
        from ...common import Util

        def is_target(comm: CommunicationStruct):
            return comm.publish_node_name == publish_node_name and \
                comm.subscribe_node_name == subscribe_node_name and \
                comm.topic_name == topic_name
        try:
            return Util.find_one(is_target, self._data)
        except ItemNotFoundError:
            msg = 'Failed to find communication. '
            msg += f'topic_name: {topic_name}, '
            msg += f'publish_node_name: {publish_node_name}, '
            msg += f'subscribe_node_name: {subscribe_node_name}, '

            raise ItemNotFoundError(msg)

    class IsTargetPubCallback:

        def __init__(self, publish: PublisherStruct):
            self._publish = publish

        def __call__(self, callback: CallbackStruct) -> bool:
            if callback.publish_topic_names is None:
                return False
            return self._publish.topic_name in callback.publish_topic_names

    class IsTargetSubCallback:

        def __init__(self, subscription: SubscriptionStruct):
            self._subscription = subscription

        def __call__(self, callback: CallbackStruct) -> bool:
            if callback.subscribe_topic_name is None:
                return False
            return self._subscription.topic_name == callback.subscribe_topic_name
