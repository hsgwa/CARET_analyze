from __future__ import annotations

from logging import getLogger

from typing import Union, Optional, List, Tuple, Iterable, Iterator
from itertools import product

from .publisher import PublisherStruct
from .struct_interface import (
    CallbackStructInterface,
    NodeInputType,
    NodeOutputType,
    NodePathStructInterface,
    NodePathsStructInterface,
    NodeStructInterface,
    TransformFrameBroadcasterStructInterface,
    TransformFrameBufferStructInterface,
)
from .subscription import SubscriptionStruct
from .transform import TransformFrameBroadcasterStruct, TransformFrameBufferStruct
from .variable_passing import VariablePassingStruct
from ..graph_search.callback_graph import CallbackPathSearch
from ..reader_interface import ArchitectureReader, UNDEFINED_STR
from ...value_objects import MessageContext, NodePathStructValue
from ...exceptions import (
    Error,
    ItemNotFoundError,
)

logger = getLogger(__name__)


NodeSend = Union[PublisherStruct, TransformFrameBroadcasterStruct]
NodeRecv = Union[SubscriptionStruct, TransformFrameBufferStruct]


class NodePathStruct(NodePathStructInterface):

    def __init__(
        self,
        node_name: str,
        node_input: Optional[NodeInputType],
        node_output: Optional[NodeOutputType],
        child: Optional[List[Union[CallbackStructInterface, VariablePassingStruct]]] = None,
        message_context: Optional[MessageContext] = None,
    ) -> None:
        self._node_name = node_name
        self._node_input = node_input
        self._node_output = node_output
        self._child = child
        self._message_context = message_context

    @property
    def publisher(self) -> Optional[PublisherStruct]:
        if isinstance(self._node_output, PublisherStruct):
            return self._node_output
        return None

    @property
    def node_input(self) -> Optional[NodeInputType]:
        return self._node_input

    @property
    def node_output(self) -> Optional[NodeOutputType]:
        return self._node_output

    @property
    def tf_frame_broadcaster(self) -> Optional[TransformFrameBroadcasterStructInterface]:
        if isinstance(self._node_output, TransformFrameBroadcasterStructInterface):
            return self._node_output
        return None

    @property
    def subscription(self) -> Optional[SubscriptionStruct]:
        if isinstance(self._node_input, SubscriptionStruct):
            return self._node_input
        return None

    @property
    def tf_frame_buffer(self) -> Optional[TransformFrameBufferStructInterface]:
        if isinstance(self._node_input, TransformFrameBufferStructInterface):
            return self._node_input
        return None

    def to_value(self) -> NodePathStructValue:
        assert self.node_name is not None
        # assert self.publisher is not None or self.tf_frame_broadcaster is not None
        if self.publisher is not None and self.publisher.topic_name == '/tf':
            assert None

        publisher = None if self.publisher is None else self.publisher.to_value()
        subscription = None if self.subscription is None else self.subscription.to_value()
        tf_frame_buffer = None if self.tf_frame_buffer is None else self.tf_frame_buffer.to_value()
        tf_frame_br = None if self.tf_frame_broadcaster is None \
            else self.tf_frame_broadcaster.to_value()
        child = None if self.child is None else tuple(
            _.to_value() for _ in self.child)
        msg_contxt = self.message_context

        return NodePathStructValue(
            node_name=self.node_name,
            subscription=subscription,
            publisher=publisher,
            tf_frame_buffer=tf_frame_buffer,
            tf_frame_broadcaster=tf_frame_br,
            child=child,
            message_context=msg_contxt
        )

    @property
    def node_name(self) -> str:
        assert self._node_name is not None
        return self._node_name

    # @node_name.setter
    # def node_name(self, node_name: str) -> None:
    #     self._node_name = node_name

    # @property
    # def publish_topic_name(self) -> Optional[str]:
    #     if self.publisher is not None:
    #         return self.publisher.topic_name
    #     return None

    # @property
    # def subscribe_topic_name(self) -> Optional[str]:
    #     if self.subscription is not None:
    #         return self.subscription.topic_name
    #     return None

    @property
    def message_context(self) -> Optional[MessageContext]:
        return self._message_context

    @message_context.setter
    def message_context(self, message_context: MessageContext):
        self._message_context = message_context

    @property
    def child(self) -> Optional[List[Union[CallbackStructInterface, VariablePassingStruct]]]:
        return self._child

    @child.setter
    def child(self, child: List[Union[CallbackStructInterface, VariablePassingStruct]]):
        self._child = child

    # def __eq__(self, __o: object) -> bool:
    #     if isinstance(__o, NodePathStruct):
    #         return self.key == __o.key
    #     return False

    # def __hash__(self) -> int:
    #     h = 17
    #     for k in self.key:
    #         h += h * 31 + hash(k)
    #     return h

    # def _create_callack_chain(
    #     self
    # ) -> List[MessageContext]:
    #     chains: List[MessageContext] = []
    #     for path in node_paths:
    #         if path.callbacks is not None:
    #             chains.append(
    #                 CallbackChain(
    #                     path.node_name,
    #                     {},
    #                     path.subscription,
    #                     path.publisher,
    #                     path.callbacks)
    #             )
    #     return chains

    # @property
    # def key(self) -> Tuple[str, ...]:
    #     keys: List[str] = []
    #     sub_topic_name = ''
    #     if self.subscription is not None:
    #         sub_topic_name = self.subscription.topic_name
    #     keys.append(sub_topic_name)

    #     if self.tf_broadcaster is not None:
    #         keys.append(self.tf_broadcaster.transform.frame_id)
    #         keys.append(self.tf_broadcaster.transform.child_frame_id)

    #     pub_topic_name = ''
    #     if self.publisher is not None:
    #         pub_topic_name = self.publisher.topic_name
    #     keys.append(pub_topic_name)

    #     if self.tf_buffer is not None:
    #         keys.append(self.tf_buffer.transform.frame_id)
    #         keys.append(self.tf_buffer.transform.child_frame_id)

    #     return tuple(keys)


