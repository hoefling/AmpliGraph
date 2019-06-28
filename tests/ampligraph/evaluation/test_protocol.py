# Copyright 2019 The AmpliGraph Authors. All Rights Reserved.
#
# This file is Licensed under the Apache License, Version 2.0.
# A copy of the Licence is available in LICENCE, or at:
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
import numpy as np
import pytest

from ampligraph.latent_features import TransE, ComplEx, RandomBaseline
from ampligraph.evaluation import evaluate_performance, generate_corruptions_for_eval, \
    generate_corruptions_for_fit, to_idx, create_mappings, mrr_score, hits_at_n_score, select_best_model_ranking, \
    filter_unseen_entities

from ampligraph.datasets import load_wn18, load_wn18rr
import tensorflow as tf

from ampligraph.evaluation import train_test_split_no_unseen
from ampligraph.evaluation.protocol import next_hyperparam, remove_unused_params, randomly_sample_params, \
    scalars_into_lists


def test_evaluate_performance_default_protocol_without_filter():
    wn18 = load_wn18()

    model = TransE(batches_count=10, seed=0, epochs=1,
                   k=50, eta=10,  verbose=True,
                   embedding_model_params={'normalize_ent_emb':False, 'norm': 1},
                   loss='self_adversarial', loss_params={'margin': 1, 'alpha': 0.5},
                   optimizer='adam',
                   optimizer_params={'lr': 0.0005})

    model.fit(wn18['train'])

    from ampligraph.evaluation import evaluate_performance
    ranks_sep = []
    from ampligraph.evaluation import hits_at_n_score, mrr_score, mr_score
    ranks = evaluate_performance(wn18['test'][::100], model, verbose=True, corrupt_side='o',
                                 use_default_protocol=False)

    ranks_sep.extend(ranks)
    from ampligraph.evaluation import evaluate_performance

    from ampligraph.evaluation import hits_at_n_score, mrr_score, mr_score
    ranks = evaluate_performance(wn18['test'][::100], model, verbose=True, corrupt_side='s',
                                 use_default_protocol=False)
    ranks_sep.extend(ranks)
    print('----------EVAL WITHOUT FILTER-----------------')
    print('----------Subj and obj corrupted separately-----------------')
    mr_sep = mr_score(ranks_sep)
    print('MAR:', mr_sep)
    print('Mrr:', mrr_score(ranks_sep))
    print('hits10:', hits_at_n_score(ranks_sep, 10))
    print('hits3:', hits_at_n_score(ranks_sep, 3))
    print('hits1:', hits_at_n_score(ranks_sep, 1))

    from ampligraph.evaluation import evaluate_performance

    from ampligraph.evaluation import hits_at_n_score, mrr_score, mr_score
    ranks = evaluate_performance(wn18['test'][::100], model, verbose=True, corrupt_side='s+o',
                                 use_default_protocol=True)
    print('----------corrupted with default protocol-----------------')
    mr_joint = mr_score(ranks)
    mrr_joint = mrr_score(ranks)
    print('MAR:', mr_joint)
    print('Mrr:', mrr_score(ranks))
    print('hits10:', hits_at_n_score(ranks, 10))
    print('hits3:', hits_at_n_score(ranks, 3))
    print('hits1:', hits_at_n_score(ranks, 1))
    
    np.testing.assert_equal(mr_sep, mr_joint)
    assert(mrr_joint is not np.Inf)
    
    
