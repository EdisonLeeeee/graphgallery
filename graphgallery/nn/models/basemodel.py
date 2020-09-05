import os
import random
import logging

import numpy as np
import tensorflow as tf
import os.path as osp
import scipy.sparse as sp

from graphgallery import intx, floatx, backend
from graphgallery.data.io import makedirs
from graphgallery.utils.raise_error import raise_if_kwargs


class BaseModel:
    """Base model for semi-supervised learning and unsupervised learning."""

    def __init__(self, graph, device="cpu:0", seed=None, name=None, **kwargs):
        """Creat an Base model for semi-supervised learning and unsupervised learning.

        Parameters:
        ----------
            graph: Graph or MultiGraph.
            device: string. optional
                The device where the model running on.
            seed: interger scalar. optional
                Used in combination with `tf.random.set_seed` & `np.random.seed`
                & `random.seed` to create a reproducible sequence of tensors
                across multiple calls.
            name: string. optional
                Specified name for the model. (default: :str: `class.__name__`)
            kwargs: other customed keyword Parameters.

        """

        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)
            # TODO: torch set seed
            tf.random.set_seed(seed)

        if name is None:
            name = self.__class__.__name__

        raise_if_kwargs(kwargs)

        self.graph = graph  # TODO: whether to use copy?

        self.seed = seed
        self.name = name
        self.device = parse_device(device)
        self.idx_train = None
        self.idx_val = None
        self.idx_test = None
        self.backup = None

        self._model = None
        self._custom_objects = None  # used for save/load model

        # log path
        self.weight_path = osp.join(osp.expanduser(osp.normpath("/tmp/weight")),
                                    f"{name}_weights")

        # data types, default: `float32` and `int32`
        self.floatx = floatx()
        self.intx = intx()

    def save(self, path=None, as_model=False):
        if not osp.exists(self.weight_dir):
            makedirs(self.weight_dir)
            logging.log(logging.WARNING, f"Make Directory in {self.weight_dir}")

        if as_model:
            save_tf_model(model, path)
        else:
            save_tf_weights(model, path)

    def load(self, path=None, as_model=False):
        if not path:
            path = self.weight_path

        if as_model:
            self.model = load_tf_model(path, custom_objects=self.custom_objects)
        else:
            load_tf_weights(self.model, path)

    def __getattr__(self, attr):
        ##### TODO: This may cause ERROR ######
        try:
            return self.__dict__[attr]
        except KeyError:
            if hasattr(self.model, attr):
                return getattr(self.model, attr)
            raise AttributeError(f"'{self.name}' and '{self.name}.model' objects have no attribute '{attr}'")

    @property
    def model(self):
        return self._model

    @model.setter
    def model(self, m):
        # Back up
        if isinstance(m, tf.keras.Model) and m.weights:
            self.backup = tf.identity_n(m.weights)
        # assert m is None or isinstance(m, tf.keras.Model)
        self._model = m

    @property
    def custom_objects(self):
        return self._custom_objects

    @custom_objects.setter
    def custom_objects(self, value):
        assert isinstance(value, dict)
        self._custom_objects = value

    def __repr__(self):
        return f"Graphgallery.nn.{self.name} in {self.device}"


def load_tf_model(file_path, custom_objects=None):
    if not file_path.endswith('.h5'):
        file_path = file_path + '.h5'
    return tf.keras.models.load_model(file_path, custom_objects=custom_objects)


def save_tf_model(model, file_path):
    file_dir = '/'.join(file_path.split('/')[:-1])
    if not osp.exists(file_dir):
        makedirs(file_dir)
        logging.log(logging.WARNING, f"Make Directory in {file_path}.")

    if not file_path.endswith('.h5'):
        file_path = file_path + '.h5'

    model.save(file_path, save_format="h5")


def save_tf_weights(model, file_path):
    file_dir = '/'.join(file_path.split('/')[:-1])
    if not osp.exists(file_dir):
        makedirs(file_dir)
        logging.log(logging.WARNING, f"Make Directory in {file_path}.")

    if not file_path.endswith('.h5'):
        file_path_with_h5 = file_path + '.h5'
    try:
        model.save_weights(file_path_with_h5)
    except KeyError as e:
        model.save_weights(file_path_with_h5[:-3])


def load_tf_weights(model, file_path):
    if not file_path.endswith('.h5'):
        file_path_with_h5 = file_path + '.h5'
    else:
        file_path_with_h5 = file_path
    try:
        model.load_weights(file_path_with_h5)
    except KeyError as e:
        model.load_weights(file_path_with_h5[:-3])


def parse_device(device: str) -> str:
    device_lower = device.lower()
    if not any((device_lower.startswith("cpu"),
                device_lower.startswith("cuda"),
                device_lower.startswith("gpu"))):
        raise RuntimeError(f" Expected one of cpu (CPU), cuda (CUDA), gpu (GPU) device type at start of device string: {device}")

    if device_lower.startswith("cuda"):
        if backend().kind == "T":
            return "GPU" + device[4:]
    elif device_lower.startswith("gpu"):
        if backend().kind == "P":
            return "cuda" + device[4:]

    return device