class NodePathsStruct(NodePathsStructInterface, Iterable):

    def __init__(
        self,
    ) -> None:
        self._data: List[NodePathStruct] = []

    def insert(self, node_path: NodePathStruct) -> None:
        self._data.append(node_path)

    def to_value(self) -> Tuple[NodePathStructValue, ...]:
        return tuple(_.to_value() for _ in self._data)

    def __iter__(self) -> Iterator[NodePathStruct]:
        return iter(self._data)

    def get(
        self,
        node_name: str,
        node_input: Optional[NodeInputType],
        node_output: Optional[NodeOutputType]
    ) -> NodePathStruct:
        for node_path in self:
            if node_path.node_input == node_input and \
                node_path.node_output == node_output and \
                    node_path.node_name == node_name:
                return node_path

        raise ItemNotFoundError('Failed to find node path')

    def get_by_context_dict(
        self,
        node_name: str,
        subscribe_topic_name: str,
        publish_topic_name: str,
        lookup_frame_id: Optional[str] = None,
        lookup_child_frame_id: Optional[str] = None,
        broadcast_frame_id: Optional[str] = None,
        broadcast_child_frame_id: Optional[str] = None,
    ) -> NodePathStruct:
        for node_path in self._data:
            if node_path.node_name != node_name:
                continue

            if node_path.publisher is not None and \
                    node_path.publisher.topic_name != publish_topic_name:
                continue
            if node_path.tf_frame_broadcaster is None and \
                    publish_topic_name == '/tf':
                continue

            if node_path.subscription is not None and \
                    node_path.subscription.topic_name != subscribe_topic_name:
                continue

            if node_path.tf_frame_buffer is not None and \
                    subscribe_topic_name == '/tf':
                continue
            return node_path

        raise ItemNotFoundError('Failed to find node path')

    def create(
        self,
        node_name: str,
        node_input: Optional[NodeInputType],
        node_output: Optional[NodeOutputType]
    ) -> None:
        node_path = NodePathStruct(node_name, node_input, node_output)
        self._data.append(node_path)

    @staticmethod
    def _search_node_paths(
        node: NodeStructInterface,
        reader: ArchitectureReader
    ) -> List[NodePathStruct]:
        raise NotImplementedError('')

    # def get_node_in(
    #     self,
    #     node_in: NodeIOValue
    # ) -> Union[SubscriptionStruct, TransformFrameBufferStruct]:
    #     raise NotImplementedError('')

    # def get_node_out(
    #     self,
    #     node_in: NodeIOValue
    # ) -> Union[PublisherStruct, TransformFrameBroadcasterStruct]:
    #     raise NotImplementedError('')

    @staticmethod
    def create_from_reader(
        reader: ArchitectureReader,
        node: NodeStructInterface,
    ) -> NodePathsStruct:
        node_paths = NodePathsStruct()

        for node_input in node.node_inputs:
            node_paths.create(node.node_name, node_input, None)

        for node_output in node.node_outputs:
            node_paths.create(node.node_name, None, node_output)

        for node_input, node_output in product(node.node_inputs, node.node_outputs):
            node_paths.create(node.node_name, node_input, node_output)

        # assign callback-graph paths
        logger.info('[callback_chain]')
        CallbackPathSearch(node, node_paths)

        # assign message contexts
        MessageContexts.create_from_reader(node_paths, reader, node)

        return node_paths


