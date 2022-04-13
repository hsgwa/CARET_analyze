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

from typing import Optional, List, Union
from itertools import product
from logging import getLogger

from ..struct.callback import CallbackStruct
from .graph_search import Graph, GraphNode, GraphPath
from ..struct.struct_interface import (
    CallbackStructInterface,
    NodeInputType,
    NodeOutputType,
    NodePathStructInterface,
    NodePathsStructInterface,
    NodeStructInterface,
    PublisherStructInterface,
    SubscriptionStructInterface,
    TransformFrameBroadcasterStructInterface,
    TransformFrameBufferStructInterface,
    VariablePassingStructInterface,
)
from ...common import Util
from ...exceptions import ItemNotFoundError, MultipleItemFoundError

logger = getLogger(__name__)


class CallbackPathSearcher:

    def __init__(
        self,
        node: NodeStructInterface,
        node_paths: NodePathsStructInterface,
    ) -> None:
        self._node = node
        self._paths = node_paths

        callbacks = node.callbacks
        var_passes = node.variable_passings

        if callbacks is None or var_passes is None:
            return

        self._graph = Graph()

        for callback in callbacks:
            if callback.callback_name is None:
                continue

            write_name = self._to_node_point_name(callback.callback_name, 'write')
            read_name = self._to_node_point_name(callback.callback_name, 'read')

            self._graph.add_edge(GraphNode(read_name), GraphNode(write_name))

        for var_pass in var_passes:
            if var_pass.callback_name_read is None:
                continue
            if var_pass.callback_name_write is None:
                continue

            write_name = self._to_node_point_name(var_pass.callback_name_write, 'write')
            read_name = self._to_node_point_name(var_pass.callback_name_read, 'read')

            self._graph.add_edge(GraphNode(write_name), GraphNode(read_name))

    def search(
        self,
        start_callback: CallbackStruct,
        end_callback: CallbackStruct,
    ) -> None:
        start_name = self._to_node_point_name(start_callback.callback_name, 'read')
        end_name = self._to_node_point_name(end_callback.callback_name, 'write')

        graph_paths = self._graph.search_paths(GraphNode(start_name), GraphNode(end_name))

        for graph_path in graph_paths:
            in_value = start_callback.node_input
            out_values = end_callback.node_outputs or []

            if out_values is None or out_values == ():
                self._to_path(graph_path, in_value, None)

            for out_value in out_values:
                self._to_path(graph_path, in_value, out_value)

    def _to_path(
        self,
        callbacks_graph_path: GraphPath,
        node_in_value: Optional[NodeInputType],
        node_out_value: Optional[NodeOutputType],
    ) -> NodePathStructInterface:
        child: List[Union[CallbackStructInterface, VariablePassingStructInterface]] = []

        graph_nodes = callbacks_graph_path.nodes
        graph_node_names = [_.node_name for _ in graph_nodes]

        for graph_node_from, graph_node_to in zip(graph_node_names[:-1], graph_node_names[1:]):
            cb_or_varpass = self._find_cb_or_varpass(graph_node_from, graph_node_to)
            child.append(cb_or_varpass)

        node_in: Union[None, SubscriptionStructInterface, TransformFrameBufferStructInterface]
        node_in = None
        node_out: Union[None, PublisherStructInterface, TransformFrameBroadcasterStructInterface]
        node_out = None

        if node_in_value is not None:
            try:
                node_in = self._node.get_node_in(node_in_value)
            except ItemNotFoundError:
                msg = 'Failed to find subscription. '
                msg += f'node_name: {self._node.node_name}, '
                msg += f'topic_name: {node_in_value}'
                logger.warning(msg)
            except MultipleItemFoundError:
                msg = 'Failed to identify subscription. Several candidates were found. '
                msg += f'node_name: {self._node.node_name}, '
                msg += f'topic_name: {node_in_value}'
                logger.warning(msg)

        if node_out_value is not None:
            try:
                node_out = self._node.get_node_out(node_out_value)
            except ItemNotFoundError:
                msg = 'Failed to find publisher. '
                msg += f'node_name: {self._node.node_name}'
                msg += f'topic_name: {node_out_value}'
                logger.warning(msg)
            except MultipleItemFoundError:
                msg = 'Failed to identify publisher. Several candidates were found. '
                msg += f'node_name: {self._node.node_name}, '
                msg += f'topic_name: {node_out_value}'
                logger.warning(msg)

        tf_buffer: Optional[TransformFrameBufferStructInterface] = None
        tf_broadcaster: Optional[TransformFrameBroadcasterStructInterface] = None

        node_path = self._paths.get(node_in, node_out)
        node_path.node_name = self._node.node_name

        if isinstance(node_in, SubscriptionStruct):
            node_path.subscription = node_in
        elif isinstance(node_in, TransformFrameBufferStruct):
            node_path.tf_buffer = node_in

        if isinstance(node_out, PublisherStruct):
            node_path.publisher = node_out
        elif isinstance(node_out, TransformFrameBroadcasterStruct):
            node_path.tf_broadcaster = tf_broadcaster

        node_path.child = child

        return node_path

    def _find_cb_or_varpass(
        self,
        graph_node_from: str,
        graph_node_to: str,
    ) -> Union[CallbackStructInterface, VariablePassingStructInterface]:
        read_write_name_ = self._point_name_to_read_write_name(graph_node_from)

        read_read_name = self._point_name_to_read_write_name(graph_node_to)

        if read_write_name_ == 'write' or read_read_name == 'read':
            return self._find_varpass(graph_node_from, graph_node_to)

        if read_write_name_ == 'read' or read_read_name == 'write':
            return self._find_cb(graph_node_from, graph_node_to)

        raise InvalidArgumentError('')

    def _find_varpass(
        self,
        graph_node_from: str,
        graph_node_to: str,
    ) -> VariablePassingStructInterface:

        def is_target(var_pass:  VariablePassingStructInterface):
            if graph_node_to is not None:
                read_cb_name = self._point_name_to_callback_name(graph_node_to)
                read_cb_match = var_pass.callback_name_read == read_cb_name

            if graph_node_from is not None:
                write_cb_name = self._point_name_to_callback_name(
                    graph_node_from)
                write_cb_match = var_pass.callback_name_write == write_cb_name

            if read_cb_match is None and write_cb_match is None:
                return False

            return read_cb_match and write_cb_match

        try:
            return Util.find_one(is_target, self._node.variable_passings)
        except ItemNotFoundError:
            pass
        raise ItemNotFoundError('')

    def _find_cb(
        self,
        graph_node_from: str,
        graph_node_to: str,
    ) -> CallbackStructInterface:
        def is_target(callback: CallbackStructInterface):
            callback_name = self._point_name_to_callback_name(graph_node_from)
            return callback.callback_name == callback_name

        callbacks = self._node.callbacks
        return Util.find_one(is_target, callbacks)

    @staticmethod
    def _to_node_point_name(callback_name: str, read_or_write: str) -> str:
        return f'{callback_name}@{read_or_write}'

    @staticmethod
    def _point_name_to_callback_name(point_name: str) -> str:
        return point_name.split('@')[0]

    @staticmethod
    def _point_name_to_read_write_name(point_name: str) -> str:
        return point_name.split('@')[1]


class CallbackPathSearch():
    def __init__(
        self,
        node: NodeStructInterface,
        node_paths: NodePathsStructInterface
    ) -> None:
        searcher = CallbackPathSearcher(node, node_paths)

        callbacks = node.callbacks

        if callbacks is None:
            return None

        for write_callback, read_callback in product(callbacks, callbacks):
            searcher.search(write_callback, read_callback)