def test_evaluate_performance_default_protocol_with_filter():
    wn18 = load_wn18()

    X_filter = np.concatenate((wn18['train'], wn18['valid'], wn18['test']))

    model = TransE(batches_count=10, seed=0, epochs=1,
                   k=50, eta=10,  verbose=True,
                   embedding_model_params={'normalize_ent_emb': False, 'norm': 1},
                   loss='self_adversarial', loss_params={'margin': 1, 'alpha': 0.5},
                   optimizer='adam',
                   optimizer_params={'lr': 0.0005})

    model.fit(wn18['train'])

    from ampligraph.evaluation import evaluate_performance
    ranks_sep = []
    from ampligraph.evaluation import hits_at_n_score, mrr_score, mr_score
    ranks = evaluate_performance(wn18['test'][::100], model, X_filter, verbose=True, corrupt_side='o',
                                 use_default_protocol=False)

    ranks_sep.extend(ranks)
    from ampligraph.evaluation import evaluate_performance

    from ampligraph.evaluation import hits_at_n_score, mrr_score, mr_score
    ranks = evaluate_performance(wn18['test'][::100], model, X_filter, verbose=True, corrupt_side='s',
                                 use_default_protocol=False)
    ranks_sep.extend(ranks)
    print('----------EVAL WITH FILTER-----------------')
    print('----------Subj and obj corrupted separately-----------------')
    mr_sep = mr_score(ranks_sep)
    print('MAR:', mr_sep)
    print('Mrr:', mrr_score(ranks_sep))
    print('hits10:', hits_at_n_score(ranks_sep, 10))
    print('hits3:', hits_at_n_score(ranks_sep, 3))
    print('hits1:', hits_at_n_score(ranks_sep, 1))

    from ampligraph.evaluation import evaluate_performance

    from ampligraph.evaluation import hits_at_n_score, mrr_score, mr_score
    ranks = evaluate_performance(wn18['test'][::100], model, X_filter, verbose=True, corrupt_side='s+o',
                                 use_default_protocol=True)
    print('----------corrupted with default protocol-----------------')
    mr_joint = mr_score(ranks)
    mrr_joint = mrr_score(ranks)
    print('MAR:', mr_joint)
    print('Mrr:', mrr_joint)
    print('hits10:', hits_at_n_score(ranks, 10))
    print('hits3:', hits_at_n_score(ranks, 3))
    print('hits1:', hits_at_n_score(ranks, 1))
    
    np.testing.assert_equal(mr_sep, mr_joint)
    assert(mrr_joint is not np.Inf)

    
def test_evaluate_performance_so_side_corruptions_with_filter():
    X = load_wn18()
    model = ComplEx(batches_count=10, seed=0, epochs=5, k=200, eta=10, loss='nll',
                    regularizer=None, optimizer='adam', optimizer_params={'lr': 0.01}, verbose=True)
    model.fit(X['train'])

    ranks = evaluate_performance(X['test'][::20], model=model, verbose=True,
                                 use_default_protocol=False, corrupt_side='s+o')
    mrr = mrr_score(ranks)
    hits_10 = hits_at_n_score(ranks, n=10)
    print("ranks: %s" % ranks)
    print("MRR: %f" % mrr)
    print("Hits@10: %f" % hits_10)
    assert(mrr is not np.Inf)


def test_evaluate_performance_so_side_corruptions_without_filter():
    X = load_wn18()
    model = ComplEx(batches_count=10, seed=0, epochs=5, k=200, eta=10, loss='nll',
                    regularizer=None, optimizer='adam', optimizer_params={'lr': 0.01}, verbose=True)
    model.fit(X['train'])

    X_filter = np.concatenate((X['train'], X['valid'], X['test']))
    ranks = evaluate_performance(X['test'][::20], model, X_filter,  verbose=True,
                                 use_default_protocol=False, corrupt_side='s+o')
    mrr = mrr_score(ranks)
    hits_10 = hits_at_n_score(ranks, n=10)
    print("ranks: %s" % ranks)
    print("MRR: %f" % mrr)
    print("Hits@10: %f" % hits_10)
    assert(mrr is not np.Inf)
    

@pytest.mark.skip(reason="Speeding up jenkins")
def test_evaluate_performance_nll_complex():
    X = load_wn18()
    model = ComplEx(batches_count=10, seed=0, epochs=10, k=150, optimizer_params={'lr': 0.1}, eta=10, loss='nll',
                    optimizer='adagrad', verbose=True)
    model.fit(np.concatenate((X['train'], X['valid'])))

    filter_triples = np.concatenate((X['train'], X['valid'], X['test']))
    ranks = evaluate_performance(X['test'][:200], model=model, filter_triples=filter_triples, verbose=True)

    mrr = mrr_score(ranks)
    hits_10 = hits_at_n_score(ranks, n=10)
    print("ranks: %s" % ranks)
    print("MRR: %f" % mrr)
    print("Hits@10: %f" % hits_10)