class MessageContexts(Iterable):

    def __init__(
        self,
    ) -> None:
        pass

    # @staticmethod
    # def _to_struct(
    #     context_dict: Dict,
    #     node_path: NodePathStruct
    # ) -> MessageContext:
    #     # type_name = context_dict['context_type']
    #     try:
    #         pass
    #         # return MessageContext.create_instance(
    #         #     type_name,
    #         #     context_dict,
    #         #     node_path.node_name,
    #         #     node_path.subscription,
    #         #     node_path.publisher,
    #         #     node_path.callbacks)
    #     except UnsupportedTypeError:
    #         raise InvalidYamlFormatError(
    #             'Failed to load message context. '
    #             f'node_name: {node_path.node_name}, '
    #             f'context: {context_dict}')

    # def __iter__(self) -> Iterator[MessageContext]:
    #     return iter(self._data)

    @staticmethod
    def create_from_reader(
        node_paths: NodePathsStruct,
        reader: ArchitectureReader,
        node: NodeStructInterface,
    ) -> None:
        # node_path = node_paths.get(
        #     message_context.subscription_topic_name,
        #     message_context.publisher_topic_name
        # )
        # node_path.message_context = message_context
        # self._data: Tuple[MessageContext, ...]
        # data: List[MessageContext] = []

        context_dicts = reader.get_message_contexts(node.node_name)
        # pub_sub_pairs: List[Tuple[Optional[str], Optional[str]]] = []
        for context_dict in context_dicts:
            try:
                context_type = context_dict.get('context_type')
                assert isinstance(context_type, str)
                if context_type == UNDEFINED_STR:
                    logger.info(
                        f'message context is UNDEFINED. {context_dict}')
                    continue

                pub_topic_name = context_dict['publisher_topic_name']
                node_output: NodeOutputType
                if pub_topic_name == '/tf':
                    assert node.tf_broadcaster is not None
                    node_output = node.tf_broadcaster.get(
                        context_dict['broadcast_frame_id'],
                        context_dict['broadcast_child_frame_id'],
                    )
                else:
                    assert node.publishers is not None
                    assert isinstance(pub_topic_name, str)
                    node_output = node.publishers.get(node.node_name, pub_topic_name)

                sub_topic_name = context_dict.get('subscription_topic_name')
                node_input: NodeInputType
                if sub_topic_name == '/tf':
                    assert node.tf_buffer is not None
                    node_input = node.tf_buffer.get(
                        context_dict['lookup_frame_id'],
                        context_dict['lookup_child_frame_id'],
                    )
                else:
                    assert node.subscriptions is not None
                    assert isinstance(sub_topic_name, str)
                    node_input = node.subscriptions.get(node.node_name, sub_topic_name)

                node_path = node_paths.get(node.node_name, node_input, node_output)

                node_path.message_context = MessageContext.create_instance(
                    context_type_name=context_type,
                    context_dict=context_dict,
                    node_name=node.node_name,
                    node_in=node_input.to_value(),
                    node_out=node_output.to_value(),
                    child=None
                )
            except Error as e:
                logger.warning(e)
        # logger.info(f'\n{len(node_paths)} paths found in {node.node_name}.')

        logger.info('\n-----\n[message context assigned]')
        for path in node_paths:
            message_context_name = UNDEFINED_STR
            if path.message_context is not None:
                message_context_name = path.message_context.type_name

            # logger.info(
            #     f'subscribe: {path.subscribe_topic_name}, '
            #     f'publish: {path.publish_topic_name}, '
            #     f'message_context: {message_context_name}'
            # )

        # for context in self._create_callack_chain(node_paths):
        #     pub_sub_pair = (context.publisher_topic_name, context.subscription_topic_name)
        #     if context not in data and pub_sub_pair not in pub_sub_pairs:
        #         data.append(context)