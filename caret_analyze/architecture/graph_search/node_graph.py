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

from logging import getLogger
from typing import (
    Callable,
    Dict,
    List,
    Optional,
    Tuple,
    Union
)


from .graph_search import Graph, GraphEdge, GraphNode, GraphPath

from ...common import Util
from ...exceptions import InvalidArgumentError, ItemNotFoundError
from ...value_objects import (
    CommunicationStructValue,
    TransformCommunicationStructValue,
    NodePathStructValue,
    NodeStructValue,
    PathStructValue,
    PublisherStructValue,
    SubscriptionStructValue,
)

logger = getLogger(__name__)

NodePathKey = Tuple[Optional[str], Optional[str], Optional[str]]


class CommunicationWrapper():

    def __init__(
        self,
        comm: Union[TransformCommunicationStructValue, CommunicationStructValue]
    ):
        self._data = comm
        if isinstance(comm, TransformCommunicationStructValue):
            self._input_node_name = comm.buffer.lookup_node_name
            self._output_node_name = comm.broadcaster.node_name
        else:
            self._input_node_name = comm.subscribe_node_name
            self._output_node_name = comm.publish_node_name

    @property
    def input_node_name(self) -> str:
        return self._input_node_name

    @property
    def output_node_name(self) -> str:
        return self._output_node_name

    @property
    def topic_name(self) -> str:
        return self._data.topic_name

    def get_key(self) -> Tuple[str, ...]:
        return (self.output_node_name, self.input_node_name, self.topic_name)


class NodePathWrapper():

    def __init__(self, node_path: NodePathStructValue):
        self._data = node_path
        if node_path.tf_frame_broadcaster is not None:
            self._output_topic_name = node_path.tf_frame_broadcaster.topic_name
        else:
            self._output_topic_name = node_path.publish_topic_name

        if node_path.tf_frame_buffer is not None:
            self._input_topic_name = node_path.tf_frame_buffer.topic_name
        else:
            self._input_topic_name = node_path.subscribe_topic_name

    @property
    def output_topic_name(self) -> Optional[str]:
        return self._output_topic_name

    @property
    def input_topic_name(self) -> Optional[str]:
        return self._input_topic_name

    @property
    def node_name(self) -> str:
        return self._data.node_name

    def get_key(self) -> Tuple[str, ...]:
        return (self.input_topic_name, self.output_topic_name, self.node_name)


