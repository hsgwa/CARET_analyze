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

from abc import abstractmethod

from typing import (
    Dict,
    Iterable,
    Iterator,
    List,
    Optional,
    Tuple,
    Union,
)

from .publisher import PublisherStruct
from .struct_interface import CallbacksStructInterface, CallbackStructInterface
from .subscription import SubscriptionStruct
from .transform import TransformFrameBroadcasterStruct, TransformFrameBufferStruct
from ..reader_interface import ArchitectureReader
from ...common import Util
from ...exceptions import ItemNotFoundError, UnsupportedTypeError
from ...value_objects import (
    CallbackGroupValue,
    CallbackStructValue,
    CallbackValue,
    NodeValue,
    SubscriptionCallbackStructValue,
    SubscriptionCallbackValue,
    TimerCallbackStructValue,
    TimerCallbackValue,
)

NodeIn = Union[PublisherStruct, TransformFrameBroadcasterStruct]
NodeOut = Union[SubscriptionStruct, TransformFrameBufferStruct]


class CallbackStruct(CallbackStructInterface):

    def __init__(
        self,
        callback_name: str,
        callback_id: str,
        node_name: Optional[str] = None,
        symbol: Optional[str] = None,
        subscribe_topic_name: Optional[str] = None,
        publish_topic_names: Optional[List[str]] = None,
    ):
        self._node_name = node_name
        self._callback_name = callback_name
        self._callback_id = callback_id
        self._symbol = symbol
        self._subscribe_topic_name = subscribe_topic_name
        self._publish_topic_names = publish_topic_names

    @property
    def symbol(self) -> str:
        assert self._symbol is not None
        return self._symbol

    @property
    def callback_id(self) -> str:
        return self._callback_id

    @property
    def callback_name(self) -> str:
        return self._callback_name

    @property
    def node_name(self) -> str:
        assert self._node_name is not None
        return self._node_name

    @property
    def subscribe_topic_name(self) -> Optional[str]:
        return self._subscribe_topic_name

    @property
    def publish_topic_names(self) -> Optional[List[str]]:
        return self._publish_topic_names

    @staticmethod
    def create_instance(callback: CallbackValue, index: int) -> CallbackStruct:

        indexed = Util.indexed_name(f'{callback.node_name}/callback', index)

        callback_name = callback.callback_name or indexed
        callback_id = callback.callback_id
        publish_topic_names = None if callback.publish_topic_names is None \
            else list(callback.publish_topic_names)
        if isinstance(callback, TimerCallbackValue):

            return TimerCallbackStruct(
                node_name=callback.node_name,
                symbol=callback.symbol,
                period_ns=callback.period_ns,
                publish_topic_names=publish_topic_names,
                callback_name=callback_name,
                callback_id=callback_id
            )
        if isinstance(callback, SubscriptionCallbackValue):
            assert callback.subscribe_topic_name is not None
            return SubscriptionCallbackStruct(
                node_name=callback.node_name,
                symbol=callback.symbol,
                subscribe_topic_name=callback.subscribe_topic_name,
                publish_topic_names=publish_topic_names,
                callback_name=callback_name,
                callback_id=callback_id
            )
        raise UnsupportedTypeError('Unsupported callback type')

    @abstractmethod
    def to_value(self) -> CallbackStructValue:
        pass

    @property
    def node_in(self) -> Optional[NodeIn]:
        raise NotImplementedError('')

    @property
    def node_out(self) -> Optional[List[NodeOut]]:
        raise NotImplementedError('')


class TimerCallbackStruct(CallbackStruct):
    def __init__(
        self,
        callback_name: str,
        callback_id: str,
        period_ns: Optional[int] = None,
        node_name: Optional[str] = None,
        symbol: Optional[str] = None,
        subscribe_topic_name: Optional[str] = None,
        publish_topic_names: Optional[List[str]] = None,
    ) -> None:
        super().__init__(
            node_name=node_name,
            symbol=symbol,
            subscribe_topic_name=subscribe_topic_name,
            publish_topic_names=publish_topic_names,
            callback_name=callback_name,
            callback_id=callback_id)

        self._period_ns = period_ns

    @property
    def period_ns(self) -> int:
        assert self._period_ns is not None
        return self._period_ns

    def to_value(self) -> TimerCallbackStructValue:
        publish_topic_names = None if self.publish_topic_names is None \
            else tuple(self.publish_topic_names)

        return TimerCallbackStructValue(
            node_name=self.node_name,
            symbol=self.symbol,
            period_ns=self.period_ns,
            publish_topic_names=publish_topic_names,
            callback_name=self.callback_name,
            callback_id=self.callback_id
        )


