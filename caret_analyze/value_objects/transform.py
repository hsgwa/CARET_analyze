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

from copy import deepcopy
from itertools import groupby

from typing import Optional, Sequence, Set, Tuple

from .publisher import PublisherStructValue, PublisherValue
from .value_object import ValueObject
from ..common.util import Util
from ..exceptions import ItemNotFoundError


class TransformValue(ValueObject):
    def __init__(
        self,
        frame_id: str,
        child_frame_id: str
    ) -> None:
        self._frame_id = frame_id
        self._child_frame_id = child_frame_id

    @property
    def frame_id(self) -> str:
        return self._frame_id

    @property
    def child_frame_id(self) -> str:
        return self._child_frame_id


class TransformRecords():

    def to_dataframe(self):
        raise NotImplementedError('')


class TransformBroadcasterValue(ValueObject):
    def __init__(
        self,
        pub: PublisherValue,
        transforms: Tuple[TransformValue, ...],
        callback_ids: Optional[Tuple[str, ...]],
    ) -> None:
        self._pub = pub
        self._transforms = transforms
        self._callback_ids = callback_ids

    @property
    def transforms(self) -> Sequence[TransformValue]:
        return self._transforms

    @property
    def publisher(self) -> PublisherValue:
        return self._pub

    @property
    def node_name(self) -> str:
        return self._pub.node_name

    @property
    def callback_ids(self) -> Optional[Tuple[str, ...]]:
        return self._callback_ids


class TransformBroadcasterStructValue(ValueObject):
    """Structured transform broadcaster value."""

    def __init__(
        self,
        publisher: PublisherStructValue,
        transforms: Sequence[TransformValue]
    ):
        self._pub = publisher
        self._transforms = transforms
        frame_broadcaster = []
        for transform in self._transforms:
            frame_broadcaster.append(
                TransformFrameBroadcasterStructValue(
                    publisher,
                    transform
                )
            )
        self._frame_broadcasters = tuple(frame_broadcaster)

    @property
    def transforms(self) -> Sequence[TransformValue]:
        return self._transforms

    @property
    def topic_name(self) -> str:
        return self._pub.topic_name

    def get(self, transform: TransformValue):
        for frame_broadcaster in self._frame_broadcasters:
            if frame_broadcaster.transform == transform:
                return frame_broadcaster
        raise ItemNotFoundError('')

    @property
    def callback_ids(self) -> Optional[Tuple[str, ...]]:
        return self._pub.callback_ids

    @property
    def node_name(self) -> str:
        return self._pub.node_name

    @property
    def publisher(self) -> PublisherStructValue:
        return self._pub

    @property
    def frame_broadcasters(self) -> Tuple[TransformFrameBroadcasterStructValue, ...]:
        return self._frame_broadcasters


class TransformFrameBroadcasterStructValue(ValueObject):
    """Structured transform broadcaster value."""

    def __init__(
        self,
        publisher: PublisherStructValue,
        transform: TransformValue,
    ):
        self._transform = transform
        self._pub = publisher

    @property
    def publisher(self) -> PublisherStructValue:
        return self._pub

    @property
    def transform(self) -> TransformValue:
        return self._transform

    @property
    def frame_id(self) -> str:
        return self._transform.frame_id

    @property
    def child_frame_id(self) -> str:
        return self._transform.child_frame_id

    @property
    def node_name(self) -> str:
        return self._pub.node_name

    @property
    def topic_name(self) -> str:
        return self._pub.topic_name


class TransformBufferValue(ValueObject):
    """transform buffer info."""

    def __init__(
        self,
        lookup_node_name: str,
        lookup_node_id: str,
        listener_node_name: Optional[str],
        listener_node_id: Optional[str],
        lookup_transforms: Optional[Tuple[TransformValue, ...]]
    ) -> None:
        self._listener_node_name = listener_node_name
        self._listener_node_id = listener_node_id
        self._lookup_node_name = lookup_node_name
        self._lookup_node_id = lookup_node_id
        self._transforms = lookup_transforms

    @property
    def lookup_node_id(self) -> str:
        return self._lookup_node_id

    @property
    def lookup_node_name(self) -> str:
        return self._lookup_node_name

    @property
    def listener_node_id(self) -> Optional[str]:
        return self._listener_node_id

    @property
    def listener_node_name(self) -> Optional[str]:
        return self._listener_node_name

    @property
    def lookup_transforms(self) -> Optional[Tuple[TransformValue, ...]]:
        return self._transforms


class TransformBufferStructValue(ValueObject):
    def __init__(
        self,
        lookup_node_name: str,
        listener_node_name: Optional[str],
        lookup_transforms: Tuple[TransformValue, ...],
    ) -> None:
        self._lookup_node_name = lookup_node_name
        self._listener_node_name = listener_node_name
        self._lookup_transforms = lookup_transforms
        self._frame_buffers: Optional[Tuple[TransformFrameBufferStructValue, ...]] = None
        if lookup_transforms is not None:
            frame_buffers = []
            for transform in lookup_transforms or []:
                frame_buffers.append(TransformFrameBufferStructValue(
                    lookup_node_name,
                    listener_node_name,
                    transform
                ))
            self._frame_buffers = tuple(frame_buffers)

    @property
    def listener_node_name(self) -> Optional[str]:
        return self._listener_node_name

    @property
    def lookup_node_name(self) -> str:
        return self._lookup_node_name

    @property
    def lookup_transforms(self) -> Tuple[TransformValue, ...]:
        return self._lookup_transforms

    @property
    def frame_buffers(self) -> Optional[Tuple[TransformFrameBufferStructValue, ...]]:
        return self._frame_buffers


