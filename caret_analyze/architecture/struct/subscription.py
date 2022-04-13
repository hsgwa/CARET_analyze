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
from typing import Any, Iterable, Iterator, List, Optional, Tuple

from .struct_interface import (
    CallbacksStructInterface,
    CallbackStructInterface,
    PublisherStructInterface,
    SubscriptionStructInterface,
)
from ..reader_interface import ArchitectureReader
from ...exceptions import Error
from ...value_objects import (
    NodeValue,
    SubscriptionStructValue,
    SubscriptionValue,
)

logger = getLogger(__name__)


class SubscriptionStruct(SubscriptionStructInterface):

    def __init__(
        self,
        node_name: str,
        topic_name: str,
        callback: Optional[CallbackStructInterface] = None,
    ) -> None:
        self._node_name: str = node_name
        self._topic_name: str = topic_name
        self._callback = callback
        self._is_transformed = False

    @property
    def node_name(self) -> str:
        return self._node_name

    @property
    def topic_name(self) -> str:
        return self._topic_name

    @property
    def callback(self) -> Optional[CallbackStructInterface]:
        return self._callback

    @callback.setter
    def callback(self, callback: CallbackStructInterface) -> None:
        assert self._is_transformed == False
        self._callback = callback

    def to_value(self) -> SubscriptionStructValue:
        self._is_transformed = True
        callback = None if self.callback is None else self.callback.to_value()
        return SubscriptionStructValue(
            node_name=self.node_name,
            topic_name=self.topic_name,
            callback=callback
        )

    def is_pair(self, other: Any) -> bool:
        if isinstance(other, PublisherStructInterface):
            return other.topic_name == self.topic_name
        return False

    @staticmethod
    def create_instance(
        callbacks: CallbacksStructInterface,
        subscription_value: SubscriptionValue,
    ) -> SubscriptionStruct:
        sub = SubscriptionStruct(subscription_value.node_name, subscription_value.topic_name)

        if subscription_value.callback_id is not None:
            callback = callbacks.get_callback(subscription_value.callback_id)
            sub.callback = callback

        return sub


class SubscriptionsStruct(Iterable):
    def __init__(
        self,
    ) -> None:
        self._data: List[SubscriptionStruct] = []
        self._is_transformed = False

    def to_value(self) -> Tuple[SubscriptionStructValue, ...]:
        self._is_transformed = True
        return tuple(subscription.to_value() for subscription in self)

    def __iter__(self) -> Iterator[SubscriptionStruct]:
        return iter(self._data)

    def add(self, subscription: SubscriptionStruct) -> None:
        assert self._is_transformed is False
        self._data.append(subscription)

    def as_list(self) -> List[SubscriptionStruct]:
        return list(self._data)

    def get(self, node_name: str, topic_name: str) -> Optional[SubscriptionStruct]:
        for subscription in self:
            if subscription.node_name == node_name and subscription.topic_name == topic_name:
                return subscription
        return None

    @staticmethod
    def create_from_reader(
        reader: ArchitectureReader,
        callbacks_loaded: CallbacksStructInterface,
        node: NodeValue
    ) -> SubscriptionsStruct:
        subscriptions = SubscriptionsStruct()
        subscription_values = reader.get_subscriptions(node.node_name)
        for sub_value in subscription_values:
            try:
                sub = SubscriptionStruct.create_instance(callbacks_loaded, sub_value)
                subscriptions.add(sub)
            except Error as e:
                logger.warning(e)
        return subscriptions