@pytest.mark.skip(reason="Speeding up jenkins")
def test_evaluate_performance_TransE():
    X = load_wn18()
    model = TransE(batches_count=10, seed=0, epochs=100, k=100, eta=5, optimizer_params={'lr': 0.1},
                   loss='pairwise', loss_params={'margin': 5}, optimizer='adagrad')
    model.fit(np.concatenate((X['train'], X['valid'])))

    filter_triples = np.concatenate((X['train'], X['valid'], X['test']))
    ranks = evaluate_performance(X['test'][:200], model=model, filter_triples=filter_triples, verbose=True)

    # ranks = evaluate_performance(X['test'][:200], model=model)

    mrr = mrr_score(ranks)
    hits_10 = hits_at_n_score(ranks, n=10)
    print("ranks: %s" % ranks)
    print("MRR: %f" % mrr)
    print("Hits@10: %f" % hits_10)

    # TODO: add test condition (MRR raw for WN18 and TransE should be ~ 0.335 - check papers)


def test_generate_corruptions_for_eval():
    X = np.array([['a', 'x', 'b'],
                  ['c', 'x', 'd'],
                  ['e', 'x', 'f'],
                  ['b', 'y', 'h'],
                  ['a', 'y', 'l']])

    rel_to_idx, ent_to_idx = create_mappings(X)
    X = to_idx(X, ent_to_idx=ent_to_idx, rel_to_idx=rel_to_idx)

    with tf.Session() as sess:
        all_ent = tf.constant(list(ent_to_idx.values()), dtype=tf.int64)
        x = tf.constant(np.array([X[0]]), dtype=tf.int64)
        x_n_actual, _ = sess.run(generate_corruptions_for_eval(x, all_ent))
        x_n_expected = np.array([[0, 0, 0],
                                 [0, 0, 1],
                                 [0, 0, 2],
                                 [0, 0, 3],
                                 [0, 0, 4],
                                 [0, 0, 5],
                                 [0, 0, 6],
                                 [0, 0, 7],
                                 [0, 0, 1],
                                 [1, 0, 1],
                                 [2, 0, 1],
                                 [3, 0, 1],
                                 [4, 0, 1],
                                 [5, 0, 1],
                                 [6, 0, 1],
                                 [7, 0, 1]])
    np.testing.assert_array_equal(x_n_actual, x_n_expected)


@pytest.mark.skip(reason="Needs to change to account for prime-product evaluation strategy")
def test_generate_corruptions_for_eval_filtered():
    x = np.array([0, 0, 1])
    idx_entities = np.array([0, 1, 2, 3])
    filter_triples = np.array(([1, 0, 1], [2, 0, 1]))

    x_n_actual = generate_corruptions_for_eval(x, idx_entities=idx_entities, filter=filter_triples)
    x_n_expected = np.array([[3, 0, 1],
                             [0, 0, 0],
                             [0, 0, 2],
                             [0, 0, 3]])
    np.testing.assert_array_equal(np.sort(x_n_actual, axis=0), np.sort(x_n_expected, axis=0))


@pytest.mark.skip(reason="Needs to change to account for prime-product evaluation strategy")
def test_generate_corruptions_for_eval_filtered_object():
    x = np.array([0, 0, 1])
    idx_entities = np.array([0, 1, 2, 3])
    filter_triples = np.array(([1, 0, 1], [2, 0, 1]))

    x_n_actual = generate_corruptions_for_eval(x, idx_entities=idx_entities, filter=filter_triples, side='o')
    x_n_expected = np.array([[0, 0, 0],
                             [0, 0, 2],
                             [0, 0, 3]])
    np.testing.assert_array_equal(np.sort(x_n_actual, axis=0), np.sort(x_n_expected, axis=0))


def test_to_idx():
    X = np.array([['a', 'x', 'b'], ['c', 'y', 'd']])
    X_idx_expected = [[0, 0, 1], [2, 1, 3]]
    rel_to_idx, ent_to_idx = create_mappings(X)
    X_idx = to_idx(X, ent_to_idx=ent_to_idx, rel_to_idx=rel_to_idx)

    np.testing.assert_array_equal(X_idx, X_idx_expected)


