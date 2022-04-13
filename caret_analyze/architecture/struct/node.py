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
from typing import (
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Sequence,
    Tuple,
    Union,
)

from caret_analyze.value_objects.transform import TransformTreeValue


from .callback import CallbacksStruct
from .callback_group import CallbackGroupsStruct
from .node_path import NodePathsStruct
from .publisher import PublishersStruct, PublisherStruct
from .struct_interface import (
    NodeInputType,
    NodeOutputType,
    NodeStructInterface,
    NodeStructsInterface,
    PublisherStructInterface,
)
from .subscription import SubscriptionsStruct, SubscriptionStruct
from .timer import TimersStruct, TimerStruct
from .transform import (
    TransformBroadcasterStruct,
    TransformBufferStruct,
    TransformFrameBroadcastersStruct,
    TransformFrameBroadcasterStruct,
    TransformFrameBuffersStruct,
    TransformFrameBufferStruct,
)
from .variable_passing import VariablePassingsStruct
from ..reader_interface import ArchitectureReader
from ...common import Progress, Util
from ...exceptions import Error, ItemNotFoundError
from ...value_objects import (
    NodeStructValue,
    NodeValue
)


logger = getLogger(__name__)


class NodeStruct(NodeStructInterface):

    def __init__(
        self,
        node_id: str,
        node_name: str,
        publishers: Optional[PublishersStruct] = None,
        subscriptions: Optional[SubscriptionsStruct] = None,
        timers: Optional[TimersStruct] = None,
        node_paths: Optional[NodePathsStruct] = None,
        callback_groups: Optional[CallbackGroupsStruct] = None,
        variable_passings: Optional[VariablePassingsStruct] = None,
        tf_buffer: Optional[TransformBufferStruct] = None,
        tf_broadcaster: Optional[TransformBroadcasterStruct] = None,
    ) -> None:
        self._node_id = node_id
        self._node_name = node_name
        self._publishers = publishers
        self._subscriptions = subscriptions
        self._timers = timers
        self._node_paths = node_paths
        self._callback_groups = callback_groups
        self._variable_passings = variable_passings
        self._tf_buffer = tf_buffer
        self._tf_broadcaster = tf_broadcaster

    def to_value(self) -> NodeStructValue:
        assert self.node_name is not None
        assert self.node_id is not None
        assert self.publishers is not None
        assert self.subscriptions is not None
        assert self.node_paths is not None
        assert self.callback_groups is not None
        assert self.variable_passings is not None
        assert self.timers is not None

        return NodeStructValue(
            node_name=self.node_name,
            node_id=self.node_id,
            publishers=self.publishers.to_value(),
            subscriptions=self.subscriptions.to_value(),
            timers=self.timers.to_value(),
            node_paths=self.node_paths.to_value(),
            callback_groups=self.callback_groups.to_value(),
            variable_passings=self.variable_passings.to_value(),
            tf_buffer=None if self.tf_buffer is None else self.tf_buffer.to_value(),
            tf_broadcaster=None if self.tf_broadcaster is None else self.tf_broadcaster.to_value(),
        )

    @property
    def node_outputs(self) -> Sequence[NodeOutputType]:
        outputs: List[NodeOutputType]
        outputs = self.publishers.as_list()
        outputs = Util.filter_items(lambda x: x.topic_name != '/tf', outputs)
        outputs = Util.filter_items(
            lambda x: not x.topic_name.endswith('/info/pub'), outputs)
        if self.tf_broadcaster is not None:
            outputs += self.tf_broadcaster.frame_broadcasters.as_list()
        return outputs

    @property
    def tf_frame_buffers(self) -> Optional[TransformFrameBuffersStruct]:
        if self._tf_buffer is None or self._tf_buffer.frame_buffers is None:
            return None
        return self._tf_buffer.frame_buffers

    @property
    def tf_frame_broadcasters(self) -> Optional[TransformFrameBroadcastersStruct]:
        if self._tf_broadcaster is None:
            return None
        return self._tf_broadcaster.frame_broadcasters

    @property
    def tf_buffer(self) -> Optional[TransformBufferStruct]:
        return self._tf_buffer

    @tf_buffer.setter
    def tf_buffer(self, value: TransformBufferStruct) -> None:
        self._tf_buffer = value

    @property
    def tf_broadcaster(self) -> Optional[TransformBroadcasterStruct]:
        return self._tf_broadcaster

    @tf_broadcaster.setter
    def tf_broadcaster(self, value: TransformBroadcasterStruct) -> None:
        self._tf_broadcaster = value

    @property
    def node_name(self) -> str:
        assert self._node_name is not None
        return self._node_name

    @node_name.setter
    def node_name(self, node_name: str) -> None:
        self._node_name = node_name

    @property
    def node_id(self) -> str:
        assert self._node_id is not None
        return self._node_id

    @node_id.setter
    def node_id(self, node_id: str) -> None:
        self._node_id = node_id

    @property
    def subscriptions(self) -> SubscriptionsStruct:
        assert self._subscriptions is not None
        return self._subscriptions

    @subscriptions.setter
    def subscriptions(self, subscriptions: SubscriptionsStruct) -> None:
        self._subscriptions = subscriptions

    @property
    def publishers(self) -> PublishersStruct:
        assert self._publishers is not None
        return self._publishers

    @publishers.setter
    def publishers(self, publishers: PublishersStruct):
        self._publishers = publishers

    @property
    def node_paths(self) -> NodePathsStruct:
        assert self._node_paths is not None
        return self._node_paths

    @node_paths.setter
    def node_paths(self, node_paths: NodePathsStruct):
        self._node_paths = node_paths

    @property
    def timers(self) -> TimersStruct:
        assert self._timers is not None
        return self._timers

    @timers.setter
    def timers(self, timers: TimersStruct):
        self._timers = timers

    @property
    def callback_groups(self) -> CallbackGroupsStruct:
        assert self._callback_groups is not None
        return self._callback_groups

    @callback_groups.setter
    def callback_groups(self, callback_groups: CallbackGroupsStruct):
        self._callback_groups = callback_groups

    @property
    def callbacks(self) -> Optional[CallbacksStruct]:
        cbs = CallbacksStruct()
        for cbg in self.callback_groups:
            cbs.add(cbg.callbacks)
        return cbs

    @property
    def variable_passings(self) -> Optional[VariablePassingsStruct]:
        return self._variable_passings

    @variable_passings.setter
    def variable_passings(self, variable_passings: VariablePassingsStruct) -> None:
        self._variable_passings = variable_passings

    @property
    def node_inputs(self) -> Sequence[NodeInputType]:
        node_inputs = self.subscriptions.as_list()
        if self.tf_buffer is not None:
            node_inputs += self.tf_buffer.frame_buffers.as_list()
        return node_inputs

    # @property
    # def callback_names(self) -> Optional[List[str]]:
    #     if self.callbacks is None:
    #         return None
    #     return [_.callback_name for _ in self.callbacks]

    # @property
    # def callback_group_names(self) -> Optional[List[str]]:
    #     if self.callback_groups is None:
    #         return None
    #     return [_.callback_group_name for _ in self.callback_groups]

    # def get_subscription(
    #     self,
    #     subscribe_topic_name: str
    # ) -> SubscriptionStructValue:

    #     try:
    #         return Util.find_one(
    #             lambda x: x.topic_name == subscribe_topic_name,
    #             self.subscriptions)
    #     except ItemNotFoundError:
    #         msg = 'Failed to find subscription info. '
    #         msg += f'topic_name: {subscribe_topic_name}'
    #         raise ItemNotFoundError(msg)

    def get_publisher(
        self,
        publish_topic_name: str
    ) -> PublisherStruct:
        try:
            return Util.find_one(
                lambda x: x.topic_name == publish_topic_name,
                self.publishers)
        except ItemNotFoundError:
            msg = 'Failed to find publisher info. '
            msg += f'topic_name: {publish_topic_name}'
            raise ItemNotFoundError(msg)

    def get_timer(
        self,
        timer_period: str
    ) -> TimerStruct:
        try:
            return Util.find_one(
                lambda x: x.period == timer_period,
                self.publishers)
        except ItemNotFoundError:
            msg = 'Failed to find timer info. '
            msg += f'timer_period: {timer_period}'
            raise ItemNotFoundError(msg)

    @staticmethod
    def create_from_reader(
        node: NodeValue,
        reader: ArchitectureReader
    ) -> NodeStruct:
        node_struct = NodeStruct(
            node_id=node.node_name,
            node_name=node.node_name
        )

        callbacks = CallbacksStruct.create_from_reader(reader, node)
        node_struct.publishers = PublishersStruct.create_from_reader(
            reader, callbacks, node)

        node_struct.subscriptions = SubscriptionsStruct.create_from_reader(
            reader, callbacks, node)
        node_struct.subscriptions.to_value()

        node_struct.timers = TimersStruct.create_from_reader(
            reader, callbacks, node)
        node_struct.callback_groups = CallbackGroupsStruct.create_from_reader(
            reader, callbacks, node)
        node_struct.variable_passings = VariablePassingsStruct.create_from_reader(
            reader, callbacks, node)
        transforms = reader.get_tf_frames()
        tf_tree = TransformTreeValue.create_from_transforms(transforms)
        node_struct.tf_buffer = TransformBufferStruct.create_from_reader(
            reader, tf_tree, node)
        node_struct.tf_broadcaster = TransformBroadcasterStruct.create_from_reader(
            reader, tf_tree, callbacks, node)
        node_struct.node_paths = NodePathsStruct.create_from_reader(
            reader, node_struct)

        return node_struct