class SubscriptionCallbackStruct(CallbackStruct):

    def __init__(
        self,
        callback_name: str,
        callback_id: str,
        node_name: Optional[str] = None,
        symbol: Optional[str] = None,
        subscribe_topic_name: Optional[str] = None,
        publish_topic_names: Optional[List[str]] = None,
    ) -> None:
        super().__init__(
            node_name=node_name,
            symbol=symbol,
            subscribe_topic_name=subscribe_topic_name,
            publish_topic_names=publish_topic_names,
            callback_name=callback_name,
            callback_id=callback_id)
        self.__subscribe_topic_name = subscribe_topic_name

    @property
    def subscribe_topic_name(self) -> str:
        assert self.__subscribe_topic_name is not None
        return self.__subscribe_topic_name

    def to_value(self) -> SubscriptionCallbackStructValue:
        publish_topic_names = None if self.publish_topic_names is None \
            else tuple(self.publish_topic_names)

        return SubscriptionCallbackStructValue(
            node_name=self.node_name,
            symbol=self.symbol,
            subscribe_topic_name=self.subscribe_topic_name,
            publish_topic_names=publish_topic_names,
            callback_name=self.callback_name,
            callback_id=self.callback_id
        )


class CallbacksStruct(CallbacksStructInterface, Iterable):

    def __init__(
        self,
        node: Optional[NodeValue] = None
    ) -> None:
        self._node = node
        self._cb_dict: Dict[str, CallbackStruct] = {}

    @property
    def node(self) -> NodeValue:
        assert self._node is not None
        return self._node

    def insert(self, callback: CallbackStruct) -> None:
        self._cb_dict[callback.callback_id] = callback

    def add(self, callbacks: CallbacksStruct) -> None:
        for callback in callbacks:
            self.insert(callback)
        return None

    @staticmethod
    def create_from_reader(
        reader: ArchitectureReader,
        node: NodeValue,
    ) -> CallbacksStruct:
        callbacks = CallbacksStruct()

        callback_values: List[CallbackValue] = []
        callback_values += reader.get_timer_callbacks(node.node_name)
        callback_values += reader.get_subscription_callbacks(node.node_name)

        for i, callback_value in enumerate(callback_values):
            callback = CallbackStruct.create_instance(callback_value, i)
            callbacks.insert(callback)

        return callbacks

    @property
    def node_name(self) -> str:
        assert self.node.node_name is not None
        return self.node.node_name

    def to_value(self) -> Tuple[CallbackStructValue, ...]:
        return tuple(_.to_value() for _ in self._cb_dict.values())

    # def _validate(self, callbacks: List[CallbackValue]) -> None:
    #     # check node name
    #     for callback in callbacks:
    #         if callback.node_id != self._node.node_id:
    #             msg = 'reader returns invalid callback value. '
    #             msg += f'get [{self._node.node_id}] value returns [{callback.node_id}]'
    #             raise InvalidReaderError(msg)

    #     # check callback name
    #     cb_names: List[str] = [
    #         cb.callback_name for cb in callbacks if cb.callback_name is not None]
    #     if len(cb_names) != len(set(cb_names)):
    #         msg = f'Duplicated callback names. node_name: {self._node.node_name}\n'
    #         for name in set(cb_names):
    #             if cb_names.count(name) >= 2:
    #                 msg += f'callback name: {name} \n'
    #         raise InvalidReaderError(msg)

    #     # check callback id
    #     cb_ids: List[str] = [
    #         cb.callback_id
    #         for cb
    #         in callbacks
    #         if cb.callback_id is not None
    #     ]
    #     if len(cb_names) != len(set(cb_names)):
    #         msg = f'Duplicated callback id. node_name: {self._node.node_name}\n'
    #         for cb_id in set(cb_ids):
    #             if cb_ids.count(cb_id) >= 2:
    #                 msg += f'callback id: {cb_id} \n'
    #         raise InvalidReaderError(msg)

    def get_callback_by_cbg(
        self,
        callback_group: CallbackGroupValue
    ) -> CallbacksStruct:
        callback_structs = CallbacksStruct()

        for callback_id in callback_group.callback_ids:
            # Ensure that the callback information exists.
            callback_struct = self.get_callback(callback_id)
            callback_structs.insert(callback_struct)

        return callback_structs

    def get_callback(
        self,
        callback_id: str
    ) -> CallbackStruct:
        if callback_id in self._cb_dict:
            return self._cb_dict[callback_id]

        raise ItemNotFoundError(
            'Failed to find callback. '
            f'callback_id: {callback_id}, '
        )

    def get_callbacks(
        self,
        *callback_ids: str
    ) -> CallbacksStruct:
        """
        Get callbacks.

        Parameters
        ----------
        callback_ids : Tuple[str, ...]
            target callback ids

        Returns
        -------
        CallbacksStruct
            If the callback is not found, it returns an empty tuple.

        """
        callbacks = CallbacksStruct()

        for callback_id in callback_ids:
            if callback_id not in self._cb_dict.keys():
                continue
            callback = self.get_callback(callback_id)
            callbacks.insert(callback)

        return callbacks

    def __iter__(self) -> Iterator[CallbackStruct]:
        return iter(self._cb_dict.values())