def test_filter_unseen_entities_with_strict_mode():
    from collections import namedtuple
    base_model = namedtuple('test_model', 'ent_to_idx')

    X = np.array([['a', 'x', 'b'],
                  ['c', 'y', 'd'],
                  ['e', 'y', 'd']])

    model = base_model({'a': 1, 'b': 2, 'c': 3, 'd': 4})

    with pytest.raises(RuntimeError):
        _ = filter_unseen_entities(X, model, strict=True)


def test_filter_unseen_entities_without_strict_mode():
    from collections import namedtuple
    base_model = namedtuple('test_model', 'ent_to_idx')

    X = np.array([['a', 'x', 'b'],
                  ['c', 'y', 'd'],
                  ['e', 'y', 'd']])

    model = base_model({'a': 1, 'b': 2, 'c': 3, 'd': 4})

    X_filtered = filter_unseen_entities(X, model, strict=False)

    X_expected = np.array([['a', 'x', 'b'],
                           ['c', 'y', 'd']])

    np.testing.assert_array_equal(X_filtered, X_expected)


# @pytest.mark.skip(reason="excluded to try out jenkins.")   # TODO: re-enable this
def test_generate_corruptions_for_fit_corrupt_side_so():
    X = np.array([['a', 'x', 'b'],
                  ['c', 'x', 'd'],
                  ['e', 'x', 'f'],
                  ['b', 'y', 'h'],
                  ['a', 'y', 'l']])
    rel_to_idx, ent_to_idx = create_mappings(X)
    X = to_idx(X, ent_to_idx=ent_to_idx, rel_to_idx=rel_to_idx)
    eta = 1
    with tf.Session() as sess:
        all_ent = tf.squeeze(tf.constant(list(ent_to_idx.values()), dtype=tf.int32))
        dataset = tf.constant(X, dtype=tf.int32)
        X_corr = sess.run(generate_corruptions_for_fit(dataset, eta=eta, corrupt_side='s+o', entities_size=len(X), rnd=0))
        print(X_corr)
    # these values occur when seed=0

    X_corr_exp = [[0, 0, 1],
                  [2, 0, 3],
                  [3, 0, 5],
                  [1, 1, 0],
                  [0, 1, 3]]

    np.testing.assert_array_equal(X_corr, X_corr_exp)


def test_generate_corruptions_for_fit_curropt_side_s():
    X = np.array([['a', 'x', 'b'],
                  ['c', 'x', 'd'],
                  ['e', 'x', 'f'],
                  ['b', 'y', 'h'],
                  ['a', 'y', 'l']])
    rel_to_idx, ent_to_idx = create_mappings(X)
    X = to_idx(X, ent_to_idx=ent_to_idx, rel_to_idx=rel_to_idx)
    eta = 1
    with tf.Session() as sess:
        all_ent = tf.squeeze(tf.constant(list(ent_to_idx.values()), dtype=tf.int32))
        dataset = tf.constant(X, dtype=tf.int32)
        X_corr = sess.run(generate_corruptions_for_fit(dataset, eta=eta, corrupt_side='s', entities_size=len(X), rnd=0))
        print(X_corr)

    # these values occur when seed=0

    X_corr_exp = [[1, 0, 1],
                  [3, 0, 3],
                  [3, 0, 5],
                  [0, 1, 6],
                  [3, 1, 7]]

    np.testing.assert_array_equal(X_corr, X_corr_exp)


def test_generate_corruptions_for_fit_curropt_side_o():
    X = np.array([['a', 'x', 'b'],
                  ['c', 'x', 'd'],
                  ['e', 'x', 'f'],
                  ['b', 'y', 'h'],
                  ['a', 'y', 'l']])
    rel_to_idx, ent_to_idx = create_mappings(X)
    X = to_idx(X, ent_to_idx=ent_to_idx, rel_to_idx=rel_to_idx)
    eta = 1
    with tf.Session() as sess:
        all_ent = tf.squeeze(tf.constant(list(ent_to_idx.values()), dtype=tf.int32))
        dataset = tf.constant(X, dtype=tf.int32)
        X_corr = sess.run(generate_corruptions_for_fit(dataset, eta=eta, corrupt_side='o', entities_size=len(X), rnd=0))
        print(X_corr)
    # these values occur when seed=0

    X_corr_exp = [[0, 0, 1],
                  [2, 0, 3],
                  [4, 0, 3],
                  [1, 1, 0],
                  [0, 1, 3]]
    np.testing.assert_array_equal(X_corr, X_corr_exp)


