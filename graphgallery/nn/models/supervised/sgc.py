import tensorflow as tf
from tensorflow.keras import Model, Input
from tensorflow.keras.layers import Dense
from tensorflow.keras.optimizers import Adam
from tensorflow.keras import regularizers

from graphgallery.nn.layers import SGConvolution
from graphgallery.sequence import FullBatchNodeSequence
from graphgallery.nn.models import SupervisedModel


class SGC(SupervisedModel):
    """
        Implementation of Simplifying Graph Convolutional Networks (RobustGCN). 
        [Simplifying Graph Convolutional Networks](https://arxiv.org/abs/1902.07153)
        Pytorch implementation: https://github.com/Tiiiger/SGC

        Arguments:
        ----------
            adj: `scipy.sparse.csr_matrix` (or `csc_matrix`) with shape (N, N)
                The input `symmetric` adjacency matrix, where `N` is the number of nodes 
                in graph.
            x: `np.array` with shape (N, F)
                The input node feature matrix, where `F` is the dimension of node features.
            labels: `np.array` with shape (N,)
                The ground-truth labels for all nodes in graph.
            order (Positive integer, optional): 
                The power (order) of adjacency matrix. (default :obj: `2`, i.e., math:: A^{2})
            normalize_rate (Float scalar, optional): 
                The normalize rate for adjacency matrix `adj`. (default: :obj:`-0.5`, 
                i.e., math:: \hat{A} = D^{-\frac{1}{2}} A D^{-\frac{1}{2}}) 
            is_normalize_x (Boolean, optional): 
                Whether to use row-normalize for node feature matrix. 
                (default :obj: `True`)
            device (String, optional): 
                The device where the model is running on. You can specified `CPU` or `GPU` 
                for the model. (default: :obj: `CPU:0`, i.e., the model is running on 
                the 0-th device `CPU`)
            seed (Positive integer, optional): 
                Used in combination with `tf.random.set_seed & np.random.seed & random.seed` 
                to create a reproducible sequence of tensors across multiple calls. 
                (default :obj: `None`, i.e., using random seed)
            name (String, optional): 
                Name for the model. (default: name of class)

    """

    def __init__(self, adj, x, labels, order=2,
                 normalize_rate=-0.5, is_normalize_x=True, 
                 device='CPU:0', seed=None, name=None, **kwargs):

        super().__init__(adj, x, labels, device=device, seed=seed, name=name, **kwargs)

        self.order = order
        self.normalize_rate = normalize_rate
        self.is_normalize_x = is_normalize_x
        self.preprocess(adj, x)

    def preprocess(self, adj, x):
        adj, x = super().preprocess(adj, x)

        if self.normalize_rate is not None:
            adj = self.normalize_adj(adj, self.normalize_rate)

        if self.is_normalize_x:
            x = self.normalize_x(x)

        with tf.device('CPU'):
            x, adj = self.to_tensor([x, adj])
            x = SGConvolution(order=self.order)([x, adj])

        with tf.device(self.device):
            self.tf_x, self.tf_adj = x, adj

    def build(self, lr=0.2, l2_norm=5e-5):

        with tf.device(self.device):

            x = Input(batch_shape=[None, self.n_features], dtype=self.floatx, name='features')

            output = Dense(self.n_classes, activation='softmax', kernel_regularizer=regularizers.l2(l2_norm))(x)

            model = Model(inputs=x, outputs=output)
            model.compile(loss='sparse_categorical_crossentropy', optimizer=Adam(lr=lr), metrics=['accuracy'])

            self.set_model(model)
            self.built = True

    def train_sequence(self, index):
        index = self.to_int(index)
        labels = self.labels[index]
        with tf.device(self.device):
            x = tf.gather(self.tf_x, index)
            sequence = FullBatchNodeSequence(x, labels)
        return sequence

    def predict(self, index):
        super().predict(index)
        index = self.to_int(index)
        with tf.device(self.device):
            x = tf.gather(self.tf_x, index)
            logit = self.model.predict_on_batch(x)

        if tf.is_tensor(logit):
            logit = logit.numpy()
        return logit