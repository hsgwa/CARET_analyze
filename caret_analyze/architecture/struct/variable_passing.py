
from __future__ import annotations

from typing import (
    Iterable,
    Iterator,
    List,
    Optional,
    Tuple,
)

from .callback import CallbacksStruct, CallbackStruct
from ..reader_interface import ArchitectureReader, UNDEFINED_STR
from ...value_objects import NodeValue, VariablePassingStructValue


class VariablePassingStruct():

    def __init__(
        self,
        node_name: Optional[str] = None,
        callback_write: Optional[CallbackStruct] = None,
        callback_read: Optional[CallbackStruct] = None,
    ) -> None:
        self._node_name = node_name
        self._callback_write = callback_write
        self._callback_read = callback_read

    @property
    def node_name(self) -> str:
        assert self._node_name is not None
        return self._node_name

    @property
    def callback_write(self) -> CallbackStruct:
        assert self._callback_write is not None
        return self._callback_write

    def callback_read(self) -> CallbackStruct:
        assert self._callback_read is not None
        return self._callback_read

    def to_value(self) -> VariablePassingStructValue:
        return VariablePassingStructValue(
            node_name=self.node_name,
            callback_write=self.callback_write,
            callback_read=self.callback_read,
        )


class VariablePassingsStruct(Iterable):

    def __init__(self) -> None:
        self._data: List[VariablePassingStruct] = []

    def add(self, var_pass: VariablePassingStruct):
        self._data.append(var_pass)

    def __iter__(self) -> Iterator[VariablePassingStruct]:
        return iter(self._data)

    @staticmethod
    def create_from_reader(
        reader: ArchitectureReader,
        callbacks: CallbacksStruct,
        node: NodeValue,
    ) -> VariablePassingsStruct:
        var_passes = VariablePassingsStruct()

        for var_pass_value in reader.get_variable_passings(node.node_name):
            if var_pass_value.callback_id_read == UNDEFINED_STR or\
                    var_pass_value.callback_id_write == UNDEFINED_STR:
                continue
            var_pass = VariablePassingStruct(
                    node.node_name,
                    callback_write=callbacks.get_callback(var_pass_value.callback_id_write),
                    callback_read=callbacks.get_callback(var_pass_value.callback_id_read)
                )
            var_passes.add(var_pass)

        return var_passes

    def to_value(self) -> Tuple[VariablePassingStructValue, ...]:
        return tuple(_.to_value() for _ in self._data)
