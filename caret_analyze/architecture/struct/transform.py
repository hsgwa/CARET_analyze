from __future__ import annotations

from typing import Any, List, Optional, Iterable, Iterator

from caret_analyze.value_objects.transform import TransformTreeValue

from .struct_interface import (
    CallbacksStructInterface,
    TransformBroadcasterStructInterface,
    TransformBufferStructInterface,
    TransformFrameBroadcasterStructInterface,
    TransformFrameBufferStructInterface,
)
from .publisher import PublisherStruct
from ..reader_interface import ArchitectureReader
from ...value_objects import (
    NodeValue,
    TransformBroadcasterStructValue,
    TransformBufferStructValue,
    TransformFrameBroadcasterStructValue,
    TransformFrameBufferStructValue,
    TransformValue,
)


class TransformFrameBroadcasterStruct(TransformFrameBroadcasterStructInterface):
    def __init__(
        self,
        publisher: Optional[PublisherStruct] = None,
        transform: Optional[TransformValue] = None,
    ) -> None:
        self._publisher = publisher
        self._transform = transform

    def to_value(
        self
    ) -> TransformFrameBroadcasterStructValue:
        return TransformFrameBroadcasterStructValue(
            publisher=self.publisher.to_value(),
            transform=self.transform,
        )

    @property
    def node_name(self) -> str:
        return self.publisher.node_name

    def is_pair(self, other: Any) -> bool:
        if isinstance(other, TransformFrameBufferStructInterface):
            other.is_pair(self)
        return False

    @property
    def publisher(self) -> PublisherStruct:
        assert self._publisher is not None
        return self._publisher

    @property
    def frame_id(self) -> str:
        return self.transform.frame_id

    @property
    def child_frame_id(self) -> str:
        return self.transform.child_frame_id

    @property
    def transform(self) -> TransformValue:
        assert self._transform is not None
        return self._transform


class TransformFrameBufferStruct(TransformFrameBufferStructInterface):

    def __init__(
        self,
        tf_tree: TransformTreeValue,
        transform: Optional[TransformValue] = None,
        lookup_node_name: Optional[str] = None,
        listener_node_name: Optional[str] = None,
    ) -> None:
        assert isinstance(tf_tree, TransformTreeValue)

        self._transform = transform
        self._lookup_node_name = lookup_node_name
        self._listener_node_name = listener_node_name
        self._tf_tree = tf_tree

    @property
    def frame_id(self) -> str:
        return self.transform.frame_id

    @property
    def child_frame_id(self) -> str:
        return self.transform.child_frame_id

    def to_value(self) -> TransformFrameBufferStructValue:
        return TransformFrameBufferStructValue(
            lookup_node_name=self.lookup_node_name,
            listener_node_name=self.listener_node_name,
            transform=self.transform
        )

    def is_pair(self, other: Any) -> bool:
        if isinstance(other, TransformFrameBroadcasterStruct):
            return self._tf_tree.is_in(self.transform, other.transform)
        return False

    @property
    def lookup_node_name(self) -> str:
        assert self._lookup_node_name is not None
        return self._lookup_node_name

    @property
    def listener_node_name(self) -> Optional[str]:
        return self._listener_node_name

    @property
    def publisher(self) -> PublisherStruct:
        assert self._publisher is not None
        return self._publisher

    @property
    def transform(self) -> TransformValue:
        assert self._transform is not None
        return self._transform


class TransformFrameBroadcastersStruct(Iterable):

    def __init__(self) -> None:
        self._data: List[TransformFrameBroadcasterStruct] = []

    def as_list(self) -> List[TransformFrameBroadcasterStruct]:
        return list(self._data)

    def add(self, brs: TransformFrameBroadcastersStruct) -> None:
        for br in brs:
            self.insert(br)

    def __iter__(self) -> Iterator[TransformFrameBroadcasterStruct]:
        return iter(self._data)

    def insert(self, br: TransformFrameBroadcasterStruct) -> None:
        self._data.append(br)

    def get(
        self,
        node_name: str,
        frame_id: str,
        child_frame_id: str
    ) -> TransformFrameBroadcasterStruct:
        for br in self:
            if br.frame_id == frame_id and \
                    br.child_frame_id == child_frame_id and \
                    br.node_name == node_name:
                return br
        raise NotImplementedError('')


class TransformFrameBuffersStruct(Iterable):

    def __init__(self) -> None:
        self._data: List[TransformFrameBufferStruct] = []

    def add(self, brs: TransformFrameBuffersStruct) -> None:
        for br in brs:
            self.insert(br)

    def __iter__(self) -> Iterator[TransformFrameBufferStruct]:
        return iter(self._data)

    def as_list(self) -> List[TransformFrameBufferStruct]:
        return self._data

    def get(
        self,
        node_name: str,
        frame_id: str,
        child_frame_id: str
    ) -> TransformFrameBufferStruct:
        for buf in self:
            if buf.frame_id == frame_id and \
                buf.lookup_node_name == node_name and \
                    buf.child_frame_id == child_frame_id:
                return buf
        raise NotImplementedError('')

    def insert(self, br: TransformFrameBufferStruct) -> None:
        self._data.append(br)


