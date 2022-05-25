import os
import sys
import json
import random

import torch

stderr = sys.stderr
sys.stderr = open(os.devnull, 'w')
import dgl
from dgl.data import DGLDataset
sys.stderr.close()
sys.stderr = stderr

import Config


class CDataSet(DGLDataset):
    """
    CDataSet loads from the Coda Dataset and process it before feeding into the trainer
    """
    def __init__(self, data_dir=Config.DATA_DIR_DEFAULT,
                 train_valid_test_ratio=Config.TRAIN_VALID_TEST_SPLIT_RATIO_DEFAULT):
        super().__init__(name='cora')
        if (train_valid_test_ratio[0] < 0 or train_valid_test_ratio[1] < 0 or train_valid_test_ratio[2] < 0) or \
                (sum(train_valid_test_ratio) != 1.0):
            sys.stderr.write('> [CDataSet:init] Train-Validation-Test ratios (%.1f, %.1f, %.1f) are not valid. Use (%.1f, %.1f, %.1f) by default.\n' %
                             (train_valid_test_ratio[0], train_valid_test_ratio[1], train_valid_test_ratio[2], Config.TRAIN_VALID_TEST_SPLIT_RATIO_DEFAULT[0], Config.TRAIN_VALID_TEST_SPLIT_RATIO_DEFAULT[1], Config.TRAIN_VALID_TEST_SPLIT_RATIO_DEFAULT[2]))

        self.data_dir = data_dir
        self.meta = json.load(open(os.path.join(self.data_dir, 'meta.json')))
        (self.graph,), _ = dgl.load_graphs(os.path.join(self.data_dir, 'cora.dgl'))

        self.train_valid_test_split_ratio = train_valid_test_ratio
        self.num_train = int(self.meta['num_nodes'] * train_valid_test_ratio[0])
        self.num_valid = int(self.meta['num_nodes'] * train_valid_test_ratio[1])
        self.num_test = self.meta['num_nodes'] - self.num_train - self.num_valid

        self.train_valid_test_split()

    def train_valid_test_split(self):
        train_mask = [False for _ in range(self.meta['num_nodes'])]
        valid_mask = [False for _ in range(self.meta['num_nodes'])]
        test_mask = [False for _ in range(self.meta['num_nodes'])]

        random.seed(Config.RAND_SEED)
        temp_list = [i for i in range(self.meta['num_nodes'])]
        random.shuffle(temp_list)

        for i in range(self.num_train):
            train_mask[temp_list[i]] = True
        for i in range(self.num_valid):
            valid_mask[temp_list[self.num_train + i]] = True
        for i in range(self.num_test):
            test_mask[temp_list[self.num_train + self.num_valid + i]] = True

        self.graph.ndata['train_mask'] = torch.Tensor(train_mask).bool()
        self.graph.ndata['valid_mask'] = torch.Tensor(valid_mask).bool()
        self.graph.ndata['test_mask'] = torch.Tensor(test_mask).bool()

    def process(self):
        """
        Load and process raw data from disk. We have preprocessing stage, so no need to do anything here.
        """
        pass

    def __len__(self):
        """ There is only one graph for the Cora Dataset """
        return 1

    def __getitem__(self, idx):
        """
        Provides the idx-th training sample
        :param idx: index of the training sample
        :return: the training sample which is a single citation graph
        """
        return self.graph

    def __str__(self):
        info_msg = 'num_nodes: %d\nnum_edges: %d\nnum_feats: %d\nnum_classes: %d\n' % \
                   (self.meta['num_nodes'], self.meta['num_edges'], self.meta['num_feats'], self.meta['num_classes'])
        info_msg += 'num_training_samples: %d\nnum_validation_samples: %d\nnum_test_samples: %d\n' % \
                    (self.num_train, self.num_valid, self.num_test)
        return info_msg


if __name__ == '__main__':
    ds = CDataSet(data_dir=Config.DATA_DIR_DEFAULT)
    print(ds)