class TransformFrameBufferStructValue(ValueObject):
    def __init__(
        self,
        lookup_node_name: str,
        listener_node_name: Optional[str],
        transform: TransformValue
    ) -> None:
        self._lookup_node_name = lookup_node_name
        self._listener_node_name = listener_node_name
        self._transform = transform

    @property
    def lookup_node_name(self) -> str:
        return self._lookup_node_name

    @property
    def transform(self) -> TransformValue:
        return self._transform

    @property
    def frame_id(self) -> str:
        return self._transform.frame_id

    @property
    def child_frame_id(self) -> str:
        return self._transform.child_frame_id

    @property
    def listener_node_name(self) -> Optional[str]:
        return self._listener_node_name

    @property
    def topic_name(self) -> str:
        return '/tf'


class TransformCommunicationStructValue():
    def __init__(
        self,
        broadcaster: TransformFrameBroadcasterStructValue,
        buffer: TransformFrameBufferStructValue,
    ) -> None:
        self._transform = broadcaster.transform
        self._broadcaster = broadcaster
        self._buffer = buffer

    @property
    def node_name(self) -> str:
        return self._broadcaster.publisher.node_name

    @property
    def broadcaster(self) -> TransformFrameBroadcasterStructValue:
        return self._broadcaster

    @property
    def buffer(self) -> TransformFrameBufferStructValue:
        return self._buffer

    @property
    def topic_name(self) -> str:
        return self._broadcaster.topic_name

    @property
    def transform(self) -> TransformValue:
        return self._transform

    @property
    def frame_id(self) -> str:
        return self._transform.frame_id

    @property
    def child_frame_id(self) -> str:
        return self._transform.child_frame_id


class TransformTreeValue():
    def __init__(
        self,
        frame: TransformValue,
        child_trees: Sequence[TransformTreeValue]
    ) -> None:
        self.root_tf = frame
        self._childs = child_trees

    @staticmethod
    def create_from_transforms(
        transforms: Sequence[TransformValue]
    ) -> TransformTreeValue:
        edge_trees = None
        tfs = set(deepcopy(transforms))

        while(True):
            edge_tfs = set(TransformTreeValue._get_edge_tfs(list(tfs)))
            tfs -= edge_tfs
            if edge_trees is not None and len(tfs) == 0:
                assert len(edge_trees) == 1
                return edge_trees[0]
            if edge_trees is None:
                edge_trees = [TransformTreeValue(
                    edge_tf, []) for edge_tf in edge_tfs]

            parent_trees = []
            for key, group in groupby(edge_trees, lambda x: x.transform.child_frame_id):
                child_trees = list(group)
                parent_tf = Util.find_one(
                    lambda x: x.frame_id == key, transforms)
                parent_tree = TransformTreeValue(parent_tf, child_trees)
                parent_trees.append(parent_tree)
            edge_trees = parent_trees

    def is_in(
        self,
        lookup_transform: TransformValue,
        target_transform: TransformValue
    ) -> bool:
        lookup_frame_ids = self._to_root(lookup_transform.frame_id)
        lookup_child_frme_ids = self._to_root(lookup_transform.child_frame_id)
        frames = lookup_frame_ids ^ lookup_child_frme_ids
        ret = {target_transform} <= frames
        return ret

    def _to_root(self, target_tf: str) -> Set[TransformValue]:
        s: Set[TransformValue] = set()

        def find_coord_local(tree: TransformTreeValue) -> bool:
            if tree.root_tf.frame_id == target_tf:
                s.add(tree.root_tf)
                return True
            for child in tree.childs:
                if find_coord_local(child):
                    s.add(tree.root_tf)
                    return True
            return False

        find_coord_local(self)

        return s

    @property
    def childs(self) -> Sequence[TransformTreeValue]:
        return self._childs

    @property
    def transform(self) -> TransformValue:
        return self.root_tf

    @staticmethod
    def _get_root_tf(
        transforms: Sequence[TransformValue]
    ) -> TransformValue:
        tf_root = transforms[0]

        def is_root(tf_target: TransformValue):
            return not any([tf.frame_id == tf_target.child_frame_id for tf in transforms])

        while not is_root(tf_root):
            tf_root = Util.find_one(
                lambda tf: tf.frame_id == tf_root.child_frame_id, transforms)

        return tf_root

    @staticmethod
    def _get_edge_tfs(
        transforms: Sequence[TransformValue]
    ) -> Sequence[TransformValue]:

        def is_edge(tf_target: TransformValue):
            return not any([tf_target.frame_id == tf.child_frame_id for tf in transforms])

        return Util.filter_items(is_edge, transforms)