class TransformBroadcasterStruct(TransformBroadcasterStructInterface):
    def __init__(
        self,
        publisher: PublisherStruct,
        transforms: List[TransformValue],
    ) -> None:
        self._publisher = publisher
        self._transforms = transforms
        self._frame_brs = TransformFrameBroadcastersStruct()

        for tf in transforms:
            frame_br = TransformFrameBroadcasterStruct(
                publisher=publisher,
                transform=tf,
            )
            self._frame_brs.insert(frame_br)

    def to_value(self) -> Optional[TransformBroadcasterStructValue]:
        return TransformBroadcasterStructValue(
            publisher=self.publisher.to_value(),
            transforms=self.transforms
        )

    def get(
        self,
        frame_id: str,
        child_frame_id: str
    ) -> TransformFrameBroadcasterStructInterface:
        return self.frame_broadcasters.get(
            self.publisher.node_name, frame_id, child_frame_id)

    @property
    def publisher(self) -> PublisherStruct:
        assert self._publisher is not None
        return self._publisher

    @property
    def transforms(self) -> List[TransformValue]:
        assert self._transforms is not None
        return self._transforms

    @staticmethod
    def create_from_reader(
        reader: ArchitectureReader,
        tf_tree: TransformTreeValue,
        callbacks: CallbacksStructInterface,
        node: NodeValue,
    ) -> Optional[TransformBroadcasterStruct]:
        broadcaster = reader.get_tf_broadcaster(node.node_name)

        if broadcaster is None:
            return None

        cb_ids = broadcaster.callback_ids or ()
        cbs = callbacks.get_callbacks(*cb_ids)
        tf_pub = PublisherStruct(node.node_name, '/tf', cbs)

        return TransformBroadcasterStruct(
            publisher=tf_pub,
            transforms=list(broadcaster.transforms)
        )

    @property
    def frame_broadcasters(self) -> TransformFrameBroadcastersStruct:
        return self._frame_brs


class TransformBufferStruct(TransformBufferStructInterface):

    def __init__(
        self,
        lookup_node_name: str,
        tf_tree: TransformTreeValue,
        lookup_transforms: List[TransformValue],
        listener_node_name: Optional[str] = None,
    ) -> None:
        self._lookup_node_name = lookup_node_name
        self._listener_node_name = listener_node_name
        self._lookup_transforms = lookup_transforms
        self._frame_buffs = TransformFrameBuffersStruct()
        for tf in lookup_transforms:
            buf = TransformFrameBufferStruct(
                tf_tree=tf_tree,
                lookup_node_name=lookup_node_name,
                listener_node_name=listener_node_name,
                transform=tf,
            )
            self._frame_buffs.insert(buf)

    @property
    def lookup_node_name(self) -> str:
        assert self._lookup_node_name is not None
        return self._lookup_node_name

    @property
    def lookup_transforms(self) -> List[TransformValue]:
        assert self._lookup_transforms is not None
        return self._lookup_transforms

    @property
    def listener_node_name(self) -> Optional[str]:
        return self._listener_node_name

    def is_pair(self, other: Any) -> bool:
        if isinstance(other, TransformBroadcasterStruct):
            return True
        return False

    def get(
        self,
        frame_id: str,
        child_frame_id: str
    ) -> TransformFrameBufferStructInterface:
        return self.frame_buffers.get(
            self.lookup_node_name, frame_id, child_frame_id)

    def to_value(self) -> TransformBufferStructValue:
        transforms = tuple(self.lookup_transforms)
        return TransformBufferStructValue(
            lookup_node_name=self.lookup_node_name,
            listener_node_name=self.listener_node_name,
            lookup_transforms=transforms
        )

    @property
    def frame_buffers(self) -> TransformFrameBuffersStruct:
        return self._frame_buffs

    @staticmethod
    def create_from_reader(
        reader: ArchitectureReader,
        tf_tree: TransformTreeValue,
        node: NodeValue,
    ) -> Optional[TransformBufferStruct]:
        buffer = reader.get_tf_buffer(node.node_name)

        if buffer is None:
            return None

        assert buffer.lookup_transforms is not None and len(buffer.lookup_transforms) > 0
        return TransformBufferStruct(
            tf_tree=tf_tree,
            lookup_node_name=buffer.lookup_node_name,
            listener_node_name=buffer.listener_node_name,
            lookup_transforms=list(buffer.lookup_transforms)
        )