class NodesStruct(NodeStructsInterface, Iterable):

    def __init__(
        self,
    ) -> None:
        self._data: Dict[str, NodeStruct] = {}

    def to_value(self) -> Tuple[NodeStructValue, ...]:
        return tuple(_.to_value() for _ in self._data.values())

    def insert(self, node: NodeStruct) -> None:
        self._data[node.node_id] = node

    def add(self, nodes: Iterable[NodeStruct]) -> None:
        for node in nodes:
            self.insert(node)

    @property
    def callback_groups(self) -> CallbackGroupsStruct:
        cbgs = CallbackGroupsStruct()
        for node in self:
            cbgs.add(node.callback_groups)
        return cbgs

    def get_node(self, node_name: str) -> NodeStruct:
        try:
            return Util.find_one(lambda x: x.node_name == node_name, self)
        except ItemNotFoundError:
            msg = 'Failed to find node. '
            msg += f'node_name: {node_name}'
            raise ItemNotFoundError(msg)

    def __iter__(self) -> Iterator[NodeStruct]:
        return iter(self._data.values())

    @staticmethod
    def create_from_reader(
        reader: ArchitectureReader,
    ) -> NodesStruct:
        nodes = NodesStruct()

        node_values = reader.get_nodes()
        for node in Progress.tqdm(node_values, 'Loading nodes.'):
            # try:
            node = NodeStruct.create_from_reader(node, reader)
            nodes.insert(node)
            # except Error as e:
            #     logger.warn(f'Failed to load node. node_name = {node.node_name}, {e}')

        return nodes

    # def find_node_path(
    #     self,
    #     node_path_value: NodePathValue,
    # ) -> NodePathStructValue:
    #     def is_target(value: NodePathStructValue):
    #         return value.publish_topic_name == node_path_value.publish_topic_name and \
    #             value.subscribe_topic_name == node_path_value.subscribe_topic_name

    #     node_value = self.find_node(node_path_value.node_name)
    #     try:
    #         return Util.find_one(is_target, node_value.paths)
    #     except ItemNotFoundError:
    #         msg = 'Failed to find node path value. '
    #         msg += f' node_name: {node_path_value.node_name}'
    #         msg += f' publish_topic_name: {node_path_value.publish_topic_name}'
    #         msg += f' subscribe_topic_name: {node_path_value.subscribe_topic_name}'
    #         raise ItemNotFoundError(msg)
    #     except MultipleItemFoundError as e:
    #         raise MultipleItemFoundError(
    #             f'{e}'
    #             f' node_name: {node_path_value.node_name}'
    #             f' publish_topic_name: {node_path_value.publish_topic_name}'
    #             f' subscribe_topic_name: {node_path_value.subscribe_topic_name}'
    #         )

    # def find_callback_group(
    #     self,
    #     callback_group_id: str
    # ) -> CallbackGroupStruct:
    #     for cbg_loaded in self._cbgs:
    #         try:
    #             return cbg_loaded.find_callback_group(callback_group_id)
    #         except ItemNotFoundError:
    #             pass

    #     msg = f'Failed to find callback group. callback_group_id={callback_group_id}'
    #     raise ItemNotFoundError(msg)

    # def find_callback(
    #     self,
    #     callback_id: str
    # ) -> CallbackStruct:
    #     for cb_loaded in self._cbs:
    #         try:
    #             return cb_loaded.find_callback(callback_id)
    #         except ItemNotFoundError:
    #             pass
    #     raise ItemNotFoundError(f'Failed to find callback. callback_id={callback_id}')

    # def find_callbacks(
    #     self,
    #     callback_ids: Tuple[str, ...]
    # ) -> Tuple[CallbackStructValue, ...]:
    #     callbacks: List[CallbackStructValue] = []
    #     for cb in self._cbs:
    #         callbacks += cb.search_callbacks(callback_ids)

    #     if len(callbacks) < len(callback_ids):
    #         raise ItemNotFoundError(f'Failed to find callback. callback_ids={callback_ids}')

    #     return tuple(callbacks)

    # @staticmethod
    # def _message_context_assigned(
    #     node_paths: Sequence[NodePathStructValue],
    #     message_contexts: Sequence[MessageContext],
    # ) -> List[NodePathStructValue]:
    #     node_paths_ = list(node_paths)
    #     for i, node_path in enumerate(node_paths_):
    #         for context in message_contexts:
    #             if node_path.subscription is None or \
    #                     node_path.publisher is None:
    #                 continue

    #             if not context.is_applicable_path(
    #                 node_path.subscription,
    #                 node_path.publisher,
    #                 node_path.callbacks
    #             ):
    #                 continue

    #             node_paths_[i] = NodePathStructValue(
    #                 node_name=node_path.node_name,
    #                 subscription=node_path.subscription,
    #                 publisher=node_path.publisher,
    #                 child=node_path.child,
    #                 message_context=context,
    #                 tf_broadcaster=None,
    #                 tf_buffer=None
    #             )
    #     return node_paths_
