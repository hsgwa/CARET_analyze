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

from caret_analyze.architecture.graph_search.graph_search import (
    Graph,
    GraphEdge,
    GraphNode,
    GraphPath,
    GraphPathCore
)

from caret_analyze.architecture.graph_search.node_graph import (
    NodePathSearcher
)


from caret_analyze.value_objects import (
    CommunicationStructValue,
    NodePathStructValue,
    NodeStructValue,
    PathStructValue,
    PublisherStructValue,
    SubscriptionStructValue,
)

from pytest_mock import MockerFixture


class TestNodePathSearcher:

    def test_empty(self, mocker: MockerFixture):
        searcher = NodePathSearcher((), ())

        assert searcher.search('node_name_not_exist', 'node_name_not_exist', 0) == []

        node_mock = mocker.Mock(spec=NodeStructValue)
        mocker.patch.object(node_mock, 'paths', [])
        mocker.patch.object(node_mock, 'node_name', 'node')
        mocker.patch.object(node_mock, 'publish_topic_names', [])
        mocker.patch.object(node_mock, 'subscribe_topic_names', [])
        searcher = NodePathSearcher((node_mock,), ())
        paths = searcher.search('node', 'node')

        assert paths == []

        searcher = NodePathSearcher((), ())
        paths = searcher.search('node', 'node')

        assert paths == []

    def test_search(self, mocker: MockerFixture):
        graph_mock = mocker.Mock(spec=Graph)
        mocker.patch(
            'caret_analyze.architecture.graph_search.node_graph.Graph',
            return_value=graph_mock)
        searcher = NodePathSearcher((), ())

        src_node = GraphNode('start_node_name')
        dst_node = GraphNode('end_node_name')

        graph_path_mock = mocker.Mock(spec=GraphPathCore)
        mocker.patch.object(graph_mock, 'search_paths',
                            return_value=[graph_path_mock])

        path_mock = mocker.Mock(spec=PathStructValue)
        mocker.patch.object(searcher, '_to_path', return_value=path_mock)
        paths = searcher.search('start_node_name', 'end_node_name')

        assert paths == [path_mock]
        assert graph_mock.search_paths.call_args == (
            (src_node, dst_node, 0), )

    def test_to_path(self, mocker: MockerFixture):
        node_name = '/node'
        topic_name = '/topic'

        node_mock = mocker.Mock(spec=NodeStructValue)
        comm_mock = mocker.Mock(spec=CommunicationStructValue)
        node_path_mock = mocker.Mock(spec=NodePathStructValue)

        mocker.patch.object(node_path_mock, 'publish_topic_name', topic_name)
        mocker.patch.object(node_path_mock, 'subscribe_topic_name', topic_name)
        mocker.patch.object(node_path_mock, 'node_name', node_name)

        mocker.patch.object(comm_mock, 'publish_node_name', node_name)
        mocker.patch.object(comm_mock, 'subscribe_node_name', node_name)
        mocker.patch.object(comm_mock, 'topic_name', topic_name)

        mocker.patch.object(node_mock, 'paths', [node_path_mock])

        mocker.patch.object(
            NodePathSearcher, '_create_head_dummy_node_path', return_value=node_path_mock)

        mocker.patch.object(
            NodePathSearcher, '_create_tail_dummy_node_path', return_value=node_path_mock)

        searcher = NodePathSearcher((node_mock,), (comm_mock,))
        graph_path_mock = mocker.Mock(spec=GraphPath)
        edge_mock = mocker.Mock(GraphEdge)
        mocker.patch.object(
            graph_path_mock, 'nodes',
            [GraphNode(node_name)],
        )
        mocker.patch.object(edge_mock, 'node_name_from', node_name)
        mocker.patch.object(edge_mock, 'node_name_to', node_name)
        mocker.patch.object(edge_mock, 'label', topic_name)
        mocker.patch.object(
            graph_path_mock, 'edges', [edge_mock]
        )
        pub_mock = mocker.Mock(spec=PublisherStructValue)
        mocker.patch.object(NodePathSearcher, '_get_publisher', return_value=pub_mock)
        sub_mock = mocker.Mock(spec=SubscriptionStructValue)
        mocker.patch.object(NodePathSearcher, '_get_subscription', return_value=sub_mock)
        path = searcher._to_path(graph_path_mock)

        expected = PathStructValue(
            None, (node_path_mock, comm_mock, node_path_mock)
        )
        assert path == expected

    def test_single_node_cyclic_case(self, mocker: MockerFixture):
        node_name = '/node'
        topic_name = '/chatter'

        node_mock = mocker.Mock(spec=NodeStructValue)

        node_path_mock = mocker.Mock(spec=NodePathStructValue)
        mocker.patch.object(node_mock, 'paths', (node_path_mock,))
        mocker.patch.object(node_mock, 'node_name', node_name)
        mocker.patch.object(node_mock, 'publish_topic_names', [topic_name])
        mocker.patch.object(node_mock, 'subscribe_topic_names', [topic_name])

        mocker.patch.object(node_path_mock, 'publish_topic_name', topic_name)
        mocker.patch.object(node_path_mock, 'subscribe_topic_name', topic_name)
        mocker.patch.object(node_path_mock, 'node_name', node_name)

        comm_mock = mocker.Mock(spec=CommunicationStructValue)
        mocker.patch.object(comm_mock, 'topic_name', topic_name)
        mocker.patch.object(comm_mock, 'publish_node_name', node_name)
        mocker.patch.object(comm_mock, 'subscribe_node_name', node_name)

        mocker.patch.object(
            NodePathSearcher, '_create_head_dummy_node_path', return_value=node_path_mock)

        mocker.patch.object(
            NodePathSearcher, '_create_tail_dummy_node_path', return_value=node_path_mock)

        searcher = NodePathSearcher((node_mock,), (comm_mock,))
        paths = searcher.search(node_name, node_name)

        expect = PathStructValue(
            None,
            (node_path_mock, comm_mock, node_path_mock),
        )
        assert paths == [expect]