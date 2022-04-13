from __future__ import annotations

from logging import getLogger
from typing import List, Optional, Iterable, Iterator, Tuple

from .node import NodesStruct
from .node_path import NodePathStruct
from .communication import CommunicationsStruct
from ..reader_interface import ArchitectureReader
from ...exceptions import Error

logger = getLogger(__name__)

class PathsStruct(Iterable):

    def __init__(
        self,
        reader: ArchitectureReader,
        nodes_loaded: NodesStruct,
        communications_loaded: CommunicationsStruct,
    ) -> None:
        paths: List[PathStruct] = []
        for path_value in reader.get_paths():
            try:
                path = PathStruct(path_value, nodes_loaded, communications_loaded)
                paths.append(path)
            except Error as e:
                logger.warning(f'Failed to load path. path_name={path.path_name}. {e}')

        self._data = paths

    def __iter__(self) -> Iterator[PathStruct]:
        return iter(self._data)

    @staticmethod
    def _to_node_path_struct(
        node_path_values: Tuple[NodePathValue, ...],
        nodes_loaded: NodesStruct,
    ) -> Tuple[NodePathStructValue, ...]:
        return tuple(nodes_loaded.find_node_path(_) for _ in node_path_values)

    def to_value(self) -> Tuple[PathStructValue, ...]:
        return tuple(_.to_value() for _ in self._data)

    # serviceはactioに対応していないので、おかしな結果になってしまう。
    # def _insert_publishers_to_callbacks(
    #     self,
    #     publishers: List[PublisherInfo],
    #     callbacks: List[CallbackStructInfo]
    # ) -> List[CallbackStructInfo]:
    #     for publisher in publishers:
    #         if publisher.callback_name in [None, UNDEFINED_STR]:
    #             continue

    #         callback = Util.find_one(
    #             callbacks,
    #             lambda x: x.callback_name == publisher.callback_name)
    #         callback.publishers_info.append(publisher)

    #     # automatically assign if there is only one callback.
    #     if len(callbacks) == 1:
    #         callback = callbacks[0]
    #         publisher = PublisherInfo(
    #             publisher.node_name,
    #             publisher.topic_name,
    #             callback.callback_name,
    #         )
    #         callback.publishers_info.append(publisher)

    # def _find_callback(
    #     self,
    #     node_name: str,
    #     callback_name: str
    # ) -> CallbackStructInfo:
    #     for node in self.nodes:
    #         for callback in node.callbacks:
    #             if callback.node_name == node_name and callback.callback_name == callback_name:
    #                 return callback
    #     raise ItemNotFoundError(
    #         f'Failed to find callback. node_name: {node_name}, callback_name: {callback_name}')

class PathStruct():
    def __init__(
        self,
        path_info: PathValue,
        nodes_loaded: NodesStruct,
        comms_loaded: CommunicationsStruct,
    ) -> None:
        node_paths_info = PathsStruct._to_node_path_struct(
            path_info.node_path_values, nodes_loaded)

        child: List[Union[NodePathStructValue, CommunicationStructValue]] = []
        child.append(node_paths_info[0])
        for pub_node_path, sub_node_path in zip(node_paths_info[:-1], node_paths_info[1:]):
            topic_name = sub_node_path.subscribe_topic_name
            if topic_name is None:
                msg = 'topic name is None. '
                msg += f'publish_node: {pub_node_path.node_name}, '
                msg += f'subscribe_node: {sub_node_path.node_name}, '
                raise InvalidArgumentError(msg)
            comm_info = comms_loaded.find_communication(
                topic_name,
                pub_node_path.node_name,
                sub_node_path.node_name
            )

            child.append(comm_info)
            child.append(sub_node_path)
        # return PathStructValue(path_info.path_name, tuple(child))

