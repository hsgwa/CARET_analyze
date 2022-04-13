from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Any, Iterator, Optional, Sequence, Union

from caret_analyze.value_objects.transform import TransformValue

from ...value_objects import (
    PublisherStructValue,
    SubscriptionStructValue,
    TransformFrameBroadcasterStructValue,
    TransformFrameBufferStructValue,
)


class PublisherStructInterface(metaclass=ABCMeta):

    @abstractmethod
    def to_value(self) -> PublisherStructValue:
        pass

    @property
    @abstractmethod
    def topic_name(self) -> str:
        pass

    @abstractmethod
    def is_pair(self, other: Any) -> bool:
        pass


class PublishersStructInterface(metaclass=ABCMeta):

    @abstractmethod
    def get(
        self,
        node_name: str,
        topic_name: str
    ) -> PublisherStructInterface:
        pass


class TransformFrameBroadcasterStructInterface(metaclass=ABCMeta):

    @abstractmethod
    def to_value(self) -> TransformFrameBroadcasterStructValue:
        pass

    @property
    @abstractmethod
    def transform(self) -> TransformValue:
        pass

    @abstractmethod
    def is_pair(self, other: Any) -> bool:
        pass


class TransformFrameBufferStructInterface(metaclass=ABCMeta):

    @property
    @abstractmethod
    def lookup_node_name(self) -> str:
        pass

    @property
    @abstractmethod
    def transform(self) -> TransformValue:
        pass

    @abstractmethod
    def to_value(self) -> TransformFrameBufferStructValue:
        pass

    @abstractmethod
    def is_pair(self, other: Any) -> bool:
        pass


class SubscriptionStructInterface(metaclass=ABCMeta):

    @property
    @abstractmethod
    def node_name(self) -> str:
        pass

    @property
    @abstractmethod
    def topic_name(self) -> str:
        pass

    @abstractmethod
    def to_value(self) -> SubscriptionStructValue:
        pass

    @abstractmethod
    def is_pair(self, other: Any) -> bool:
        pass


class SubscriptionsStructInterface(metaclass=ABCMeta):

    @abstractmethod
    def get(self, node_name: str, topic_name: str) -> SubscriptionStructInterface:
        pass


NodeOutputType = Union[TransformFrameBroadcasterStructInterface,
                       PublisherStructInterface]
NodeInputType = Union[TransformFrameBufferStructInterface,
                      SubscriptionStructInterface]


class NodeStructsInterface(metaclass=ABCMeta):
    pass


class VariablePassingStructInterface(metaclass=ABCMeta):

    @property
    @abstractmethod
    def callback_name_read(self) -> Optional[str]:
        pass

    @property
    @abstractmethod
    def callback_name_write(self) -> Optional[str]:
        pass


class VariablePassingsInterface(metaclass=ABCMeta):

    def __iter__(self) -> Iterator[VariablePassingStructInterface]:
        pass


class NodeStructInterface(metaclass=ABCMeta):

    @property
    @abstractmethod
    def node_name(self) -> str:
        pass

    @property
    @abstractmethod
    def callbacks(self) -> Optional[CallbacksStructInterface]:
        pass

    @property
    @abstractmethod
    def variable_passings(self) -> Optional[VariablePassingsInterface]:
        pass

    @property
    @abstractmethod
    def node_inputs(self) -> Sequence[NodeInputType]:
        pass

    @property
    @abstractmethod
    def node_outputs(self) -> Sequence[NodeOutputType]:
        pass

    @property
    @abstractmethod
    def publishers(self) -> Optional[PublishersStructInterface]:
        pass

    @property
    @abstractmethod
    def tf_broadcaster(self) -> Optional[TransformBroadcasterStructInterface]:
        pass

    @property
    @abstractmethod
    def subscriptions(self) -> Optional[SubscriptionsStructInterface]:
        pass

    @property
    @abstractmethod
    def tf_buffer(self) -> Optional[TransformBufferStructInterface]:
        pass


class TransformBroadcasterStructInterface(metaclass=ABCMeta):

    @abstractmethod
    def get(
        self,
        frame_id: str,
        child_frame_id: str
    ) -> TransformFrameBroadcasterStructInterface:
        pass


class TransformBufferStructInterface(metaclass=ABCMeta):

    @abstractmethod
    def get(
        self,
        frame_id: str,
        child_frame_id: str
    ) -> TransformFrameBufferStructInterface:
        pass


class NodePathStructInterface(metaclass=ABCMeta):

    @property
    @abstractmethod
    def node_input(self) -> Optional[NodeInputType]:
        pass

    @property
    @abstractmethod
    def node_output(self) -> Optional[NodeOutputType]:
        pass


class NodePathsStructInterface:

    @abstractmethod
    def get(
        self,
        node_name: str,
        node_input: Optional[NodeInputType],
        node_output: Optional[NodeOutputType]
    ) -> NodePathStructInterface:
        pass

    @abstractmethod
    def create(
        self,
        node_name: str,
        node_input: Optional[NodeInputType],
        node_output: Optional[NodeOutputType]
    ) -> None:
        pass


class CallbackStructInterface:

    @property
    @abstractmethod
    def node_input(self) -> Optional[NodeInputType]:
        pass

    @property
    @abstractmethod
    def node_outputs(self) -> Optional[Sequence[NodeOutputType]]:
        pass

    @property
    @abstractmethod
    def callback_name(self) -> str:
        pass


class CallbacksStructInterface:

    @abstractmethod
    def get_callback(
        self,
        callback_id: str
    ) -> CallbackStructInterface:
        pass

    @abstractmethod
    def get_callbacks(
        self,
        *callback_ids: str
    ) -> CallbacksStructInterface:
        pass

    def __iter__(self) -> Iterator[CallbackStructInterface]:
        pass