class NodePathSearcher:

    def __init__(
        self,
        nodes: Tuple[NodeStructValue, ...],
        communications: Tuple[CommunicationStructValue, ...],
        node_filter: Optional[Callable[[str], bool]] = None,
        communication_filter: Optional[Callable[[str], bool]] = None,
    ) -> None:
        self._nodes = nodes
        self._comms = [CommunicationWrapper(_) for _ in communications]

        self._graph = Graph()

        self._node_path_dict: Dict[NodePathKey, NodePathStructValue] = {}
        self._comm_dict: Dict[Tuple[str, str, str], CommunicationStructValue] = {}

        node_paths: List[NodePathWrapper]
        node_paths = [NodePathWrapper(_) for _ in Util.flatten([n.paths for n in self._nodes])]

        for node_path in node_paths:
            key = node_path.get_key()
            if key not in self._node_path_dict:
                self._node_path_dict[key] = node_path
            else:
                logger.warning(
                    'duplicated node_path found. skip adding. '
                    f'node_name: {node_path.node_name}, '
                    f'subscribe_topic_name: {node_path.subscribe_topic_name}, '
                    f'publish_topic_name: {node_path.publish_topic_name}')

        for comm in self._comms:
            if communication_filter is not None and \
                    not communication_filter(comm.topic_name):
                continue
            if node_filter is not None and not node_filter(comm.output_node_name):
                continue
            if node_filter is not None and not node_filter(comm.input_node_name):
                continue

            key = comm.get_key()
            if key not in self._comm_dict:
                self._comm_dict[key] = comm
            else:
                logger.warning(
                    'duplicated communication found. skip adding.'
                    f'topic_name: {comm.topic_name}, '
                    f'publish_node_name: {comm.publish_node_name}, '
                    f'subscribe_node_name: {comm.subscribe_node_name}, ')
                continue

            self._graph.add_edge(
                GraphNode(comm.output_node_name),
                GraphNode(comm.input_node_name),
                comm.topic_name
            )

    @staticmethod
    def _node_path_key(
        subscribe_topic_name: Optional[str],
        publish_topic_name: Optional[str],
        node_name: Optional[str]
    ) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        return (subscribe_topic_name, publish_topic_name, node_name)

    def search(
        self,
        start_node_name: str,
        end_node_name: str,
        max_node_depth: Optional[int] = None
    ) -> List[PathStructValue]:
        paths: List[PathStructValue] = []

        max_search_depth = max_node_depth or 0

        graph_paths = self._graph.search_paths(
            GraphNode(start_node_name),
            GraphNode(end_node_name),
            max_search_depth)

        for graph_path in graph_paths:
            paths.append(self._to_path(graph_path))

        return paths

    def _find_node(self, node_name: str) -> NodeStructValue:
        try:
            return Util.find_one(lambda x: x.node_name == node_name, self._nodes)
        except ItemNotFoundError:
            msg = 'Failed to find node. '
            msg += f'node_name: {node_name}. '
            raise ItemNotFoundError(msg)

    @staticmethod
    def _get_publisher(
        nodes: Tuple[NodeStructValue, ...],
        node_name: str,
        topic_name: str
    ) -> PublisherStructValue:
        node: NodeStructValue
        node = Util.find_one(lambda x: x.node_name == node_name, nodes)
        return node.get_publisher(topic_name)

    @staticmethod
    def _get_subscription(
        nodes: Tuple[NodeStructValue, ...],
        node_name: str,
        topic_name: str
    ) -> SubscriptionStructValue:
        node: NodeStructValue
        node = Util.find_one(lambda x: x.node_name == node_name, nodes)
        return node.get_subscription(topic_name)

    # @staticmethod
    # def _create_head_dummy_node_path(
    #     nodes: Tuple[NodeStructValue, ...],
    #     head_edge: GraphEdge
    # ) -> NodePathStructValue:
    #     node_name = head_edge.node_name_from
    #     topic_name = head_edge.label
    #     publisher = NodePathSearcher._get_publisher(nodes, node_name, topic_name)
    #     return NodePathStructValue(
    #         node_name=node_name,
    #         subscription=None,
    #         publisher=publisher,
    #         child=None,
    #         message_context=None,
    #         tf_frame_broadcaster=None,
    #         tf_frame_buffer=None)

    # @staticmethod
    # def _create_tail_dummy_node_path(
    #     nodes: Tuple[NodeStructValue, ...],
    #     tail_edge: GraphEdge,
    # ) -> NodePathStructValue:
    #     node_name = tail_edge.node_name_to
    #     topic_name: str = tail_edge.label
    #     sub = NodePathSearcher._get_subscription(nodes, node_name, topic_name)
    #     return NodePathStructValue(
    #         node_name=node_name,
    #         subscription=sub,
    #         publisher=None,
    #         child=None,
    #         message_context=None,
    #         tf_frame_broadcaster=None,
    #         tf_frame_buffer=None)

    def _to_path(
        self,
        node_graph_path: GraphPath,
    ) -> PathStructValue:
        child: List[Union[NodePathStructValue, CommunicationStructValue]] = []

        # add head node path
        if len(node_graph_path.edges) == 0:
            raise InvalidArgumentError("path doesn't have any edges")
        # head_node_path = self._create_head_dummy_node_path(self._nodes, node_graph_path.edges[0])
        head_node_path = self._find_node_path(
            node_graph_path.edges[0].node_from
        )
        child.append(head_node_path)

        for edge_, edge in zip(node_graph_path.edges[:-1], node_graph_path.edges[1:]):
            comm = self._find_comm(
                edge_.node_from.node_name,
                edge_.node_to.node_name,
                edge_.label)
            child.append(comm)

            node = self._find_node_path(
                edge_.label,
                edge.label,
                edge_.node_to.node_name,
            )

            child.append(node)

        # add tail comm
        tail_edge = node_graph_path.edges[-1]
        comm = self._find_comm(
            tail_edge.node_name_from,
            tail_edge.node_name_to,
            tail_edge.label)
        child.append(comm)

        # add tail node path
        tail_node_path = self._create_tail_dummy_node_path(self._nodes, tail_edge)
        child.append(tail_node_path)

        path_info = PathStructValue(
            None,
            tuple(child)
        )
        return path_info

    def _find_comm(
        self,
        node_from: str,
        node_to: str,
        topic_name: str
    ) -> CommunicationStructValue:
        key = self._comm_key(node_from, node_to, topic_name)
        if key not in self._comm_dict:
            msg = 'Failed to find communication path. '
            msg += f'publish node name: {node_from}, '
            msg += f'subscription node name: {node_to}, '
            msg += f'topic name: {topic_name}, '
            raise ItemNotFoundError(msg)

        return self._comm_dict[key]

    def _find_node_path(
        self,
        sub_topic_name: str,
        pub_topic_name: str,
        node_name: str,
    ) -> NodePathStructValue:
        key = self._node_path_key(sub_topic_name, pub_topic_name, node_name)
        if key not in self._node_path_dict:
            msg = 'Failed to find node path. '
            msg += f'publish topic name: {pub_topic_name}, '
            msg += f'subscription topic name: {sub_topic_name}, '
            msg += f'node name: {node_name}, '
            raise ItemNotFoundError(msg)
        return self._node_path_dict[key]