def test_train_test_split():

    # Graph
    X = np.array([['a', 'y', 'b'],
                  ['a', 'y', 'c'],
                  ['c', 'y', 'a'],
                  ['d', 'y', 'e'],
                  ['e', 'y', 'f'],
                  ['f', 'y', 'c'],
                  ['f', 'y', 'c']])

    expected_X_train = np.array([['a', 'y', 'b'],
                                ['c', 'y', 'a'],
                                ['d', 'y', 'e'],
                                ['e', 'y', 'f'],
                                ['f', 'y', 'c']])
    
    expected_X_test = np.array([['a', 'y', 'c'],
                                ['f', 'y', 'c']])

    X_train, X_test = train_test_split_no_unseen(X, test_size=2, seed=0)

    np.testing.assert_array_equal(X_train, expected_X_train)
    np.testing.assert_array_equal(X_test, expected_X_test)


def test_next_hyperparam():
    param_grid = {
        "batches_count": [50],
        "epochs": [4000],
        "k": [100, 200],
        "eta": [5, 10, 15],
        "loss": ["pairwise", "nll"],
        "loss_params": {
            "margin": [2]
        },
        "embedding_model_params": {
        },
        "regularizer": ["LP", None],
        "regularizer_params": {
            "p": [1, 3],
            "lambda": [1e-4, 1e-5]
        },
        "optimizer": ["adagrad", "adam"],
        "optimizer_params": {
            "lr": [0.01, 0.001, 0.0001]
        },
        "verbose": False
    }

    combinations = [i for i in next_hyperparam("ComplEx", param_grid)]
    assert len(combinations) == 360
    assert all(type(d) is dict for d in combinations)
    assert all(all(type(k) is str for k in d.keys()) for d in combinations)


def test_remove_unused_params():
    params1 = {
        "batches_count": 50,
        "epochs": 4000,
        "k": 200,
        "eta": 15,
        "loss": "nll",
        "loss_params": {
            "margin": 2
        },
        "embedding_model_params": {
        },
        "regularizer": "LP",
        "regularizer_params": {
            "p": 1,
            "lambda": 1e-5
        },
        "optimizer": "adam",
        "optimizer_params": {
            "lr": 0.001
        },
        "verbose": False
    }
    nested_keys = {"loss_params", "embedding_model_params", "regularizer_params", "optimizer_params"}
    remove_unused_params(params1, nested_keys, "ComplEx")

    assert nested_keys == {"loss_params", "embedding_model_params", "regularizer_params", "optimizer_params"}
    assert params1["loss_params"] == {}
    assert params1["embedding_model_params"] == {}
    assert params1["regularizer_params"] == {
        "p": 1,
        "lambda": 1e-5
    }
    assert params1["optimizer_params"] == {
        "lr": 0.001
    }

    params2 = {
        "batches_count": 50,
        "epochs": 4000,
        "k": 200,
        "eta": 15,
        "loss": "self_adversarial",
        "loss_params": {
            "margin": 2
        },
        "regularizer": None,
        "regularizer_params": {
            "p": 1,
            "lambda": 1e-5
        },
        "optimizer": "adam",
        "optimizer_params": {
            "lr": 0.001
        },
        "verbose": False
    }
    nested_keys = {"loss_params", "regularizer_params", "optimizer_params"}
    remove_unused_params(params2, nested_keys, "unknown_model")

    assert nested_keys == {"loss_params", "regularizer_params", "optimizer_params"}
    assert params2["loss_params"] == {
        "margin": 2
    }
    assert params2["regularizer_params"] == {}
    assert params2["optimizer_params"] == {
        "lr": 0.001
    }


