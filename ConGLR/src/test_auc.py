# -*- coding: utf-8 -*-
import os, sys
import argparse
import logging
import torch
from scipy.sparse import SparseEfficiencyWarning
import numpy as np
import json
from warnings import simplefilter

sys.path.append(os.path.join(os.path.dirname(__file__), f'utils'))
sys.path.append(os.path.join(os.path.dirname(__file__), f'model'))

from utils.initialization_utils import initialize_experiment, initialize_model
from utils.process_utils import generate_subgraph_datasets
from utils.data_utils import SubgraphDataset
from utils.batch_utils import collate_dgl, move_batch_to_device_dgl

from evaluator import Evaluator



def main(params):
    simplefilter(action='ignore', category=UserWarning)
    simplefilter(action='ignore', category=SparseEfficiencyWarning)

    graph_classifier = initialize_model(params, None, load_model=True)

    logging.info(f"Device: {params.device}")

    all_auc = []
    auc_mean = 0

    all_auc_pr = []
    all_hit10 = []
    auc_pr_mean = 0
    for r in range(1, params.runs + 1):
        params.db_path = os.path.join(params.main_dir,
                                      f'../../{params.data_dir}/{params.dataset}/test_subgraphs_{params.experiment_name}_{params.constrained_neg_prob}_en_{params.enclosing_sub_graph}')
        generate_subgraph_datasets(params, splits=['test'],
                                   saved_relation2id=graph_classifier.relation2id,
                                   max_label_value=graph_classifier.max_label_value)

        relation2id = graph_classifier.relation2id
        id2revid = {}  # 增加对应的拟关系
        # for temp_str in relation2id.keys():
        #     if 'reverse/end' not in temp_str:
        #         temp_id = relation2id[temp_str]
        #         rev_str = temp_str + '/reverse/end'
        #         id2revid[temp_id] = relation2id[rev_str]

        # test = SubgraphDataset(params.db_path, id2revid, 'test_pos', 'test_neg', params.file_paths,  # 没加relation2id
        test = SubgraphDataset(params.db_path, id2revid, 'test_pos', 'test_neg', params.file_paths, graph_classifier.relation2id,
                               add_traspose_rels=params.add_traspose_rels,
                               num_neg_samples_per_link=params.num_neg_samples_per_link,
                               use_kge_embeddings=params.use_kge_embeddings, dataset=params.dataset,
                               kge_model=params.kge_model, file_name=params.test_file)

        test_evaluator = Evaluator(params, graph_classifier, test)

        result = test_evaluator.eval(save=False)
        logging.info('\nTest Set Performance:' + str(result))
        all_auc.append(result['auc'])
        all_hit10.append(result['hit10'])
        auc_mean = auc_mean + (result['auc'] - auc_mean) / r

        all_auc_pr.append(result['auc_pr'])
        auc_pr_mean = auc_pr_mean + (result['auc_pr'] - auc_pr_mean) / r

    auc_std = np.std(all_auc)
    auc_pr_std = np.std(all_auc_pr)
    avg_auc = np.mean(all_auc)
    avg_auc_pr = np.mean(all_auc_pr)
    hit10 = np.mean(all_hit10)
    hit10_std = np.std(all_hit10)

    # logging.info('\nAvg test Set Performance -- mean auc :' + str(avg_auc) + ' std auc: ' + str(auc_std))
    logging.info('\nAvg test Set Performance -- mean auc_pr :' + str(avg_auc_pr) + ' std auc_pr: ' + str(auc_pr_std))
    logging.info('\nAvg test Set Performance -- mean hit10 :' + str(hit10) + ' std hit10: ' + str(hit10_std))
    logging.info(f'auc_pr: {avg_auc_pr: .4f}   hit10: {hit10: .4f}')



