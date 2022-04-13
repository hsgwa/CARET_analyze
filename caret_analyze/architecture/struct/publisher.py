from __future__ import annotations

from logging import getLogger
from typing import (
    Any,
    Iterable,
    Iterator,
    List,
    Optional,
    Tuple,
)

from .struct_interface import CallbacksStructInterface, PublisherStructInterface, SubscriptionStructInterface
from ..reader_interface import ArchitectureReader, UNDEFINED_STR
from ...common import Util
from ...exceptions import Error
from ...value_objects import (
    NodeValue,
    PublisherStructValue,
    PublisherValue,
)

logger = getLogger(__name__)


class PublisherStruct(PublisherStructInterface):

    def __init__(
        self,
        node_name: Optional[str] = None,
        topic_name: Optional[str] = None,
        callbacks: Optional[CallbacksStructInterface] = None
    ) -> None:
        self._node_name = node_name
        self._topic_name = topic_name
        self._callbacks = callbacks

    @property
    def node_name(self) -> str:
        assert self._node_name is not None
        return self._node_name

    def is_pair(self, other: Any) -> bool:
        if isinstance(other, SubscriptionStructInterface):
            return self.topic_name == other.topic_name
        return False

    @property
    def topic_name(self) -> str:
        assert self._topic_name is not None
        return self._topic_name

    @property
    def callbacks(self) -> Optional[CallbacksStructInterface]:
        return self._callbacks

    @callbacks.setter
    def callbacks(self, callbacks: CallbacksStructInterface):
        self._callbacks = callbacks

    def to_value(self) -> PublisherStructValue:
        callback_values = None if self.callbacks is None else self.callbacks.to_value()
        return PublisherStructValue(
            node_name=self.node_name,
            topic_name=self.topic_name,
            callback_values=callback_values,
        )

    @staticmethod
    def create_instance(
        callbacks: CallbacksStructInterface,
        publisher_value: PublisherValue,
    ) -> PublisherStruct:
        publisher = PublisherStruct()

        if publisher_value.callback_ids is not None:
            cb_ids = Util.filter_items(lambda x: x != UNDEFINED_STR, publisher_value.callback_ids)
            publisher.callbacks = callbacks.get_callbacks(*cb_ids)

        # TODO(hsgawa): delete here. and implement other way.
        # callbacks = PublishersStruct._get_callbacks(callbacks)
        # if len(pub_callbacks) == 0 and len(callbacks) == 1:
        #     pub_callbacks.append(callbacks[0])
        # for callback in callbacks:
        #     if callback.publish_topic_names is None:
        #         continue
        #     if publisher_value.topic_name in callback.publish_topic_names and \
        #             callback not in pub_callbacks:
        #         pub_callbacks.append(callback)

        return publisher


class PublishersStruct(Iterable):

    def __init__(
        self,
    ) -> None:
        self._data: List[PublisherStruct] = []

    def __iter__(self) -> Iterator[PublisherStruct]:
        return iter(self._data)

    def get(
        self,
        node_name: str,
        topic_name: str
    ) -> PublisherStruct:
        return Util.find_one(
            lambda pub: pub.topic_name == topic_name and pub.node_name == node_name, self
        )

    # @staticmethod
    # def _get_callbacks(
    #     callbacks_loaded: CallbacksStruct,
    # ) -> List[CallbackStructValue]:
    #     def is_user_defined(callback: CallbackStructValue):
    #         if isinstance(callback, SubscriptionCallbackStruct):
    #             if callback.subscribe_topic_name == '/parameter_events':
    #                 return False
    #         return True

    #     callbacks = callbacks_loaded.data
    #     return Util.filter_items(is_user_defined, callbacks)

    def to_value(self) -> Tuple[PublisherStructValue, ...]:
        return tuple(_.to_value() for _ in self._data)

    def insert(
        self,
        publisher: PublisherStruct
    ) -> None:
        self._data.append(publisher)

    def as_list(self) -> List[PublisherStruct]:
        return self._data

    @staticmethod
    def create_from_reader(
        reader: ArchitectureReader,
        callbacks: CallbacksStructInterface,
        node: NodeValue,
    ) -> PublishersStruct:
        publishers = PublishersStruct()

        for publisher_value in reader.get_publishers(node.node_name):
            try:
                if publisher_value.topic_name == '/tf':
                    continue

                pub_callbacks = None
                if publisher_value.callback_ids is not None:
                    pub_callbacks = callbacks.get_callbacks(*publisher_value.callback_ids)
                pub = PublisherStruct(
                    node_name=publisher_value.node_name,
                    topic_name=publisher_value.topic_name,
                    callbacks=pub_callbacks
                )
                publishers.insert(pub)
            except Error as e:
                logger.warning(e)

        return publishers