def test_randomly_sample_params():
    np.random.seed(0)

    param_grid = {
        "batches_count": [50],
        "epochs": [4000],
        "k": [100, 200],
        "eta": lambda: np.random.choice([5, 10, 15]),
        "loss": ["pairwise", "nll"],
        "loss_params": {
            "margin": [2]
        },
        "embedding_model_params": {
        },
        "regularizer": ["LP", None],
        "regularizer_params": {
            "p": [1, 3],
            "lambda": [1e-4, 1e-5]
        },
        "optimizer": ["adagrad", "adam"],
        "optimizer_params": {
            "lr": lambda: np.random.uniform(0.001, 0.1)
        },
        "verbose": False
    }
    
    randomly_sample_params(param_grid, max_combinations=10)

    assert len(param_grid["eta"]) == 10
    assert len(set(param_grid["eta"])) == 3
    assert len(param_grid["optimizer_params"]["lr"]) == 10
    assert len(set(param_grid["optimizer_params"]["lr"])) == 10


def test_scalars_into_lists():
    eta_fn = lambda: np.random.choice([5, 10, 15])

    param_grid = {
        "batches_count": 50,
        "epochs": [4000],
        "k": [100, 200],
        "eta": eta_fn,
        "loss": "nll",
        "loss_params": {
            "margin": 2
        },
        "embedding_model_params": {
        },
        "regularizer": ["LP", None],
        "regularizer_params": {
            "p": [1, 3],
            "lambda": [1e-4, 1e-5]
        },
        "optimizer": ["adagrad", "adam"],
        "optimizer_params": {
            "lr": "wrong"
        },
        "verbose": False
    }

    scalars_into_lists(param_grid)

    expected = {
        "batches_count": [50],
        "epochs": [4000],
        "k": [100, 200],
        "eta": eta_fn,
        "loss": ["nll"],
        "loss_params": {
            "margin": [2]
        },
        "embedding_model_params": {
        },
        "regularizer": ["LP", None],
        "regularizer_params": {
            "p": [1, 3],
            "lambda": [1e-4, 1e-5]
        },
        "optimizer": ["adagrad", "adam"],
        "optimizer_params": {
            "lr": ["wrong"]
        },
        "verbose": [False]
    }

    assert param_grid == expected


def test_select_best_model_ranking_grid():
    X = load_wn18rr()
    model_class = TransE
    param_grid = {
        "batches_count": [50],
        "seed": 0,
        "epochs": [1],
        "k": [2, 50],
        "eta": [1],
        "loss": ["nll"],
        "loss_params": {
        },
        "embedding_model_params": {
        },
        "regularizer": [None],

        "regularizer_params": {
        },
        "optimizer": ["adagrad"],
        "optimizer_params": {
            "lr": [1000.0, 0.0001]
        }
    }

    best_model, best_params, best_mrr_train, ranks_test, mrr_test = select_best_model_ranking(
        model_class,
        X['train'],
        X['valid'][::5],
        X['test'][::10],
        param_grid
    )
    assert best_params['k'] == 50
    assert best_params['optimizer_params']['lr'] == 0.0001


def test_select_best_model_ranking_random():
    X = load_wn18rr()
    model_class = TransE
    param_grid = {
        "batches_count": [50],
        "seed": 0,
        "epochs": [1],
        "k": lambda: np.random.choice(range(1, 50)),
        "eta": [1],
        "loss": ["nll"],
        "loss_params": {
        },
        "embedding_model_params": {
        },
        "regularizer": [None],

        "regularizer_params": {
        },
        "optimizer": ["adagrad"],
        "optimizer_params": {
            "lr": lambda: np.log(np.random.uniform(1.00001, 1.1))
        }
    }

    best_model, best_params, best_mrr_train, ranks_test, mrr_test = select_best_model_ranking(
        model_class,
        X['train'],
        X['valid'][::5],
        X['test'][::10],
        param_grid,
        max_combinations=5
    )
    assert 0 < best_params['k'] < 50
    assert np.log(1.00001) <= best_params['optimizer_params']['lr'] <= np.log(100)