def main2(params):
    simplefilter(action='ignore', category=UserWarning)
    simplefilter(action='ignore', category=SparseEfficiencyWarning)

    graph_classifier = initialize_model(params, None, load_model=True)

    logging.info(f"Device: {params.device}")

    all_auc = []
    auc_mean = 0

    all_auc_pr = []
    auc_pr_mean = 0
    for r in range(1, params.runs + 1):

        params.db_path = os.path.join(params.main_dir, f'../../{params.data_dir}/{params.dataset}/test_subgraphs_{params.experiment_name}_{params.constrained_neg_prob}_en_{params.enclosing_sub_graph}')
        generate_subgraph_datasets(params, splits=['test'],
                                   saved_relation2id=graph_classifier.relation2id,
                                   max_label_value=graph_classifier.max_label_value)

        relation2id = graph_classifier.relation2id
        id2revid = {}  # 增加对应的拟关系
        # for temp_str in relation2id.keys():
        #     if 'reverse/end' not in temp_str:
        #         temp_id = relation2id[temp_str]
        #         rev_str = temp_str + '/reverse/end'
        #         id2revid[temp_id] = relation2id[rev_str]


        test = SubgraphDataset(params.db_path, id2revid, 'test_pos', 'test_neg', params.file_paths,
                               add_traspose_rels=params.add_traspose_rels,
                               num_neg_samples_per_link=params.num_neg_samples_per_link,
                               use_kge_embeddings=params.use_kge_embeddings, dataset=params.dataset,
                               kge_model=params.kge_model, file_name=params.test_file)

        test_evaluator = Evaluator(params, graph_classifier, test)

        result = test_evaluator.eval(save=False)
        logging.info('\nTest Set Performance:' + str(result))
        all_auc.append(result['auc'])
        auc_mean = auc_mean + (result['auc'] - auc_mean) / r

        all_auc_pr.append(result['auc_pr'])
        auc_pr_mean = auc_pr_mean + (result['auc_pr'] - auc_pr_mean) / r

    auc_std = np.std(all_auc)
    auc_pr_std = np.std(all_auc_pr)

    logging.info('\nAvg test Set Performance -- mean auc :' + str(np.mean(all_auc)) + ' std auc: ' + str(np.std(all_auc)))
    logging.info('\nAvg test Set Performance -- mean auc_pr :' + str(np.mean(all_auc_pr)) + ' std auc_pr: ' + str(np.std(all_auc_pr)))


if __name__ == '__main__':

    logging.basicConfig(level=logging.INFO)

    parser = argparse.ArgumentParser(description='TransE model')

    # Experiment setup params
    parser.add_argument("--experiment_name", "-e", type=str, default="nell_v1",
                        help="A folder with this name would be created to dump saved models and log files")
    parser.add_argument("--dataset", "-d", type=str, default="nell_v1_ind",
                        help="Dataset string")
    parser.add_argument("--data_dir", "-dr", type=str, default='data',
                        help="data directory")  # 是否使用逆关系增强 data_rev data
    parser.add_argument("--train_file", "-tf", type=str, default="train",
                        help="Name of file containing training triplets")
    parser.add_argument("--test_file", "-t", type=str, default="test",
                        help="Name of file containing test triplets")
    parser.add_argument("--runs", type=int, default=5,
                        help="How many runs to perform for mean and std?")
    parser.add_argument("--gpu", type=int, default=1,
                        help="Which GPU to use?")
    parser.add_argument('--disable_cuda', action='store_true',
                        help='Disable CUDA')

    # Data processing pipeline params
    parser.add_argument("--max_links", type=int, default=100000,
                        help="Set maximum number of links (to fit into memory)")
    parser.add_argument("--hop", type=int, default=3,
                        help="Enclosing subgraph hop number")
    parser.add_argument("--max_nodes_per_hop", "-max_h", type=int, default=None,
                        help="if > 0, upper bound the # nodes per hop by subsampling")
    parser.add_argument("--use_kge_embeddings", "-kge", type=bool, default=False,
                        help='whether to use pretrained KGE embeddings')
    parser.add_argument("--kge_model", type=str, default="TransE",
                        help="Which KGE model to load entity embeddings from")
    parser.add_argument('--model_type', '-m', type=str, choices=['dgl'], default='dgl',
                        help='what format to store subgraphs in for model')
    parser.add_argument('--constrained_neg_prob', '-cn', type=float, default=0,
                        help='with what probability to sample constrained heads/tails while neg sampling')
    parser.add_argument("--num_neg_samples_per_link", '-neg', type=int, default=1,
                        help="Number of negative examples to sample per positive link")
    parser.add_argument("--batch_size", type=int, default=16,
                        help="Batch size")
    parser.add_argument("--num_workers", type=int, default=8,
                        help="Number of dataloading processes")
    parser.add_argument('--add_traspose_rels', '-tr', type=bool, default=False,
                        help='whether to append adj matrix list with symmetric relations')
    parser.add_argument('--enclosing_sub_graph', '-en', type=bool, default=True,
                        help='whether to only consider enclosing subgraph')

    params = parser.parse_args()
    initialize_experiment(params, __file__)

    params.file_paths = {
        'train': os.path.join(params.main_dir, '../../{}/{}/{}.txt'.format(params.data_dir, params.dataset, params.train_file)),
        'test': os.path.join(params.main_dir, '../../{}/{}/{}.txt'.format(params.data_dir, params.dataset, params.test_file))
    }

    if not params.disable_cuda and torch.cuda.is_available():
        params.device = torch.device('cuda:%d' % params.gpu)
    else:
        params.device = torch.device('cpu')

    params.collate_fn = collate_dgl
    params.move_batch_to_device = move_batch_to_device_dgl

    main(params)