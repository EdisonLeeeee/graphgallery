import tensorflow as tf

from graphgallery.gallery import GalleryModel
from graphgallery.sequence import FullBatchNodeSequence

from graphgallery.nn.models.tensorflow import GWNN as tfGWNN

from graphgallery import functional as gf


class GWNN(GalleryModel):
    """
        Implementation of Graph Wavelet Neural Networks (GWNN). 
        `Graph Wavelet Neural Network <https://arxiv.org/abs/1904.07785>`
        Tensorflow 1.x implementation: <https://github.com/Eilene/GWNN>
        Pytorch implementation: 
        <https://github.com/benedekrozemberczki/GraphWaveletNeuralNetwork>

    """

    def __init__(self,
                 graph,
                 adj_transform="wavelet_basis",
                 attr_transform=None,
                 graph_transform=None,
                 device="cpu",
                 seed=None,
                 name=None,
                 **kwargs):
        r"""Create a Graph Wavelet Neural Networks (GWNN) model.


        This can be instantiated in the following way:

            model = GWNN(graph)
                with a `graphgallery.data.Graph` instance representing
                A sparse, attributed, labeled graph.


        Parameters:
        ----------
        graph: An instance of `graphgallery.data.Graph`.
            A sparse, attributed, labeled graph.
        adj_transform: string, `transform`, or None. optional
            How to transform the adjacency matrix. See `graphgallery.functional`
            (default: :obj:`'wavelet_basis'`.) 
        attr_transform: string, `transform`, or None. optional
            How to transform the node attribute matrix. See `graphgallery.functional`
            (default :obj: `None`)    
        graph_transform: string, `transform` or None. optional
            How to transform the graph, by default, the graph transform is used
            before the other transform unless specify ``graph_first=False``
        device: string. optional
            The device where the model is running on. You can specified `CPU` or `GPU` 
            for the model. (default: :str: `cpu`, i.e., running on the 0-th `CPU`)
        seed: interger scalar. optional 
            Used in combination with `tf.random.set_seed` & `np.random.seed` 
            & `random.seed` to create a reproducible sequence of tensors across 
            multiple calls. (default :obj: `None`, i.e., using random seed)
        name: string. optional
            Specified name for the model. (default: :str: `class.__name__`)
        kwargs: keyword parameters for transform, 
            e.g., ``graph_first`` argument indicating the graph transform is
            used at the first or last, by default at the first.

        """
        super().__init__(graph, device=device, seed=seed, name=name, **kwargs)

        self.adj_transform = gf.get(adj_transform)
        self.attr_transform = gf.get(attr_transform)
        self.process()

    def process_step(self):
        graph = self.graph
        adj_matrix = self.adj_transform(graph.adj_matrix)
        node_attr = self.attr_transform(graph.node_attr)

        self.feature_inputs, self.structure_inputs = gf.astensors(
            node_attr, adj_matrix, device=self.device)

    # use decorator to make sure all list arguments have the same length
    @gf.equal()
    def build(self,
              hiddens=[16],
              activations=['relu'],
              dropout=0.5,
              weight_decay=5e-4,
              lr=0.01,
              use_bias=False):

        if self.backend == "tensorflow":
            with tf.device(self.device):
                self.model = tfGWNN(self.graph.num_node_attrs,
                                    self.graph.num_node_classes,
                                    self.graph.num_nodes,
                                    hiddens=hiddens,
                                    activations=activations,
                                    dropout=dropout,
                                    weight_decay=weight_decay,
                                    lr=lr,
                                    use_bias=use_bias)
        else:
            raise NotImplementedError

    def train_sequence(self, index):

        labels = self.graph.node_label[index]
        sequence = FullBatchNodeSequence(
            [self.feature_inputs, *self.structure_inputs, index],
            labels,
            device=self.device)
        return sequence
